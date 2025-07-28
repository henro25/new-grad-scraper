import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, default_delay: float = 1.0):
        self.default_delay = default_delay
        self.last_request_time: Dict[str, float] = {}
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        
    async def wait_if_needed(self, domain: str, custom_delay: Optional[float] = None) -> None:
        """Wait if necessary to respect rate limits"""
        delay = custom_delay or self.default_delay
        
        if domain in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[domain]
            if time_since_last < delay:
                wait_time = delay - time_since_last
                await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
    
    def add_request(self, domain: str) -> None:
        """Record a request for rate limiting tracking"""
        current_time = time.time()
        self.request_counts[domain].append(current_time)
        
        # Clean old requests (older than 1 hour)
        while (self.request_counts[domain] and 
               current_time - self.request_counts[domain][0] > 3600):
            self.request_counts[domain].popleft()
    
    def get_request_count(self, domain: str, time_window: float = 3600) -> int:
        """Get number of requests in the last time_window seconds"""
        current_time = time.time()
        count = 0
        
        for request_time in reversed(self.request_counts[domain]):
            if current_time - request_time <= time_window:
                count += 1
            else:
                break
        
        return count
    
    def should_backoff(self, domain: str) -> bool:
        """Check if we should back off due to high request rate"""
        recent_requests = self.get_request_count(domain, 300)  # 5 minutes
        return recent_requests > 50  # More than 50 requests in 5 minutes