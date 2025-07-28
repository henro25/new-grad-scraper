#!/usr/bin/env python3
"""
New Grad Job Scraper - CLI Tool

A comprehensive job scraper for new graduate positions at top tech companies.
Searches for software engineering, ML, data science, and quantitative research roles.
"""

import asyncio
import click
from pathlib import Path
from colorama import Fore, Style, init

from src.scraper_manager import ScraperManager
from src.utils.output_formatter import OutputFormatter

# Initialize colorama
init()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🎯 New Grad Job Scraper - Find your dream tech job!"""
    pass

@cli.command()
@click.option('--tiers', '-t', multiple=True, 
              help='Filter by company tiers. Space-separated: --tiers big_tech trading_and_finance')
@click.option('--companies', '-c', multiple=True,
              help='Filter by specific companies. Space-separated: --companies Google Apple Netflix')
@click.option('--output-format', '-f', type=click.Choice(['table', 'json', 'csv', 'all']), 
              default='table', help='Output format')
@click.option('--save', '-s', is_flag=True, default=False,
              help='Save results to file (auto-determined by output format)')
@click.option('--max-concurrent', '-j', type=int, default=5,
              help='Maximum concurrent scraping requests')
@click.option('--config-dir', default='config', 
              help='Configuration directory path')
def scrape(tiers, companies, output_format, save, max_concurrent, config_dir):
    """🚀 Scrape new grad jobs from configured companies"""
    
    # Validate config directory
    config_path = Path(config_dir)
    if not config_path.exists():
        click.echo(f"{Fore.RED}❌ Configuration directory '{config_dir}' not found!{Style.RESET_ALL}")
        click.echo(f"Make sure you have the config files in: {config_path.absolute()}")
        return
    
    click.echo(f"{Fore.CYAN}🎯 Starting new grad job search...{Style.RESET_ALL}")
    
    # Run the scraping
    asyncio.run(run_scraper(
        tiers=list(tiers) if tiers else None,
        companies=list(companies) if companies else None,
        output_format=output_format,
        save_results=save,
        max_concurrent=max_concurrent,
        config_dir=config_dir
    ))

@cli.command()
@click.option('--config-dir', default='config', help='Configuration directory path')
def list_companies(config_dir):
    """📋 List all available companies organized by tier"""
    try:
        manager = ScraperManager(config_dir)
        companies_by_tier = manager.get_available_companies()
        
        click.echo(f"\n{Fore.CYAN}🏢 Available Companies by Tier:{Style.RESET_ALL}")
        
        for tier, companies in companies_by_tier.items():
            tier_display = tier.replace('_', ' ').title()
            click.echo(f"\n{Fore.YELLOW}{tier_display}:{Style.RESET_ALL}")
            
            for company in sorted(companies):
                click.echo(f"  • {company}")
        
        click.echo(f"\n{Fore.GREEN}💡 Use --tiers or --companies flags to filter your search{Style.RESET_ALL}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error loading companies: {e}{Style.RESET_ALL}")

@cli.command()
@click.argument('company_name')
@click.option('--config-dir', default='config', help='Configuration directory path')
def test_company(company_name, config_dir):
    """🧪 Test scraping a single company"""
    click.echo(f"{Fore.CYAN}🧪 Testing scraper for: {company_name}{Style.RESET_ALL}")
    
    asyncio.run(test_single_company(company_name, config_dir))

async def run_scraper(tiers, companies, output_format, save_results, max_concurrent, config_dir):
    """Main scraping logic"""
    try:
        # Initialize manager and formatter
        manager = ScraperManager(config_dir)
        formatter = OutputFormatter(manager.settings.get('output', {}))
        
        # Show what we're scraping
        if tiers:
            click.echo(f"🎯 Targeting tiers: {', '.join(tiers)}")
        if companies:
            click.echo(f"🏢 Targeting companies: {', '.join(companies)}")
        
        click.echo(f"⚡ Using {max_concurrent} concurrent requests")
        click.echo(f"{Fore.YELLOW}⏳ Scraping in progress...{Style.RESET_ALL}")
        
        # Run the scraping
        results = await manager.scrape_all_companies(
            tier_filter=tiers,
            company_filter=companies,
            max_concurrent=max_concurrent
        )
        
        # Output results
        if output_format in ['table', 'all']:
            formatter.print_table(results)
        
        # Save results if requested
        if save_results or output_format in ['json', 'csv', 'all']:
            if output_format in ['json', 'all']:
                json_file = formatter.save_to_json(results)
                click.echo(f"{Fore.GREEN}💾 Results saved to: {json_file}{Style.RESET_ALL}")
            
            if output_format in ['csv', 'all']:
                csv_file = formatter.save_to_csv(results)
                click.echo(f"{Fore.GREEN}💾 Results saved to: {csv_file}{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}⏹️  Scraping interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error during scraping: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

async def test_single_company(company_name, config_dir):
    """Test scraping a single company"""
    try:
        manager = ScraperManager(config_dir)
        formatter = OutputFormatter(manager.settings.get('output', {}))
        
        result = await manager.scrape_company(company_name)
        
        if result.success:
            click.echo(f"{Fore.GREEN}✅ Successfully scraped {company_name}{Style.RESET_ALL}")
            click.echo(f"📊 Found {len(result.jobs_found)} potential positions")
            click.echo(f"⏱️  Scraping took {result.scraping_time:.2f} seconds")
            
            if result.jobs_found:
                formatter.print_table([result])
        else:
            click.echo(f"{Fore.RED}❌ Failed to scrape {company_name}{Style.RESET_ALL}")
            for error in result.errors:
                click.echo(f"  • {error}")
    
    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error testing {company_name}: {e}{Style.RESET_ALL}")

if __name__ == '__main__':
    cli()