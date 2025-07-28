from typing import List
from urllib.parse import urljoin
from src.models import Job
from src.scrapers.base_scraper import BaseScraper

class GreenhouseScraper(BaseScraper):
    """Specialized scraper for Greenhouse-powered career pages"""
    
    async def _scrape_implementation(self) -> List[Job]:
        jobs = []
        
        # Greenhouse typically has a consistent API structure
        soup = await self.fetch_page(self.config.careers_url)
        if not soup:
            return jobs
        
        # Greenhouse usually structures jobs in a specific way
        job_sections = soup.select('div.opening')
        
        for section in job_sections:
            try:
                # Extract title
                title_elem = section.select_one('a.opening-title')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                job_url = urljoin(self.config.careers_url, title_elem.get('href', ''))
                
                # Extract location
                location_elem = section.select_one('.location')
                location = location_elem.get_text(strip=True) if location_elem else "Not specified"
                
                # Extract department/team
                dept_elem = section.select_one('.department')
                department = dept_elem.get_text(strip=True) if dept_elem else ""
                
                # Check if it's relevant (software engineering related)
                if self._is_relevant_job(title, department):
                    job = Job(
                        title=title,
                        company=self.config.name,
                        location=location,
                        url=job_url,
                        category=None,  # Will be set by matcher
                        company_tier=self.config.tier,
                        description=department
                    )
                    jobs.append(job)
            
            except Exception as e:
                continue
        
        return jobs
    
    def _is_relevant_job(self, title: str, department: str) -> bool:
        """Check if job is relevant for new grad tech positions"""
        relevant_keywords = [
            'software', 'engineer', 'developer', 'data', 'machine learning',
            'ml', 'ai', 'artificial intelligence', 'backend', 'frontend',
            'full stack', 'mobile', 'ios', 'android', 'web', 'systems',
            'platform', 'infrastructure', 'devops', 'sre', 'site reliability',
            'quantitative', 'quant', 'research', 'scientist'
        ]
        
        text = f"{title} {department}".lower()
        return any(keyword in text for keyword in relevant_keywords)