import logging

import httpx


class Client:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.session = httpx.AsyncClient(headers=headers)

    async def get(self, url: str, index: int | None = None):
        try:
            response = await self.session.get(url)
            response.raise_for_status()

        except httpx.RequestError as exc:
            logging.error(f"Error occurred while requesting '{url}': {exc}.")
            return None

        except httpx.HTTPStatusError as exc:
            msg = f"Error response {exc.response.status_code} while requesting {url}."
            logging.error(msg)
            return None

        else:
            if index:
                print(f"- {index}. {url}")
            return response

    async def close(self) -> None:
        await self.session.aclose()


def basic_request(url: str, headers: dict[str, str]) -> httpx.Response | None:
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()

    except httpx.RequestError as exc:
        logging.error(f"Error occurred while requesting '{url}': {exc}.")
        return None

    except httpx.HTTPStatusError as exc:
        msg = f"Error response {exc.response.status_code} while requesting {url}."
        logging.error(msg)
        return None

    else:
        return response
