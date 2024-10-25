import logging
import sys
from functools import partial
from typing import Literal

import chompjs
from aiometer import run_all
from httpx import Response
from selectolax.parser import HTMLParser, Node

from src.models import PlayerModel
from src.web import Client


class Player:
    def __init__(self, tree: HTMLParser) -> None:
        self.profile = self._get_profile(tree, "script[type='application/ld+json']")
        self.tables = self._get_tables(tree)

    def _html_node_to_iterable(
        self,
        tree: HTMLParser,
        query: str,
        attr: str | None = None,
    ) -> dict | None:
        if not (node := tree.css_first(query)):
            return None

        raw_text: str | None = node.attributes.get(attr) if attr else node.text()

        if not raw_text:
            return None

        try:
            data: dict = chompjs.parse_js_object(raw_text)
        except ValueError:
            return None
        else:
            return data

    def _sanitise(self, data: dict):
        player = PlayerModel(
            name=data.get("name", ""),
            family_name=data.get("familyName", ""),
            given_name=data.get("givenName", ""),
            url=data.get("url", "-"),
            birth_date=data.get("birthDate", ""),
            birth_place=data.get("birthPlace", "").get("address", ""),
            height=data.get("height", 0.0).get("value", 0.0),
            weight=data.get("weight", 0.0).get("value", 0.0),
            role=data.get("jobTitle", ""),
        )
        return player.model_dump(by_alias=True)

    def _get_profile(self, tree: HTMLParser, query: str) -> dict | None:
        data = self._html_node_to_iterable(tree, query)
        return self._sanitise(data) if data else None

    def _get_tables(self, tree: HTMLParser) -> dict:
        if not (tables := tree.css("table")):
            return {}

        if len(tables) == 1:
            t1 = Table(tables[-1], "careerOverall")
            return {t1.table_name: t1.output()}

        elif len(tables) == 2:
            t1 = Table(tables[-1], "careerOverall")
            t2 = Table(tables[-2], "careerSeason")
            return {t1.table_name: t1.output(), t2.table_name: t2.output()}

        else:
            t1 = Table(tables[-1], "careerOverall")
            t2 = Table(tables[-2], "careerSeason")
            t3 = Table(tables[-3], "currentSeason")
            return {
                t1.table_name: t1.output(),
                t2.table_name: t2.output(),
                t3.table_name: t3.output(),
            }

    def output(self):
        return {"profile": self.profile, "stats": self.tables}


class Table:
    def __init__(
        self,
        node: Node,
        name: Literal["currentSeason", "careerSeason", "careerOverall"],
    ) -> None:
        self.table_name = name
        self._column_titles = self._get_titles(node)
        self._column_values = self._get_values(node)

    def _nodes(self, node: Node, query: str) -> list[Node] | list:
        return node.css(query)

    def _text_filter(self, values: list[str]) -> list[str]:
        output = []
        for v in values:
            if v in ["LLost", "WWon", "DDrawn"]:
                new_val = v[1:]
                output.append(new_val)

            else:
                output.append(v)

        return output

    def _get_titles(self, node: Node) -> list | None:
        # Find table headers
        if not (headers := self._nodes(node, "thead > tr")):
            return None

        # Second header row - contains all column titles
        row = headers[-1]

        # Find titles
        if not (titles := self._nodes(row, "th.table__cell.table__th")):
            return None

        # Unpack title strings
        values = [v.text(strip=True).replace("\xa0", " ") for v in titles if v.text()]

        if self.table_name in ["careerSeason", "careerOverall"]:
            # Insert Extra Title
            values.insert(0, "Team")

        else:
            # Insert Extra Title
            values.insert(2, "Outcome")

        return values

    def _get_values(self, node: Node) -> list[list] | None:
        # Find all rows
        if not (rows := self._nodes(node, "tbody > tr")):
            return None

        output = []
        if self.table_name in ["careerSeason", "careerOverall"]:
            for row in rows:
                cells = self._nodes(row, "td.table__cell.table-tbody__td")
                values = [c.text(strip=True) for c in cells if c.text()]

                # Omit empty string
                values = values[1:]

                output.append(values)

        elif self.table_name == "currentSeason":
            for row in rows:
                cells = self._nodes(row, "td")
                values = [c.text(strip=True) for c in cells if c.text(strip=True) != ""]
                clean_values = self._text_filter(values)
                output.append(clean_values)

        return output

    def output(self) -> list[list] | list:
        if not self._column_titles or not self._column_values:
            return []

        try:
            data = [self._column_titles, *self._column_values]
        except Exception:
            return []
        else:
            return data


def get_ids(teams: list[dict]) -> list[int]:
    return list(map(lambda x: x["team_id"], teams))


def create_team_urls(
    base_url: str,
    comp_id: int,
    team_ids: list[int],
) -> list[str]:
    return [base_url.format(comp_id=comp_id, id=id) for id in team_ids]


# ! NOTE: there's a version of this in team_stats.py
async def fetch(
    urls: list[str],
    headers: dict[str, str],
    *,
    max_at_once: int | None = None,
    max_per_second: float | None = None,
) -> list:
    # open session
    client = Client(headers)

    # send requests
    results = await run_all(
        [partial(client.get, url, index) for index, url in enumerate(urls, 1)],
        max_at_once=max_at_once,
        max_per_second=max_per_second,
    )

    # close session
    await client.close()

    # remove None results
    return list(filter(lambda x: isinstance(x, Response), results))


def unpack_team_lists(responses: list[Response]) -> list[dict]:
    # pre-validated responses
    data = [r.json() for r in responses]

    teams = []
    for item in data:
        try:
            team: list[dict] = item["profileGroups"][0]["profiles"]
        except (IndexError, KeyError) as exc:
            logging.error(f"Unable to extract JSON from response: {exc}")
            continue
        else:
            teams.extend(team)
    return teams


def create_player_urls(
    responses: list[Response],
    base_url: str = "https://www.nrl.com",
) -> list[str]:
    teams: list[dict] = unpack_team_lists(responses)
    hrefs: list[str] = list(map(lambda x: x["url"], teams))
    return list(map(lambda href: f"{base_url}{href}", hrefs))


def parse_html(response: Response) -> HTMLParser:
    return HTMLParser(str(response.text))


async def get(env: dict):
    # unpack environment vars
    headers: dict[str, str] = env["web"]["headers"]
    comp_id: int = env["players"]["comp_id"]
    team_ids: list[int] = get_ids(teams=env["teams"][str(comp_id)])
    base_url: str = env["players"]["base_url"]

    # get team webpages
    team_urls: list[str] = create_team_urls(base_url, comp_id, team_ids)
    team_responses = await fetch(team_urls, headers, max_at_once=5)
    if not team_responses:
        sys.exit(1)

    # get players
    player_urls: list[str] = create_player_urls(team_responses)
    player_responses = await fetch(
        player_urls,
        headers,
        max_at_once=10,
        max_per_second=5,
    )
    if not player_responses:
        sys.exit()

    # parse data for each player
    trees: list[HTMLParser] = list(map(parse_html, player_responses))
    player_data: list[Player] = [Player(tree) for tree in trees]
    return [player.output() for player in player_data]
