import logging
from functools import partial
from json import JSONDecodeError

from aiometer import run_all
from httpx import Response

from src.web import Client


def create_urls(
    base_url: str,
    comp_id: int,
    year: int,
    stat_ids: list[int],
) -> list[str]:
    return [base_url.format(comp_id=comp_id, year=year, id=id) for id in stat_ids]


async def fetch(urls: list[str], headers: dict[str, str]) -> list:
    # open session
    client = Client(headers)

    # send requests
    results = await run_all(
        [partial(client.get, url) for url in urls],
        max_per_second=5,
    )

    # close session
    await client.close()

    # remove None results
    return list(filter(lambda x: isinstance(x, Response), results))


def extract_stats(responses: list[Response]) -> list | list[dict]:
    try:
        data = [r.json()["totalStats"] for r in responses]
    except (JSONDecodeError, KeyError) as exc:
        logging.error(f"Error unpacking JSON response: {exc}.")
        return []
    else:
        return data


def parse_stats(raw_data: list[dict]) -> list[dict]:
    results = []
    for stat in raw_data:
        title: str = stat["title"]
        teams = list(
            map(
                lambda x: {
                    "team": x["teamNickName"],
                    "value": x["value"],
                    "played": x["played"],
                },
                stat["leaders"],
            )
        )
        results.append({"stat": title, "leaders": teams})
    return results


async def get(env: dict) -> list[dict] | None:
    # unpack environment vars
    headers: dict[str, str] = env["web"]["headers"]
    comp_id: int = env["team_stats"]["comp_id"]
    year: int = env["team_stats"]["year"]
    stat_ids: list[int] = env["team_stats"]["ids"]
    base_url: str = env["team_stats"]["base_url"]

    # apply stat ids to urls
    urls: list[str] = create_urls(base_url, comp_id, year, stat_ids)

    # send requests
    if not (responses := await fetch(urls, headers)):
        return None

    if not (raw_stats := extract_stats(responses)):
        return None

    return parse_stats(raw_stats)
