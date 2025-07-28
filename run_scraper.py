#!/usr/bin/env python3
"""
Simple runner script for the new grad job scraper
Usage: python run_scraper.py
"""

import sys
import subprocess

def main():
    """Run the scraper CLI"""
    try:
        # Run the main CLI
        subprocess.run([sys.executable, '-m', 'src.main'] + sys.argv[1:], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(0)

if __name__ == '__main__':
    main()