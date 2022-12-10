#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""The setup.py file."""

from setuptools import find_packages, setup

with open("geniushubclient/__init__.py") as fh:
    for line in fh:
        if line.strip().startswith("__version__"):
            VERSION = eval(line.split("=")[-1])
            break

URL = "https://github.com/manzanotti/geniushub-client"

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()


setup(
    name="geniushub-client",
    description="A aiohttp-based client for Genius Hub systems",
    keywords=["genius", "geniushub", "heatgenius"],
    author="Paul Manzotti",
    author_email="manzo@gorilla-tactics.com",
    url=URL,
    download_url=f"{URL}/archive/{VERSION}.tar.gz",
    install_requires=["aiohttp"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["test", "docs"]),
    version=VERSION,
    license="MIT",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Home Automation",
    ],
    project_urls={  # Optional
        "Bug Reports": "https://github.com/manzanotti/geniushub-client/issues",
        "Source": "https://github.com/manzanotti/geniushub-client/",
    },
)
