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
        "numpy",
        "pdoc",
        "pynvml",
        "psutil",
        "plotly",
        "kaleido",
        "clang-format",
        "jinja2",
    ],
    data_files=[
        ("./geosongpu/experiments", ["./experiments/experiments.yaml"]),
        (
            "./geosongpu/templates",
            ["./geosongpu_ci/pipeline/templates/gpu-wrapper-slurm-mps.sh.tpl"],
        ),
        (
            "./geosongpu/interface/templates",
            [
                "./geosongpu_ci/tools/py_ftn_interface/templates/data_conversion.py.tpl",
                "./geosongpu_ci/tools/py_ftn_interface/templates/cuda_profiler.py.tpl",
            ],
        ),
    ],
    entry_points={
        "console_scripts": [
            "geosongpu_dispatch = geosongpu_ci.dispatch:cli",
            "geosongpu_hws = geosongpu_ci.tools.hws.cli:cli",
            "geosongpu_py_ftn_interface = geosongpu_ci.tools.py_ftn_interface.cli:cli",
        ],
    },
)

# --------------------------------------------------------------------------------------------------
