from setuptools import find_packages, setup

setup(
    name="queens",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
