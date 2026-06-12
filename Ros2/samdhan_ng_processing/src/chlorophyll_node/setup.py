from glob import glob
from setuptools import find_packages, setup


package_name = "chlorophyll_node"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="soumik",
    maintainer_email="soumik@example.com",
    description="ROS 2 node for GNSS-triggered chlorophyll image analysis.",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "chlorophyll_node = chlorophyll_node.chloro_node:main",
        ],
    },
)
