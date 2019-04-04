# GeniusHub
This is a Python library to provide access to the [Genius Hub RESTful API](https://my.geniushub.co.uk/docs). It is a WIP, and is currently read-only (e.g. you can't change the mode of a zone).

This library can use either the _offical_ v1 API via a [hub token](https://my.geniushub.co.uk/tokens), or the _latest_ v3 API direct to the hub (using your own [username and password](https://www.geniushub.co.uk/app)). In either case, the library will return v1-compatible results wherever possible.

It is based upon work by @GeoffAtHome - thanks!

# Installation
Either clone this repository and run `python setup.py install`, or install from pip using `pip install geniushub-client`.

# Using the Library
See `ghclient.py` for example code. You can also use `ghclient.py` for ad-hoc queries:
```bash
python ghclient.py -?
```
You require either
 - a hub token to query HeatGenius' servers via the v1 API or 
 - a hub hostname/address, `username` and `password` to directly query the hub via the v3 API
 
```bash
HUB_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlciI6IjEuM..."  # from: https://my.geniushub.co.uk/tokens
HUB_ADDRESS="my-hub.dyndns.com"                                   # either hostname, or IP address
USERNAME=my_username                                              # used for: https://www.geniushub.co.uk/app
PASSWORD=my_password

python ghclient.py ${HUB_TOKEN} zones -vv
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -v
```

You can compare any output to the official API:
```bash
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones
curl -X GET https://my.geniushub.co.uk/v1/zones/summary -H "authorization: Bearer ${HUB_TOKEN}"
```

# Advanced Features
 It uses **aiohttp** and is therefore asyncio-friendly.
 
 It can utilize your own `aiohttp.ClientSession()` rather than creating another:
 ```python
client = GeniusHub(hub_id=ip_address, username, password, session=my_session)
```
 
