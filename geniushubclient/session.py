"""Python client library for the Genius Hub API."""

import logging
from hashlib import sha256

import aiohttp

from .const import DEFAULT_TIMEOUT_V1, DEFAULT_TIMEOUT_V3

_LOGGER = logging.getLogger(__name__)


class GeniusService:
    """Handle all communication to the Genius Hub."""

    def __init__(self, hub_id, username=None, password=None, session=None) -> None:
        self._session = session if session else aiohttp.ClientSession()

        if username or password:  # use the v3 Api
            sha = sha256()
            sha.update((username + password).encode("utf-8"))
            self._auth = aiohttp.BasicAuth(login=username, password=sha.hexdigest())
            self._url_base = f"http://{hub_id}:1223/v3/"
            self._headers = {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
        else:
            self._auth = None
            self._url_base = "https://my.geniushub.co.uk/v1/"
            self._headers = {"authorization": f"Bearer {hub_id}"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)

    async def request(self, method, url, data=None):
        """Perform a request."""
        _LOGGER.debug("request(method=%s, url=%s, data=%s)", method, url, data)

        http_method = {
            "GET": self._session.get,
            "PATCH": self._session.patch,
            "POST": self._session.post,
            "PUT": self._session.put,
        }.get(method)

        try:
            async with http_method(
                self._url_base + url,
                auth=self._auth,
                headers=self._headers,
                json=data,
                raise_for_status=True,
                timeout=self._timeout,
            ) as resp:
                response = await resp.json(content_type=None)

        except aiohttp.ServerDisconnectedError as exc:
            _LOGGER.debug("request(): ServerDisconnectedError (msg=%s), retrying.", exc)
            async with http_method(
                self._url_base + url,
                auth=self._auth,
                headers=self._headers,
                json=data,
                raise_for_status=True,
                timeout=self._timeout,
            ) as resp:
                response = await resp.json(content_type=None)

        if method != "GET":
            _LOGGER.debug("request(): response=%s", response)
        return response

    @property
    def use_v1_api(self) -> bool:
        """Return True is using the v1 API."""
        return self._auth is None
