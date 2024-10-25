import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import tomllib


class File:
    @staticmethod
    def path(route: str) -> str:
        "Points to root folder of project (i.e. nrl_scraper)."
        f = Path().absolute().joinpath(route)

        if f.exists():
            return str(f)

        msg = f"The specified path '{f}' does not exist!"
        raise FileNotFoundError(msg)


def utc_date(format: str = "%Y-%m-%d %H:%M:%S%z") -> str:
    now: datetime = datetime.now(timezone.utc)
    return now.strftime(format)


def save_to_json(data_object: Iterable, route: str, filename: str) -> None:
    filepath: str = f"{route}/{filename}.json"
    date: str = utc_date()
    file_object: dict = {"date": date, "data": data_object}
    with open(filepath, "w") as f:
        json.dump(file_object, f)
    print(f"File saved to JSON at '{filepath}'")


def logger(filepath: str) -> None:
    logging.basicConfig(
        filename=filepath,
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)s | %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )


def load_env(filepath: str) -> dict:
    with open(filepath, "rb") as f:
        data = tomllib.load(f)
    return data
