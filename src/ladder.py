import logging
from json import JSONDecodeError

from httpx import Response

from src import web
from src.models import Ladder, Stats


def team_positions(data: list[dict]) -> list[dict]:
    results = []
    for team in data:
        try:
            name: str = team.get("teamNickname", "Error fetching name")
            stats: dict = team["stats"]
            ladder = Ladder(name=name, stats=Stats(**stats))

        except Exception as exc:
            logging.error(f"Unable to parse ladder data: {exc}")
            continue

        else:
            results.append(ladder.model_dump(by_alias=True))

    return results


def unpack_json(response: Response) -> list[dict] | None:
    try:
        data = response.json()["positions"]
    except (JSONDecodeError, KeyError) as exc:
        logging.error(f"Error unpacking JSON response: {exc}.")
        return None
    else:
        return data


def get(env: dict) -> list[dict] | None:
    # unpack environment vars
    headers: dict[str, str] = env["web"]["headers"]
    comp_id: int = env["ladder"]["comp_id"]
    round_num: int = env["ladder"]["round"]
    year: int = env["ladder"]["year"]
    base_url: str = env["ladder"]["base_url"]

    # http request
    url: str = base_url.format(comp_id=comp_id, round_num=round_num, year=year)
    if not (response := web.basic_request(url, headers)):
        return None

    return team_positions(data) if (data := unpack_json(response)) else None
