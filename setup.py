from setuptools import setup, find_packages

setup(
    name="new-grad-scraper",
    version="0.1.0",
    description="A job scraper for new graduate positions at top tech companies",
    author="Henry Huang",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "selenium>=4.15.0",
        "aiohttp>=3.9.0",
        "asyncio",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "colorama>=0.4.0",
        "tabulate>=0.9.0",
        "pydantic>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "scrape-jobs=src.main:main",
        ],
    },
    python_requires=">=3.8",
)