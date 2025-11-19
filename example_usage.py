#!/usr/bin/env python3
"""
Example usage demonstrating the enhanced device parsing functionality.

This example shows how to use the new device property accessors and methods
added to access detailed device information from the v3 API.

Requirements:
    - Create a .env file with your credentials:
        GENIUS_USER=your_username
        GENIUS_PASS=your_password
        GENIUS_HUB_IP=your_hub_ip  (optional, defaults to 192.168.1.100)
    - Install: pip install aiohttp geniushubclient
"""

import asyncio
import os
from datetime import datetime

import aiohttp

# Load credentials from .env file
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    print("ERROR: .env file not found.")
    print("Please create a .env file with:")
    print("  GENIUS_USER=your_username")
    print("  GENIUS_PASS=your_password")
    print("  GENIUS_HUB_IP=your_hub_ip")
    exit(1)

from geniushubclient import GeniusHub


async def main():
    """Example usage as specified in requirements."""

    # Initialize the hub connection
    # Replace with your hub's IP address or hostname
    hub_ip = os.environ.get('GENIUS_HUB_IP', '192.168.1.100')  # Change to your hub IP

    async with aiohttp.ClientSession() as session:
        hub = GeniusHub(
            hub_id=hub_ip,
            username=os.environ.get('GENIUS_USER'),
            password=os.environ.get('GENIUS_PASS'),
            session=session
        )

        # Fetch latest data
        await hub.update()

        # EXAMPLE USAGE (as requested):
        devices = hub.get_devices()

        for device in devices:
            print(f"{device.id}: {device.type} in {device.location}")

            if device.device_model:
                print(f"  Model: {device.device_model}")

            if device.battery_level is not None:
                print(f"  Battery: {device.battery_level}%")

            if device.last_communication:
                last_seen = datetime.fromtimestamp(device.last_communication)
                print(f"  Last seen: {last_seen}")

            if device.setpoint is not None:
                print(f"  Setpoint: {device.setpoint}°C")

            if device.measured_temperature is not None:
                print(f"  Current temp: {device.measured_temperature}°C")

            # Additional useful information
            if device.valve_offset is not None:
                print(f"  Valve offset: {device.valve_offset}°C")

            if device.protocol_version:
                print(f"  Protocol: {device.protocol_version}")

            print()  # Blank line between devices


if __name__ == "__main__":
    asyncio.run(main())
