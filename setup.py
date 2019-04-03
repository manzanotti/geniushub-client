import setuptools

VERSION = "0.2.1"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="geniushub-client",
    version=VERSION,
    author="David Bonnes",
    author_email="zxdavb@gmail.com",
    description="A client for Genius Hub systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zxdavb/geniushub-client",
    packages=setuptools.find_packages(),
    keywords = ['genius', 'geniushub', 'heatgenius'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Development Status :: "4 - Beta",
    ],
)