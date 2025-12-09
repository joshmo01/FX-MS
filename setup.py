#!/usr/bin/env python3
"""
FX Smart Routing Engine - Setup Configuration

Universal FX routing across Fiat, CBDC, and Stablecoin rails.

Author: Fintaar.ai
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="fx-smart-routing",
    version="2.0.0",
    author="Fintaar.ai",
    author_email="engineering@fintaar.ai",
    description="Universal FX Smart Routing Engine with CBDC and Stablecoin Support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshmo01/FX-MS",
    packages=find_packages(exclude=["tests", "tests.*", "scripts"]),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.0",
        "aiohttp>=3.9.0",
        "python-dateutil>=2.8.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
        ],
        "blockchain": [
            "web3>=6.11.0",
            "solana>=0.30.0",
        ],
        "database": [
            "asyncpg>=0.29.0",
            "redis>=5.0.0",
            "sqlalchemy>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fx-routing=app.main:main",
            "fx-demo=demo_all_routes:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: FastAPI",
    ],
    keywords=[
        "fx", "foreign-exchange", "routing", "cbdc", "stablecoin",
        "fintech", "banking", "payments", "mbridge", "atomic-swap"
    ],
    include_package_data=True,
    package_data={
        "": ["config/*.json", "app/static/*.jsx"],
    },
)
