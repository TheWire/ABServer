from setuptools import find_packages, setup

setup(
    name="ABServer",
    packages=find_packages(include=["ABServer"]),
    version="1.0.0",
    description="simple python/micropython web server/framework",
    author="Andrew Barber",
    license="MIT",
    install_requires=[],
)