"""Python client library for the Genius Hub API."""

HTTP_OK = 200  # cheaper than: from http import HTTPStatus.OK

DEFAULT_TIMEOUT_V1 = 10
DEFAULT_TIMEOUT_V3 = 60

DEFAULT_INTERVAL_V1 = 300
DEFAULT_INTERVAL_V3 = 30

API_STATUS_ERROR = {
    400: "The request body or request parameters are invalid.",
    401: "The authorization information is missing or invalid.",
    404: "No zone/device with the specified ID was found "
         "(or the state property does not exist on the specified device).",
    502: "The hub is offline.",
    503: "The authorization information is invalid.",
}

ZONE_MODE_MAP = {
    1: 'off',
    2: 'timer',
    4: 'footprint',
    8: 'away',
    16: 'boost',
    32: 'early',
    64: 'test',
    128: 'linked',
    256: 'other'
}
