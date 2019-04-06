# geniushub-client
This is a Python library to provide access to a **Genius Hub** via its [RESTful API](https://my.geniushub.co.uk/docs). It uses **aiohttp** and is therefore asyncio-friendly.

It is a WIP, and is currently read-only (e.g. you can't change the mode of a zone).

This library can use either the **_offical_ v1 API** with a [hub token](https://my.geniushub.co.uk/tokens), or the **_latest_ v3 API** (using your own [username and password](https://www.geniushub.co.uk/app)). In either case, the library will return v1-compatible results wherever possible (this is not a trivial task).

If you use the v3 API, you can interrogate the hub directly, rather than via Heat Genius' servers. Note that the v3 API is undocumented, and this functionality may break at any time.

It is based upon work by @GeoffAtHome - thanks!

## Installation
Either clone this repository and run `python setup.py install`, or install from pip using `pip install geniushub-client`.

## Using the Library
See `ghclient.py` for example code. You can also use `ghclient.py` for ad-hoc queries:
```bash
python ghclient.py -?
```
There are two distinct options for accessing a Genius Hub:

Option 1: **hub token** only:
  - requires a hub token obtained from https://my.geniushub.co.uk/tokens
  - uses the v1 API - which is well-documented
  - interrogates Heat Genius' own servers (so is slower)
 
Option 2: **hub hostname/address** with **user credentials**:
  - requires your `username` & `password`, as used with https://www.geniushub.co.uk/app
  - uses the v3 API - results are WIP and may not be what you expect
  - interrogates the hub directly (so is faster)

```bash
HUB_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlc..."
HUB_ADDRESS="my-geniushub.dyndns.com"
USERNAME="my-username"
PASSWORD="my-password"

python ghclient.py ${HUB_TOKEN} issues

python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -v
```

You can compare any output to the official API (v1 response):
```bash
curl -X GET https://my.geniushub.co.uk/v1/zones -H "authorization: Bearer ${HUB_TOKEN}"
python ghclient.py ${HUB_TOKEN} zones -vv

curl -X GET https://my.geniushub.co.uk/v1/devices/summary -H "authorization: Bearer ${HUB_TOKEN}"
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices
```

You can obtain the actual v3 API responses (i.e. the JSON is not converted to the v1 schema):
```bash
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -vvvv
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices -vvvv
```

## Advanced Features
 When used as a library, there is the option to utilize the rerencing module's own `aiohttp.ClientSession()` (recommended):
 ```python
import asyncio
import aiohttp
from geniushubclient import GeniusHubClient, GeniusHub

session = aiohttp.ClientSession()

if not (username or password):
    client = GeniusHubClient(hub_id=hub_address, username, password, session=session)
else:
    client = GeniusHubClient(hub_id=hub_token, session=my_session)
    
hub = GeniusHub(client, hub_id=args.hub_id[:20])

print(await hub.zones)
print(hub.zone_by_id[3].temperature)

await session.close()
```
 
