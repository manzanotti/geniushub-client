#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""The setup.py file."""

import versioneer
from setuptools import find_packages, setup

URL = "https://github.com/manzanotti/geniushub-client"

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

VERSION = versioneer.get_version()

setup(
    name="geniushub-client",
    description="An aiohttp-based client for Genius Hub systems",
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
        "Bug Reports": "{URL}/issues",
        "Source": "{URL}",
    },
    cmdclass=versioneer.get_cmdclass(),
)
