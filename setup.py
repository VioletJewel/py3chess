#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="Chessy",
    version="0.1dev",
    description="Exploratory chess engine for project",
    author="Violet McClure",
    # url="",
    include_package_data=True,
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={ "console_scripts": ["chessy = chess_box.ui:main"], },
    install_requires=[ "pygame", ],
)


