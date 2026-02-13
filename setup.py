"""
CURC LLM Hoster Setup

Author: Patrick Cooper
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="curc-llm-hoster",
    version="0.1.0",
    author="Patrick Cooper",
    description="High-performance LLM inference infrastructure for CURC resources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/patrickcooper/curc-llm-hoster",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.9",
    install_requires=[
        "vllm>=0.3.0",
        "ray[default]>=2.9.0",
        "openai>=1.0.0",
        "httpx>=0.24.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "curc-llm=src.client.curc_llm_client:main",
        ],
    },
)
