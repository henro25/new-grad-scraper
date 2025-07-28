from typing import List
from urllib.parse import urlparse
from src.models import Job
from src.scrapers.base_scraper import BaseScraper

class GoogleScraper(BaseScraper):
    """Specialized scraper for Google Careers (requires Selenium for JS content)"""
    
    async def _scrape_implementation(self) -> List[Job]:
        jobs = []
        
        # Google careers requires Selenium due to dynamic content
        soup = await self.fetch_page(
            self.config.careers_url, 
            self.config.search_params, 
            use_selenium=True
        )
        
        if not soup:
            return jobs
        
        base_url = f"{urlparse(self.config.careers_url).scheme}://{urlparse(self.config.careers_url).netloc}"
        
        # Look for job cards with various selectors that Google might use
        potential_selectors = [
            'div',                             # Generic divs (most likely to contain job titles)
            '[data-track-name="job-click"]',   # Original selector (any element)
            'a[data-track-name="job-click"]',  # Link specific
            '.job-tile',                       # Job tile containers
            '.job-card',                       # Job card containers
            '[data-job-id]',                   # Job ID based elements
            '.job-listing',                    # Job listing containers
            '[role="listitem"]',               # List items that might contain jobs
            'div[jsname]',                     # Google's internal divs
            'a[href*="/job"]',                 # Any links with job in URL
        ]
        
        job_elements = []
        for selector in potential_selectors:
            elements = soup.select(selector)
            # Filter out pagination and navigation links
            filtered_elements = []
            for elem in elements:
                href = elem.get('href', '') if elem.name == 'a' else ''
                text = elem.get_text(strip=True).lower()
                
                # Skip pagination and non-job links
                if ('page=' in href or 
                    'nav' in text or 
                    'next' in text or 
                    'previous' in text or
                    'send feedback' in text or
                    'copy link' in text or
                    'email a friend' in text or
                    len(text) < 20):  # Too short to be a job title
                    continue
                
                # Only include elements that look like job titles (not requirements)
                is_job_title = False
                
                # Check if this looks like a job title
                if any(keyword in text for keyword in [
                    'software engineer', 'data scientist', 'research scientist',
                    'product manager', 'technical program manager'
                ]):
                    # Make sure it's not a requirement or qualification
                    if not any(req_keyword in text for req_keyword in [
                        'bachelor\'s degree', 'phd degree', 'master\'s degree',
                        'years of experience', 'equivalent practical experience',
                        'experience in', 'experience with', 'knowledge of'
                    ]):
                        # Check if it contains company/location indicators (job titles often do)
                        if any(indicator in text for indicator in [
                            'google', 'university', 'graduate', 'phd', 'campus',
                            'new york', 'california', 'mountain view', 'usa'
                        ]):
                            is_job_title = True
                
                if is_job_title:
                    filtered_elements.append(elem)
            
            if filtered_elements:
                job_elements = filtered_elements
                break
        
        for element in job_elements[:20]:  # Limit to first 20 results
            try:
                # For Google, job information might be in the same element or parent
                job_container = element
                
                # Try to find parent container if needed
                if not (job_container.select_one(self.config.selectors.get('job_title', 'h3')) or
                        job_container.get_text(strip=True)):
                    job_container = element.parent
                    while job_container and job_container.name != 'body':
                        if job_container.select_one(self.config.selectors.get('job_title', 'h3')):
                            break
                        job_container = job_container.parent
                
                if job_container:
                    job = self.extract_job_from_element(job_container, base_url)
                    if job and job.title and job.url:
                        jobs.append(job)
                        
            except Exception as e:
                continue
        
        return jobs
    
    def extract_job_from_element(self, element, base_url: str = None):
        """Override to handle Google's specific job structure"""
        try:
            # For Google, try multiple approaches to extract job info
            
            # Try to find the job link first
            job_link = None
            job_url = ""
            
            if element.name == 'a':
                job_link = element
                job_url = element.get('href', '')
            else:
                # Look for a link within the element or nearby elements
                job_link = element.select_one('a[href*="/jobs/"]')
                if not job_link:
                    # Try parent elements
                    parent = element.parent
                    while parent and parent.name != 'body':
                        job_link = parent.select_one('a[href*="/jobs/"]')
                        if job_link:
                            break
                        parent = parent.parent
                
                # If still no link found, look for sibling elements
                if not job_link and element.parent:
                    siblings = element.parent.find_all(['a', 'div', 'li'])
                    for sibling in siblings:
                        if sibling.name == 'a' and '/jobs/' in sibling.get('href', ''):
                            job_link = sibling
                            break
                        elif sibling != element:
                            nested_link = sibling.select_one('a[href*="/jobs/"]')
                            if nested_link:
                                job_link = nested_link
                                break
                
                if job_link:
                    job_url = job_link.get('href', '')
            
            # Extract title - try multiple selectors
            title = None
            for title_selector in [
                self.config.selectors.get('job_title', 'h3'),
                'h3', 'h2', 'h4',
                '[data-automation="title"]',
                '.job-title',
                'a[data-track-name="job-click"]'
            ]:
                title_elem = element.select_one(title_selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # If no title found, use the element's text
            if not title:
                title = element.get_text(strip=True)
            
            # Extract location - try multiple selectors  
            location = "Unknown Location"
            for loc_selector in [
                self.config.selectors.get('location', '[data-automation="location"]'),
                '[data-automation="location"]',
                '.job-location',
                '.location'
            ]:
                loc_elem = element.select_one(loc_selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Clean up the URL
            if job_url:
                if job_url.startswith('./'):
                    job_url = base_url + '/' + job_url[2:]
                elif job_url.startswith('/'):
                    job_url = base_url + job_url
                elif not job_url.startswith('http'):
                    job_url = base_url + '/' + job_url
            else:
                # If no direct job URL found, create a search URL as fallback
                if title and len(title) > 10:
                    import urllib.parse
                    search_title = title[:50]  # Truncate for URL
                    job_url = f"{base_url}/jobs/results/?q={urllib.parse.quote(search_title)}"
            
            # Only create job if we have meaningful title and URL  
            if title and len(title) > 10 and job_url:
                from src.models import Job, JobCategory, CompanyTier
                return Job(
                    title=title,
                    company=self.config.name,
                    location=location,
                    url=job_url,
                    category=JobCategory.SOFTWARE_ENGINEERING,  # Will be updated by job matcher
                    company_tier=self.config.tier
                )
            
            return None
            
        except Exception as e:
            print(f"Error extracting job from element: {e}")
            return None