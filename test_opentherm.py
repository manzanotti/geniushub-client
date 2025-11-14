#!/usr/bin/env python3
"""Test script to verify OpenTherm support in geniushubclient."""

import asyncio
import json
import aiohttp
from geniushubclient import GeniusHub

# Replace these with your own Genius Hub credentials for testing
HUB_ADDRESS = "192.168.x.x"  # Your hub IP address
USERNAME = "your_username"     # Your Genius Hub username
PASSWORD = "your_password"     # Your Genius Hub password


async def main():
    """Test OpenTherm zone parsing."""
    print("Connecting to Genius Hub...")

    async with aiohttp.ClientSession() as session:
        hub = GeniusHub(
            hub_id=HUB_ADDRESS,
            username=USERNAME,
            password=PASSWORD,
            session=session,
        )

        hub.verbosity = 1  # Standard v1 API compatible output

        print("Fetching hub data...")
        await hub.update()

        print(f"\nHub UID: {hub.uid}")
        print(f"API Version: v{hub.api_version}")
        print(f"Number of zones: {len(hub.zones)}")

        # Find Zone 1 (OpenTherm zone)
        zone1 = hub.zone_by_id.get(1)

        if zone1:
            print(f"\n{'='*60}")
            print(f"Zone 1 Details:")
            print(f"{'='*60}")
            print(json.dumps(zone1.data, indent=2))

            # Check for OpenTherm specific data
            if "_opentherm" in zone1.data:
                print(f"\n{'='*60}")
                print(f"OpenTherm Specific Data:")
                print(f"{'='*60}")
                print(json.dumps(zone1.data["_opentherm"], indent=2))
            else:
                print("\nNote: No _opentherm data found in zone1.data")
                print("Checking raw zone data for 'opentherm' key...")
                if hasattr(zone1, '_raw') and 'opentherm' in zone1._raw:
                    print("Found 'opentherm' in raw data!")
                    print(json.dumps(zone1._raw['opentherm'], indent=2))
        else:
            print("\nERROR: Zone 1 not found!")
            print(f"Available zones: {list(hub.zone_by_id.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
