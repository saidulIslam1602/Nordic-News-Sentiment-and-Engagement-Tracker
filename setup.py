#!/usr/bin/env python3
"""
Setup script for Nordic News Sentiment & Engagement Tracker
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="nordic-news-tracker",
    version="1.0.0",
    author="Nordic News Analytics Team",
    author_email="analytics@nordicnews.com",
    description="A comprehensive data analytics platform for tracking sentiment and engagement across Nordic news media",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/nordicnews/analytics-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "production": [
            "gunicorn>=21.2.0",
            "psycopg2-binary>=2.9.9",
            "redis>=4.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nordic-tracker=scripts.run_pipeline:main",
            "nordic-init=scripts.init_database:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "*.md", "*.txt"],
    },
    zip_safe=False,
)