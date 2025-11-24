#!/usr/bin/env python3
"""
microchip-emc2305 - Setup Configuration

Python driver for the Microchip EMC2305 5-channel PWM fan controller.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")
else:
    long_description = "Python driver for Microchip EMC2305 fan controller"

setup(
    name="microchip-emc2305",
    version="0.1.0",
    author="Jose Luis Moffa",
    author_email="moffa3@gmail.com",
    description="Python driver for Microchip EMC2305 5-channel PWM fan controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moffa90/python-emc2305",
    project_urls={
        "Bug Tracker": "https://github.com/moffa90/python-emc2305/issues",
        "Documentation": "https://github.com/moffa90/python-emc2305",
        "Source Code": "https://github.com/moffa90/python-emc2305",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: No Input/Output (Daemon)",
    ],
    keywords="emc2305 microchip fan controller pwm i2c hardware driver smbus",
    python_requires=">=3.9",
    install_requires=[
        "smbus2>=0.4.0",          # I2C communication
        "filelock>=3.12.0",       # Cross-process I2C locking
    ],
    extras_require={
        "config": [
            "PyYAML>=6.0",        # Configuration file support
        ],
        "dev": [
            "pytest>=7.4",
            "pytest-cov>=4.1",
            "black>=23.0",
            "isort>=5.12",
            "mypy>=1.5",
            "ruff>=0.1.0",
        ],
        "grpc": [
            "grpcio>=1.60.0",
            "grpcio-tools>=1.60.0",
            "protobuf>=4.25.0",
        ],
    },
    package_data={
        "emc2305": [
            "py.typed",           # PEP 561 type information
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="MIT",
)
