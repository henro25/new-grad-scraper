from typing import List
from urllib.parse import urlparse
from src.models import Job
from src.scrapers.base_scraper import BaseScraper

class GenericScraper(BaseScraper):
    """Generic scraper that works for most standard job board layouts"""
    
    async def _scrape_implementation(self) -> List[Job]:
        jobs = []
        
        # Try to fetch the careers page
        soup = await self.fetch_page(self.config.careers_url, self.config.search_params)
        if not soup:
            return jobs
        
        base_url = f"{urlparse(self.config.careers_url).scheme}://{urlparse(self.config.careers_url).netloc}"
        
        # Find job listings using configured selectors
        job_elements = soup.select(self.config.selectors.get('job_links', 'a'))
        
        for element in job_elements[:20]:  # Limit to first 20 results
            # For generic scraper, we need to find the parent container
            job_container = element.parent
            while job_container and job_container.name != 'body':
                if (job_container.select_one(self.config.selectors.get('job_title', 'h3')) and
                    job_container.select_one(self.config.selectors.get('location', 'span'))):
                    break
                job_container = job_container.parent
            
            if job_container:
                job = self.extract_job_from_element(job_container, base_url)
                if job and job.title and job.url:
                    jobs.append(job)
        
        return jobs