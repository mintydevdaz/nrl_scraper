import logging

import httpx


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
