import setuptools

VERSION = "0.4.12"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="geniushub-client",
    version=VERSION,
    author="David Bonnes & Geoff Soord",
    author_email="zxdavb@gmail.com",
    description="A aiohttp-based client for Genius Hub systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zxdavb/geniushub-client",
    download_url = 'https://github.com/zxdavb/geniushub-client/archive/VERSION.tar.gz',
    packages=setuptools.find_packages(),
    keywords = ['genius', 'geniushub', 'heatgenius'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
)
