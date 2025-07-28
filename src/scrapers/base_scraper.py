import asyncio
import aiohttp
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, urljoin, urlencode
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.models import Job, CompanyConfig, ScrapingResult, CompanyTier
from src.utils.rate_limiter import RateLimiter
from src.utils.job_matcher import JobMatcher

class BaseScraper(ABC):
    def __init__(self, config: CompanyConfig, settings: Dict, job_matcher: JobMatcher):
        self.config = config
        self.settings = settings
        self.job_matcher = job_matcher
        self.rate_limiter = RateLimiter(settings.get('scraping', {}).get('rate_limit_delay', 2.0))
        self.session: Optional[aiohttp.ClientSession] = None
        self.driver: Optional[webdriver.Chrome] = None
        
    async def __aenter__(self):
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def setup(self):
        """Setup HTTP session and/or browser driver"""
        connector = aiohttp.TCPConnector(
            limit=10, 
            limit_per_host=3,  # Reduce concurrent connections per host
            verify_ssl=False,  # Disable SSL verification for problematic sites
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=self.settings.get('scraping', {}).get('request_timeout', 30))
        
        headers = {
            'User-Agent': self.settings.get('scraping', {}).get('user_agent', 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Remove brotli to avoid compression issues
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    def setup_selenium(self) -> webdriver.Chrome:
        """Setup Selenium Chrome driver if needed"""
        if self.driver:
            return self.driver
            
        chrome_options = Options()
        selenium_config = self.settings.get('selenium', {})
        
        if selenium_config.get('headless', True):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        
        window_size = selenium_config.get('window_size', [1920, 1080])
        chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        user_agent = self.settings.get('scraping', {}).get('user_agent')
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(selenium_config.get('implicit_wait', 10))
        
        return self.driver
    
    async def scrape_jobs(self) -> ScrapingResult:
        """Main scraping method - returns ScrapingResult"""
        start_time = time.time()
        result = ScrapingResult(company=self.config.name, jobs_found=[])
        
        try:
            domain = urlparse(self.config.careers_url).netloc
            await self.rate_limiter.wait_if_needed(domain)
            
            jobs = await self._scrape_implementation()
            
            # Filter and score jobs
            filtered_jobs = []
            for job in jobs:
                # Filter by US location first
                if not self.job_matcher.is_us_location(job.location):
                    continue
                
                category, category_score = self.job_matcher.match_job_category(
                    job.title, job.description or ""
                )
                
                if category and category_score > 0.3:  # Minimum threshold
                    is_new_grad, new_grad_score = self.job_matcher.is_new_grad_position(
                        job.title, job.description or ""
                    )
                    
                    if is_new_grad:
                        job.category = category
                        job.company_tier = self.config.tier
                        job.match_score = (category_score + new_grad_score) / 2
                        filtered_jobs.append(job)
            
            result.jobs_found = filtered_jobs
            self.rate_limiter.add_request(domain)
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Scraping failed: {str(e)}")
        
        result.scraping_time = time.time() - start_time
        return result
    
    @abstractmethod
    async def _scrape_implementation(self) -> List[Job]:
        """Company-specific scraping implementation"""
        pass
    
    async def fetch_page(self, url: str, params: Optional[Dict] = None, use_selenium: bool = False) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        if use_selenium:
            return await self.fetch_page_selenium(url, params)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                else:
                    return None
        except Exception as e:
            error_msg = str(e).lower()
            # Check for header value too long or brotli issues - fallback to Selenium
            if 'header value is too long' in error_msg or 'brotli' in error_msg:
                print(f"HTTP error for {url}, falling back to Selenium: {e}")
                return await self.fetch_page_selenium(url, params)
            print(f"Error fetching {url}: {response.status if 'response' in locals() else e}, message='{e}', url='{url}{f'?{urlencode(params)}' if params else ''}'")
            return None
    
    async def fetch_page_selenium(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page using Selenium for JavaScript-heavy sites"""
        try:
            if not self.driver:
                self.setup_selenium()
            
            # Construct URL with parameters
            if params:
                from urllib.parse import urlencode
                url = f"{url}?{urlencode(params)}"
            
            self.driver.get(url)
            
            # Wait for content to load
            wait = WebDriverWait(self.driver, 15)
            try:
                # Wait for body to load first
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Try to wait for job-related content
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Software') or contains(text(), 'Engineer')]")))
                except TimeoutException:
                    pass
                
                # Additional wait for dynamic content and JavaScript execution
                await asyncio.sleep(5)
                
                # Scroll down to trigger lazy loading if any
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
                
            except TimeoutException:
                pass
            
            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            print(f"Error fetching {url} with Selenium: {e}")
            return None
    
    def extract_job_from_element(self, element, base_url: str = None) -> Optional[Job]:
        """Extract job information from a DOM element"""
        try:
            selectors = self.config.selectors
            
            # Extract title
            title_elem = element.select_one(selectors.get('job_title', 'h3'))
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract URL
            link_elem = element.select_one(selectors.get('job_links', 'a'))
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/') and base_url:
                    url = urljoin(base_url, href)
                elif href.startswith('http'):
                    url = href
                else:
                    url = f"{base_url}/{href}" if base_url else ""
            else:
                url = ""
            
            # Extract location
            location_elem = element.select_one(selectors.get('location', 'span'))
            location = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Create job object
            job = Job(
                title=title,
                company=self.config.name,
                location=location,
                url=url,
                category=None,  # Will be set by matcher
                company_tier=self.config.tier
            )
            
            return job
            
        except Exception as e:
            print(f"Error extracting job from element: {e}")
            return None