import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='genius',
    version='0.1',
    description='Python library to provide connect to Genius Hub on a local network.',
    url='https://github.com/GeoffAtHome/genus',
    author='Geoff Soord',
    author_email='geoff@soord.org.uk',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    packages=setuptools.find_packages(),
    keywords=['Genius', 'Genius Hub',
              'Heat Genius', 'Heat Genius Hub'],
    zip_safe=False
)
