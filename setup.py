#!/usr/bin/env python3
"""
Setup configuration for US Company Dossier skill
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the requirements
requirements_path = Path(__file__).parent / "requirements.txt"
with open(requirements_path) as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="us-company-dossier",
    version="1.0.0",
    description="Build comprehensive company research dossiers from SEC EDGAR and IR materials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpenClaw",
    author_email="research@openclaw.ai",
    url="https://github.com/openclaw/us-company-dossier",
    py_modules=[
        "us_company_dossier",
        "us_company_dossier_optimized",
        "cli",
        "config",
        "demo"
    ],
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "us-dossier=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="sec edgar financial research company dossier investor relations",
    package_data={
        "": ["ticker_cik_map.json", "*.md"],
    },
    include_package_data=True,
)
