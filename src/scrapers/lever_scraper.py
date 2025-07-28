from typing import List
from urllib.parse import urljoin
from src.models import Job
from src.scrapers.base_scraper import BaseScraper

class LeverScraper(BaseScraper):
    """Specialized scraper for Lever-powered career pages"""
    
    async def _scrape_implementation(self) -> List[Job]:
        jobs = []
        
        soup = await self.fetch_page(self.config.careers_url)
        if not soup:
            return jobs
        
        # Lever typically uses posting-* classes
        job_postings = soup.select('.posting')
        
        for posting in job_postings:
            try:
                # Extract title and URL
                title_elem = posting.select_one('.posting-title h5')
                if not title_elem:
                    title_elem = posting.select_one('h5')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Get URL from parent link
                link_elem = posting.select_one('a.posting-title')
                if not link_elem:
                    link_elem = posting.select_one('a')
                
                job_url = ""
                if link_elem:
                    href = link_elem.get('href', '')
                    if href.startswith('/'):
                        job_url = urljoin('https://jobs.lever.co/', href)
                    else:
                        job_url = href
                
                # Extract location and team
                categories = posting.select('.posting-categories .sort-by-location, .sort-by-team')
                location = "Not specified"
                team = ""
                
                for cat in categories:
                    text = cat.get_text(strip=True)
                    if any(loc_word in text.lower() for loc_word in ['office', 'remote', 'hybrid', 'san francisco', 'new york', 'seattle', 'austin']):
                        location = text
                    else:
                        team = text
                
                # Check relevance
                if self._is_relevant_job(title, team):
                    job = Job(
                        title=title,
                        company=self.config.name,
                        location=location,
                        url=job_url,
                        category=None,
                        company_tier=self.config.tier,
                        description=team
                    )
                    jobs.append(job)
            
            except Exception as e:
                continue
        
        return jobs
    
    def _is_relevant_job(self, title: str, team: str) -> bool:
        """Check if job is relevant for new grad tech positions"""
        relevant_keywords = [
            'software', 'engineer', 'developer', 'data', 'machine learning',
            'ml', 'ai', 'artificial intelligence', 'backend', 'frontend',
            'full stack', 'mobile', 'ios', 'android', 'web', 'systems',
            'platform', 'infrastructure', 'devops', 'sre', 'site reliability',
            'quantitative', 'quant', 'research', 'scientist', 'technology',
            'engineering', 'technical'
        ]
        
        text = f"{title} {team}".lower()
        return any(keyword in text for keyword in relevant_keywords)