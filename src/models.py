from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class JobCategory(Enum):
    SOFTWARE_ENGINEERING = "software_engineering"
    MACHINE_LEARNING = "machine_learning"
    QUANTITATIVE_RESEARCH = "quantitative_research"
    DATA_SCIENCE = "data_science"

class CompanyTier(Enum):
    BIG_TECH = "big_tech"
    DATA_AND_AI = "data_and_ai"
    MOBILITY_AND_TRANSPORT = "mobility_and_transport"
    SOCIAL_AND_PROFESSIONAL = "social_and_professional"
    TRADING_AND_FINANCE = "trading_and_finance"
    FINTECH_AND_CRYPTO = "fintech_and_crypto"
    HARDWARE_AND_INFRASTRUCTURE = "hardware_and_infrastructure"
    ENTERPRISE_AND_CLOUD = "enterprise_and_cloud"

@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    category: JobCategory
    company_tier: CompanyTier
    description: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    salary_range: Optional[str] = None
    is_remote: bool = False
    is_hybrid: bool = False
    match_score: float = 0.0
    found_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'category': self.category.value,
            'company_tier': self.company_tier.value,
            'description': self.description,
            'requirements': self.requirements,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'salary_range': self.salary_range,
            'is_remote': self.is_remote,
            'is_hybrid': self.is_hybrid,
            'match_score': self.match_score,
            'found_at': self.found_at.isoformat()
        }

@dataclass
class CompanyConfig:
    name: str
    careers_url: str
    search_params: Dict[str, str]
    selectors: Dict[str, str]
    tier: CompanyTier
    
@dataclass
class ScrapingResult:
    company: str
    jobs_found: List[Job]
    errors: List[str] = field(default_factory=list)
    scraping_time: float = 0.0
    success: bool = True