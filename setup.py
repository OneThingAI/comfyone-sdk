from setuptools import setup, find_packages

setup(
    name="comfyone-sdk",
    version="0.1.2",
    packages=["comfyone"],
    install_requires=[
        "requests>=2.25.0",
        "websocket-client>=1.0.0",
        "pydantic>=1.10.0",
        "pylint>=2.17.0",
        "fastapi>=0.100.0",
        "sqlalchemy>=2.0.0",
    ],
    python_requires=">=3.7",
) 