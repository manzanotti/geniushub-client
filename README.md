[![CircleCI](https://circleci.com/gh/manzanotti/geniushub-client.svg?style=svg)](https://circleci.com/gh/manzanotti/geniushub-client) [![Join the chat at https://gitter.im/geniushub-client/community](https://badges.gitter.im/geniushub-client/community.svg)](https://gitter.im/geniushub-client/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/geniushub-client)

# geniushub-client
This is a Python library to provide access to a **Genius Hub** by abstracting its [RESTful API](https://my.geniushub.co.uk/docs). It uses **aiohttp** and is therefore async-friendly.

This library can use either the **_offical_ v1 API** with a [hub token](https://my.geniushub.co.uk/tokens), or the **_latest_ v3 API** (using your own [username and password](https://www.geniushub.co.uk/app)). In either case, the library will return v1-compatible results wherever possible (this is not a trivial task).

If you use the v3 API, you can interrogate the hub directly, rather than via Heat Genius' own servers. Note that the v3 API is undocumented, and so this functionality may break at any time. In fact, the v3 to v1 conversion if best efforts and may even be broken as is for some edge cases - it was tested with HW, on/off (i.e. smart plugs), and radiators only.

It is a WIP, and may be missing some functionality. In addition, there are some other limitations (see below).

It is based upon work by [@GeoffAtHome](https://github.com/manzanotti/geniushub-client/commits?author=GeoffAtHome) and [@zxdavb]](https://github.com/manzanotti/geniushub-client/commits?author=zxdavb) - thanks!

## Current limitations
Current limitations & to-dos include:
 - **ghclient.py** is not complete
 - schedules are read-only
 - when using the v3 API, zones sometimes have the wrong value for `occupied`

 The library will return v1 API responses wherever possible, however:
  1. the only code available to reverse-engineer is from the web app, but
  2. the Web app does not correlate completely with the v1 API (e.g. issue messages, occupied state)

Thus, always check your output against the corresponding v1 API response rather than the web app.

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
  - interrogates the hub directly (so is faster), via port :1223

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
curl -H "authorization: Bearer ${HUB_TOKEN}" -X GET https://my.geniushub.co.uk/v1/zones/summary
python ghclient.py ${HUB_TOKEN} zones

curl -H "authorization: Bearer ${HUB_TOKEN}" -X GET https://my.geniushub.co.uk/v1/devices
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices -v

curl -H "authorization: Bearer ${HUB_TOKEN}" -X GET https://my.geniushub.co.uk/v1/issues
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
 When used as a library, there is the option to utilize the referencing module's own `aiohttp.ClientSession()` (recommended).

 Here is an example, but see **ghclient.py** for a more complete example:
 ```python
import asyncio
import aiohttp
from geniushubclient import GeniusHub

my_session = aiohttp.ClientSession()

...

if not (username or password):
    hub = GeniusHub(hub_id=hub_address, username=username, password=password, session=my_session)
else:
    hub = GeniusHub(hub_id=hub_token, session=my_session)

await hub.update()  # enumerate all zones, devices and issues

hub.verbosity = 0  # same as v1/zones/summary, v1/devices/summary
print(hub.zones)

hub.verbosity = 1  # default, same as v1/zones, v1/devices, v1/issues
print(hub.devices)

print(hub.zone_by_id[3].data["temperature"])
print(hub.device_by_id["2-2"].data)

await my_session.close()
```

### Unit tests

Please see the README.md file in the tests folder for more details on unit tests protocol.

### QA/CI via CircleCI
QA includes comparing JSON from **cURL** with output from this app using **diff**, for example:
```bash
(venv) root@hostname:~/$ curl -X GET https://my.geniushub.co.uk/v1/zones -H "authorization: Bearer ${HUB_TOKEN}" | \
    python -c "import sys, json; print(json.dumps(json.load(sys.stdin, parse_float=lambda x: int(float(x))), indent=4, sort_keys=True))" > a.out

(venv) root@hostname:~/$ python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -v | \
    python -c "import sys, json; print(json.dumps(json.load(sys.stdin, parse_float=lambda x: int(float(x))), indent=4, sort_keys=True))" > b.out

(venv) root@hostname:~/$ diff a.out b.out
```
