# (C) Copyright 2021-2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

# Setup and installation script
#
# Usage: "pip install --prefix=/path/to/install ."

# --------------------------------------------------------------------------------------------------

import os.path
import setuptools

setuptools.setup(
    name="geosongpu_ci",
    author="NASA Advanced Software and Technology Group",
    description="On-premise continuous integration for the GEOS on GPU project",
    url="https://github.com/geos-esm/geosongpu-ci",
    packages=setuptools.find_packages(exclude=["test"]),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
    install_requires=[
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "geosongpu_dispatch = geosongpu_ci.dispatch:main",
        ],
    },
)

# --------------------------------------------------------------------------------------------------
