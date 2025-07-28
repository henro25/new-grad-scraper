import asyncio
import json
from typing import List, Dict, Type
from pathlib import Path

from src.models import CompanyConfig, CompanyTier, ScrapingResult
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.generic_scraper import GenericScraper
from src.scrapers.greenhouse_scraper import GreenhouseScraper
from src.scrapers.lever_scraper import LeverScraper
from src.scrapers.google_scraper import GoogleScraper
from src.utils.job_matcher import JobMatcher

class ScraperManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.companies = self._load_companies()
        self.job_types = self._load_job_types()
        self.settings = self._load_settings()
        self.job_matcher = JobMatcher(self.job_types)
        
        # Map company domains to specialized scrapers
        self.scraper_mapping = {
            'greenhouse.io': GreenhouseScraper,
            'jobs.lever.co': LeverScraper,
            'lever.co': LeverScraper,
            'careers.google.com': GoogleScraper,
            'google.com/about/careers': GoogleScraper,
            # Add more specialized scrapers as needed
        }
    
    def _load_companies(self) -> Dict:
        """Load company configurations"""
        companies_file = self.config_dir / "companies.json"
        with open(companies_file, 'r') as f:
            return json.load(f)
    
    def _load_job_types(self) -> Dict:
        """Load job type configurations"""
        job_types_file = self.config_dir / "job_types.json"
        with open(job_types_file, 'r') as f:
            return json.load(f)
    
    def _load_settings(self) -> Dict:
        """Load scraping settings"""
        settings_file = self.config_dir / "settings.json"
        with open(settings_file, 'r') as f:
            return json.load(f)
    
    def _get_scraper_class(self, careers_url: str) -> Type[BaseScraper]:
        """Determine which scraper class to use for a given URL"""
        for domain, scraper_class in self.scraper_mapping.items():
            if domain in careers_url:
                return scraper_class
        
        return GenericScraper  # Default fallback
    
    def _create_company_configs(self, tier_filter: List[str] = None) -> List[CompanyConfig]:
        """Create CompanyConfig objects from loaded data"""
        configs = []
        
        for tier_name, companies in self.companies.items():
            if tier_filter and tier_name not in tier_filter:
                continue
                
            tier = CompanyTier(tier_name)
            
            for company_name, company_data in companies.items():
                config = CompanyConfig(
                    name=company_name,
                    careers_url=company_data['careers_url'],
                    search_params=company_data.get('search_params', {}),
                    selectors=company_data.get('selectors', {}),
                    tier=tier
                )
                configs.append(config)
        
        return configs
    
    async def scrape_all_companies(self, 
                                 tier_filter: List[str] = None,
                                 company_filter: List[str] = None,
                                 max_concurrent: int = None) -> List[ScrapingResult]:
        """Scrape jobs from all configured companies"""
        
        configs = self._create_company_configs(tier_filter)
        
        # Filter by specific companies if requested
        if company_filter:
            configs = [c for c in configs if c.name in company_filter]
        
        # Limit concurrency
        if max_concurrent is None:
            max_concurrent = self.settings.get('scraping', {}).get('concurrent_requests', 5)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_single_company(config: CompanyConfig) -> ScrapingResult:
            async with semaphore:
                scraper_class = self._get_scraper_class(config.careers_url)
                
                async with scraper_class(config, self.settings, self.job_matcher) as scraper:
                    return await scraper.scrape_jobs()
        
        # Execute all scraping tasks
        tasks = [scrape_single_company(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, ScrapingResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                print(f"Scraping error: {result}")
        
        return valid_results
    
    async def scrape_company(self, company_name: str) -> ScrapingResult:
        """Scrape jobs from a specific company"""
        configs = self._create_company_configs()
        
        for config in configs:
            if config.name.lower() == company_name.lower():
                scraper_class = self._get_scraper_class(config.careers_url)
                
                async with scraper_class(config, self.settings, self.job_matcher) as scraper:
                    return await scraper.scrape_jobs()
        
        # Return empty result if company not found
        return ScrapingResult(
            company=company_name,
            jobs_found=[],
            errors=[f"Company '{company_name}' not found in configuration"],
            success=False
        )
    
    def get_available_companies(self) -> Dict[str, List[str]]:
        """Get list of all available companies organized by tier"""
        result = {}
        for tier_name, companies in self.companies.items():
            result[tier_name] = list(companies.keys())
        return result
    
    def get_available_tiers(self) -> List[str]:
        """Get list of all available company tiers"""
        return list(self.companies.keys())