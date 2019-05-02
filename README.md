[![CircleCI](https://circleci.com/gh/zxdavb/geniushub-client.svg?style=svg)](https://circleci.com/gh/zxdavb/geniushub-client)

# geniushub-client
This is a Python library to provide access to a **Genius Hub** by abstracting its [RESTful API](https://my.geniushub.co.uk/docs). It uses **aiohttp** and is therefore async-friendly.

This library can use either the **_offical_ v1 API** with a [hub token](https://my.geniushub.co.uk/tokens), or the **_latest_ v3 API** (using your own [username and password](https://www.geniushub.co.uk/app)). In either case, the library will return v1-compatible results wherever possible (this is not a trivial task).

If you use the v3 API, you can interrogate the hub directly, rather than via Heat Genius' own servers. Note that the v3 API is undocumented, and so this functionality may break at any time. In fact, the v3 to v1 conversion if best efforts and may even be broken as is for some edge cases - it was tested with HW, on/off (i.e. smart plugs), and radiators only.

It is a WIP, and is missing some functionality (e.g. schedules). In addition, there are some other limitations (see below).

It is based upon work by [@GeoffAtHome](https://github.com/zxdavb/geniushub-client/commits?author=GeoffAtHome) - thanks!

## Current limitations
Current limitations & to-dos include:
 - **ghclient.py** is not complete
 - schedules are read-only
 - when using the v3 API, zones sometimes have the wrong value for `occupied`

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

Option 2: hub **hostname/address** with **user credentials**:
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

You can compare any output to the 'official' API (v1 response):
```bash
curl -X GET https://my.geniushub.co.uk/v1/zones -H "authorization: Bearer ${HUB_TOKEN}"
python ghclient.py ${HUB_TOKEN} zones -v

curl -X GET https://my.geniushub.co.uk/v1/devices/summary -H "authorization: Bearer ${HUB_TOKEN}"
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices

curl -X GET https://my.geniushub.co.uk/v1/issues -H "authorization: Bearer ${HUB_TOKEN}"
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} issues
```

You can obtain the 'raw' v3 API responses (i.e. the JSON is not converted to the v1 schema):
```bash
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -vvv
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices -vvv
```

To obtain the 'official' v3 API responses takes a little work.  First, use python to obtain a `HASH`:
```python
>>> from hashlib import sha256
>>> hash = sha256()
>>> hash.update(("my_username" + "my_password").encode('utf-8'))
>>> print(hash.hexdigest())
001b24f45b...
```
Then you can use **curl**:
```bash
curl --user ${USERNAME}:${HASH} -X GET http://${HUB_ADDRESS}:1223/v3/zones
```

## Advanced Features
 When used as a library, there is the option to utilize the referencing module's own `aiohttp.ClientSession()` (recommended):
 ```python
import asyncio
import aiohttp
from geniushubclient import GeniusHubClient

my_session = aiohttp.ClientSession()

...

if not (username or password):
    client = GeniusHubClient(hub_id=hub_address, username, password, session=my_session)
else:
    client = GeniusHubClient(hub_id=hub_token, session=my_session)

hub = client.hub
await hub.update()  # enumerate all zones, devices and issues

client.verbosity = 0  # same as v1/zones/summary, v1/devices/summary
print(hub.zones)

client.verbosity = 1  # default, same as v1/zones, v1/devices, v1/issues
print(hub.devices)

print(hub.zone_by_id[3].temperature)

await session.close()
```

### QA/CI via CircleCI
QA includes comparing JSON from **cURL** with output from this app using **diff**, for example:
```bash
(venv) root@hostname:~/$ curl -X GET https://my.geniushub.co.uk/v1/zones -H "authorization: Bearer ${HUB_TOKEN}" | \
    python -c "import sys, json; print(json.load(sys.stdin))" > a.out
    
(venv) root@hostname:~/$ python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -v > b.out

(venv) root@hostname:~/$ diff a.out b.out
```
