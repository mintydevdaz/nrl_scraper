import logging
from pathlib import Path


class File:
    @staticmethod
    def path(folder_name: str) -> str:
        # Point to specified folder within project
        directory = Path().absolute().joinpath(folder_name)

        if directory.exists():
            return str(directory)

        msg = f"The specified path '{directory}' does not exist!"
        raise FileNotFoundError(msg)


def logger(directory: str, filename: str = "app.log") -> None:
    logging.basicConfig(
        filename=f"{directory}/{filename}",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s | %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
