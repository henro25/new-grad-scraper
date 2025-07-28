# 🎯 New Grad Job Scraper

A comprehensive job scraper designed specifically for finding new graduate positions at top companies.

## ✨ Features

- **🏢 65+ Top Companies**: Covers FAANG, trading firms, AI companies, startups, and more
- **🎯 Smart Job Matching**: AI-powered filtering for SWE, ML, Data Science, and Quant roles
- **⚡ Concurrent Scraping**: Fast, respectful scraping with rate limiting
- **📊 Rich Output**: Beautiful terminal tables, JSON, and CSV exports
- **🔧 Modular Architecture**: Easy to extend with new companies and scrapers
- **🛡️ Ethical Scraping**: Built-in rate limiting and respectful request patterns

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/henro25/new-grad-scraper.git
cd new-grad-scraper

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Basic Usage

```bash
# Scrape all companies
python run_scraper.py scrape

# Filter by company tiers
python run_scraper.py scrape --tiers big_tech --tiers trading_and_finance

# Target specific companies
python run_scraper.py scrape --companies Google --companies Apple --companies Netflix

# Save results to file
python run_scraper.py scrape --save --output-format json

# Test a single company
python run_scraper.py test-company Google
```

## 🏢 Supported Companies

### Big Tech (8 companies)
- Google, Apple, Microsoft, Netflix, Amazon, Meta, TikTok, Spotify

### Trading & Finance (10 companies)
- Jane Street, DRW, HRT, Optiver, IMC, SIG, Citadel, Five Rings, Chicago Trading, Point72

### AI & Data (7 companies)
- Palantir, OpenAI, Anthropic, Scale AI, Cursor, C3.ai, Hugging Face

### And many more across fintech, mobility, enterprise, and hardware!

## 🎯 Target Roles

- **Software Engineering**: Backend, Frontend, Full-Stack, Mobile, Systems
- **Machine Learning**: ML Engineer, AI Researcher, Applied Scientist
- **Data Science**: Data Scientist, Analytics Engineer, Business Intelligence
- **Quantitative Research**: Quant Researcher, Algorithmic Trading, Risk Analysis

## 📊 Sample Output

```
🎯 Starting new grad job search...
⚡ Using 5 concurrent requests
⏳ Scraping in progress...

=== JOB SEARCH RESULTS ===
📊 Found 127 new grad positions from 42/45 companies
⭐ Average match score: 0.78

📋 Jobs by Category:
  Software Engineering: 68
  Machine Learning: 32
  Data Science: 19
  Quantitative Research: 8

🎯 Top Matches:
╒══════════════╤══════════════════════════════════════════════════╤═══════════════════════╤═══════════════════════════╤═════════╤══════════════╕
│ Company      │ Position                                         │ Category              │ Location                  │ Score   │ Tier         │
╞══════════════╪══════════════════════════════════════════════════╪═══════════════════════╪═══════════════════════════╪═════════╪══════════════╡
│ Google       │ Software Engineer, New Grad 2026                │ software_engineering  │ Mountain View, CA         │ 0.95    │ big_tech     │
├──────────────┼──────────────────────────────────────────────────┼───────────────────────┼───────────────────────────┼─────────┼──────────────┤
│ Jane Street  │ Software Developer - New Grad                    │ software_engineering  │ New York, NY              │ 0.92    │ trading      │
└──────────────┴──────────────────────────────────────────────────┴───────────────────────┴───────────────────────────┴─────────┴──────────────┘
```

## ⚙️ Configuration

The scraper is highly configurable through JSON files in the `config/` directory:

- **`companies.json`**: Company URLs, search parameters, and CSS selectors
- **`job_types.json`**: Job categories, keywords, and filtering rules
- **`settings.json`**: Scraping behavior, rate limits, and output preferences

## 🔧 Architecture

```
src/
├── models.py              # Data models (Job, Company, etc.)
├── scraper_manager.py     # Main orchestration logic
├── scrapers/              # Scraper implementations
│   ├── base_scraper.py    # Abstract base class
│   ├── generic_scraper.py # Default scraper
│   ├── greenhouse_scraper.py # Greenhouse ATS
│   └── lever_scraper.py   # Lever ATS
└── utils/
    ├── job_matcher.py     # Job classification logic
    ├── rate_limiter.py    # Request rate limiting
    └── output_formatter.py # Results formatting
```

## 🤝 Contributing

Want to add a company or improve the scraper? 

1. Add company details to `config/companies.json`
2. Create specialized scrapers in `src/scrapers/` if needed
3. Test with `python run_scraper.py test-company CompanyName`
4. Submit a PR!

## ⚖️ Legal & Ethics

This tool is designed for educational and personal job search purposes. Please:
- Respect robots.txt and rate limits
- Don't overload company servers
- Use scraped data responsibly
- Follow each company's terms of service

## 📝 License

MIT License - see LICENSE file for details.

---

**Good luck with your job search! 🍀**