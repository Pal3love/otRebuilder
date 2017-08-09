#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages


setup(
    name = "otrebuilder",
    version = "1.4.2",
    description = "A simple tool to resolve OpenType fonts' mapping and naming issues, powered by fontTools.",
    author = "Pal3love",
    author_email = "pal3love@gmail.com",
    maintainer = "Pal3love",
    maintainer_email = "pal3love@gmail.com",
    url = "https://github.com/Pal3love/otRebuilder",
    license = "MIT",
    platforms = ["Any"],
    packages = find_packages("Package"),
    package_dir = {'': 'Package'},
    include_package_data = True,
    data_files = [('otRebuilder/Dep', ['Package/otRebuilder/Dep/Readme.txt'])],
    install_requires = ['toml', 'fonttools', 'cu2qu', 'ufoLib'],
    entry_points = {
        'console_scripts': [
            "otrebuild = otRebuilder.otrebuild:main"
        ]
    },
    zip_safe = True,
    classifiers = [
    "Environment :: Console",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 2.7"
    ],
)
