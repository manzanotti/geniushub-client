import setuptools

VERSION = "0.2.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='geniushubclient',
    version=VERSION,
    description='Python client for connecting to a Genius Hub.',
    url='https://github.com/GeoffAtHome/geniushub-client',
    author='Geoff Soord',
    author_email='geoff@soord.org.uk',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    packages=setuptools.find_packages(),
    keywords=['Genius', 'Genius Hub', 'Heat Genius', 'Heat Genius Hub'],
    install_requires=['aiohttp'],
    zip_safe=False
)
