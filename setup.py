from setuptools import setup, find_packages


with open("requirements.txt") as file:
    requirements = file.read().splitlines()


setup(
    name="big-numbers",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    author="Fabio Antonio Astore",
    author_email="astore.a.fabio@gmail.com",
    description="Python lib to worker with big numbers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/fabioantonioastore/big-numbers",
)
