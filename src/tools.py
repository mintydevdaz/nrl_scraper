import logging
import tomllib
from pathlib import Path


class File:
    @staticmethod
    def path(route: str) -> str:
        # Point to specified folder within project
        f = Path().absolute().joinpath(route)

        if f.exists():
            return str(f)

        msg = f"The specified path '{f}' does not exist!"
        raise FileNotFoundError(msg)


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
