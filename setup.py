import os
import sys

from setuptools import find_packages, setup
from setuptools.command.install import install

VERSION = "0.6.30p1"

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our VERSION."""

    def run(self):
        tag = os.getenv("CIRCLE_TAG")

        if tag != VERSION:
            info = "Git tag: {tag} does not match the version of this pkg: {VERSION}"
            sys.exit(info)


setup(
    name="geniushub-client",
    version=VERSION,
    packages=find_packages(),
    install_requires=["aiohttp=>3.6.1"],
    # metadata to display on PyPI
    author="David Bonnes",
    author_email="zxdavb@gmail.com",
    description="A aiohttp-based client for Genius Hub systems",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/zxdavb/geniushub-client",
    download_url="{url}tarball/{VERSION}",
    keywords=["genius", "geniushub", "heatgenius"],
    license="XXX",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.7",
        "Topic :: Home Automation",
    ],
    cmdclass={"verify": VerifyVersionCommand},
)
