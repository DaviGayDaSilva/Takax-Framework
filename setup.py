#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="takax",
    version="1.0.0",
    description="Create Linux OS via chat - Open-source framework",
    author="Takax Team",
    author_email="team@takax.io",
    url="https://github.com/takax/takax-framework",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "takax=cli.main:main",
            "takax-server=cloud.app:run_server",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="linux os build framework cli cloud sdk",
    project_urls={
        "Documentation": "https://takax.readthedocs.io",
        "Source": "https://github.com/takax/takax-framework",
        "Tracker": "https://github.com/takax/takax-framework/issues",
    },
)