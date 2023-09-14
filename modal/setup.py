from setuptools import setup, find_packages

setup(
    name="modal",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["modal=modal.__main__:app"]
    }
)

