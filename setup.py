#!/usr/bin/env python3
"""
Cellgain Ventus - Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cellgain-ventus",
    version="0.1.0",
    author="Cellgain",
    author_email="contact@cellgain.com",
    description="I2C-based Fan Controller System for Embedded Linux Platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cellgain/cellgain-ventus",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "smbus2>=0.4.0",          # I2C communication
        "filelock>=3.12.0",       # Cross-process I2C locking
        "PyYAML>=6.0",            # Configuration
        "pydantic>=2.0",          # Data validation
        "colorlog>=6.7",          # Logging
    ],
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-cov>=4.1",
            "black>=23.0",
            "isort>=5.12",
            "mypy>=1.5",
        ],
        "grpc": [
            "grpcio>=1.60.0",
            "grpcio-tools>=1.60.0",
            "grpcio-reflection>=1.60.0",
            "protobuf>=4.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ventus-server=ventus.server.__main__:main",
            "ventus-client=ventus.client:main",
        ],
    },
    package_data={
        "ventus": [
            "proto/*.proto",
            "config/*.yaml",
        ],
    },
    include_package_data=True,
)
