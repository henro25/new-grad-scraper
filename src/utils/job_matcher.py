import re
from typing import List, Dict, Set, Tuple
from src.models import Job, JobCategory

class JobMatcher:
    def __init__(self, job_types_config: Dict):
        self.job_types_config = job_types_config
        self.target_roles = job_types_config['target_roles']
        self.exclude_keywords = set(kw.lower() for kw in job_types_config['exclude_keywords'])
    
    def match_job_category(self, title: str, description: str = "") -> Tuple[JobCategory, float]:
        """Determine job category and confidence score"""
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        # Check if we should exclude this job
        if self._should_exclude(title_lower, desc_lower):
            return None, 0.0
        
        best_category = None
        best_score = 0.0
        
        for category_name, config in self.target_roles.items():
            score = self._calculate_category_score(title_lower, desc_lower, config)
            if score > best_score:
                best_score = score
                best_category = JobCategory(category_name)
        
        return best_category, best_score
    
    def is_new_grad_position(self, title: str, description: str = "") -> Tuple[bool, float]:
        """Check if position is suitable for new graduates"""
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        # Check for new grad indicators
        new_grad_score = 0.0
        total_indicators = 0
        
        for category_config in self.target_roles.values():
            indicators = category_config['new_grad_indicators']
            for indicator in indicators:
                total_indicators += 1
                if indicator.lower() in title_lower or indicator.lower() in desc_lower:
                    new_grad_score += 1.0
        
        # Check for exclusionary keywords (senior, lead, etc.)
        exclusion_penalty = 0.0
        for exclude_kw in self.exclude_keywords:
            if exclude_kw in title_lower or exclude_kw in desc_lower:
                exclusion_penalty += 2.0  # Heavy penalty for senior roles
        
        final_score = max(0.0, (new_grad_score / total_indicators) - (exclusion_penalty / 10))
        return final_score > 0.1, final_score
    
    def _should_exclude(self, title: str, description: str) -> bool:
        """Check if job should be excluded based on exclusion keywords"""
        text = f"{title} {description}"
        
        # Strong exclusion patterns
        exclusion_patterns = [
            r'\b(senior|sr\.)\s+',
            r'\blead\s+',
            r'\bprincipal\s+',
            r'\bstaff\s+',
            r'\bmanager\b',
            r'\bdirector\b',
            r'\bhead\s+of\b',
            r'\bvp\b|\bvice\s+president\b',
            r'\bchief\b',
            r'\b\d+\+?\s+years?\b',
            r'\bexperienced\b',
            r'\bseasoned\b'
        ]
        
        for pattern in exclusion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_category_score(self, title: str, description: str, config: Dict) -> float:
        """Calculate how well a job matches a specific category"""
        text = f"{title} {description}"
        
        keyword_matches = 0
        total_keywords = len(config['keywords'])
        
        for keyword in config['keywords']:
            if keyword.lower() in text:
                keyword_matches += 1
        
        # Bonus for new grad indicators
        new_grad_bonus = 0.0
        for indicator in config['new_grad_indicators']:
            if indicator.lower() in text:
                new_grad_bonus += 0.1
        
        base_score = keyword_matches / total_keywords if total_keywords > 0 else 0.0
        return min(1.0, base_score + new_grad_bonus)
    
    def get_location_score(self, location: str, preferred_locations: List[str]) -> float:
        """Score location based on preferences"""
        if not location or not preferred_locations:
            return 0.5  # Neutral score
        
        location_lower = location.lower()
        
        for preferred in preferred_locations:
            if preferred.lower() in location_lower:
                return 1.0
        
        # Check for remote/hybrid
        if any(keyword in location_lower for keyword in ['remote', 'hybrid', 'work from home']):
            return 0.9
        
        return 0.3  # Lower score for non-preferred locations
    
    def is_us_location(self, location: str) -> bool:
        """Check if location is in the United States"""
        if not location or location.lower() in ['unknown location', 'unknown', 'n/a', '']:
            return False
        
        location_lower = location.lower()
        
        # US indicators
        us_keywords = [
            # States (abbreviated and full)
            'usa', 'united states', 'us', 'america',
            'california', 'ca', 'new york', 'ny', 'texas', 'tx', 'florida', 'fl',
            'washington', 'wa', 'oregon', 'or', 'colorado', 'co', 'illinois', 'il',
            'massachusetts', 'ma', 'virginia', 'va', 'north carolina', 'nc',
            'georgia', 'ga', 'ohio', 'oh', 'pennsylvania', 'pa', 'michigan', 'mi',
            'arizona', 'az', 'nevada', 'nv', 'utah', 'ut', 'connecticut', 'ct',
            'new jersey', 'nj', 'maryland', 'md', 'tennessee', 'tn',
            
            # Major cities
            'san francisco', 'los angeles', 'seattle', 'chicago', 'boston',
            'new york city', 'nyc', 'austin', 'denver', 'atlanta', 'miami',
            'san diego', 'phoenix', 'philadelphia', 'dallas', 'houston',
            'portland', 'minneapolis', 'detroit', 'las vegas', 'nashville',
            'raleigh', 'durham', 'richmond', 'arlington', 'alexandria',
            'palo alto', 'mountain view', 'menlo park', 'santa clara',
            'cupertino', 'sunnyvale', 'fremont', 'redmond', 'bellevue',
            
            # Remote work indicators
            'remote', 'remote - us', 'remote (us)', 'work from home', 'wfh',
            'remote - usa', 'remote usa', 'telecommute', 'distributed'
        ]
        
        # Non-US indicators (exclude these)
        non_us_keywords = [
            'canada', 'toronto', 'vancouver', 'montreal', 'ottawa',
            'london', 'uk', 'united kingdom', 'england', 'scotland',
            'ireland', 'dublin', 'germany', 'berlin', 'munich',
            'france', 'paris', 'netherlands', 'amsterdam', 'sweden',
            'stockholm', 'norway', 'oslo', 'denmark', 'copenhagen',
            'australia', 'sydney', 'melbourne', 'singapore', 'japan',
            'tokyo', 'china', 'beijing', 'shanghai', 'india', 'bangalore',
            'mumbai', 'hyderabad', 'israel', 'tel aviv', 'brazil',
            'mexico', 'argentina', 'poland', 'warsaw', 'czech republic',
            'prague', 'ukraine', 'kyiv', 'romania', 'bucharest'
        ]
        
        # Check for non-US locations first (exclude)
        for keyword in non_us_keywords:
            if keyword in location_lower:
                return False
        
        # Check for US locations
        for keyword in us_keywords:
            if keyword in location_lower:
                return True
        
        # If no clear indicators, default to False (non-US)
        return False