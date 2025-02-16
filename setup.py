from setuptools import find_packages, setup

setup(
    name="ABServer",
    packages=find_packages(include=["ABServer"]),
    version="1.0.3",
    description="simple python/micropython web server/framework",
    author="Andrew Barber",
    license="GPLV2",
    install_requires=[],
)