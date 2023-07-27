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
        "click",
    ],
    data_files=[
        ("./geosongpu/experiments", ["./experiments/experiments.yaml"]),
    ],
    entry_points={
        "console_scripts": [
            "geosongpu_dispatch = geosongpu_ci.dispatch:cli_dispatch",
        ],
    },
)

# --------------------------------------------------------------------------------------------------
