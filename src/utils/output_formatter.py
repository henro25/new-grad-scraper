import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from tabulate import tabulate
from colorama import Fore, Style, init

from src.models import Job, ScrapingResult, JobCategory, CompanyTier

# Initialize colorama for cross-platform colored output
init()

class OutputFormatter:
    def __init__(self, output_config: Dict):
        self.config = output_config
        self.output_dir = Path(output_config.get('output_directory', 'data'))
        self.output_dir.mkdir(exist_ok=True)
    
    def format_results(self, results: List[ScrapingResult]) -> Dict[str, Any]:
        """Format scraping results for output"""
        all_jobs = []
        summary_stats = {
            'total_companies_scraped': len(results),
            'successful_scrapes': sum(1 for r in results if r.success),
            'total_jobs_found': 0,
            'jobs_by_category': {},
            'jobs_by_tier': {},
            'jobs_by_company': {},
            'average_match_score': 0.0,
            'scraping_errors': []
        }
        
        for result in results:
            if result.success:
                all_jobs.extend(result.jobs_found)
                summary_stats['jobs_by_company'][result.company] = len(result.jobs_found)
            else:
                summary_stats['scraping_errors'].extend([
                    f"{result.company}: {error}" for error in result.errors
                ])
        
        summary_stats['total_jobs_found'] = len(all_jobs)
        
        # Calculate category distribution
        for job in all_jobs:
            category = job.category.value if job.category else 'unknown'
            tier = job.company_tier.value if job.company_tier else 'unknown'
            
            summary_stats['jobs_by_category'][category] = summary_stats['jobs_by_category'].get(category, 0) + 1
            summary_stats['jobs_by_tier'][tier] = summary_stats['jobs_by_tier'].get(tier, 0) + 1
        
        # Calculate average match score
        if all_jobs:
            summary_stats['average_match_score'] = sum(job.match_score for job in all_jobs) / len(all_jobs)
        
        return {
            'jobs': all_jobs,
            'summary': summary_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    def print_table(self, results: List[ScrapingResult]) -> None:
        """Print results in a nice table format"""
        formatted_data = self.format_results(results)
        jobs = formatted_data['jobs']
        summary = formatted_data['summary']
        
        if not jobs:
            print(f"{Fore.YELLOW}No jobs found matching criteria.{Style.RESET_ALL}")
            return
        
        # Sort jobs by match score (highest first)
        jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        # Prepare table data
        table_data = []
        for job in jobs:
            # Truncate long titles/companies for better display
            title = job.title[:50] + "..." if len(job.title) > 50 else job.title
            company = job.company[:20] + "..." if len(job.company) > 20 else job.company
            location = job.location[:25] + "..." if len(job.location) > 25 else job.location
            
            # Color code by category
            category_color = self._get_category_color(job.category)
            category_display = f"{category_color}{job.category.value if job.category else 'unknown'}{Style.RESET_ALL}"
            
            table_data.append([
                company,
                title,
                category_display,
                location,
                f"{job.match_score:.2f}",
                job.company_tier.value if job.company_tier else 'unknown'
            ])
        
        # Print summary
        print(f"\n{Fore.CYAN}=== JOB SEARCH RESULTS ==={Style.RESET_ALL}")
        print(f"📊 Found {Fore.GREEN}{summary['total_jobs_found']}{Style.RESET_ALL} new grad positions from {summary['successful_scrapes']}/{summary['total_companies_scraped']} companies")
        print(f"⭐ Average match score: {Fore.YELLOW}{summary['average_match_score']:.2f}{Style.RESET_ALL}")
        
        # Print category breakdown
        print(f"\n{Fore.CYAN}📋 Jobs by Category:{Style.RESET_ALL}")
        for category, count in summary['jobs_by_category'].items():
            color = self._get_category_color(JobCategory(category) if category != 'unknown' else None)
            print(f"  {color}{category.replace('_', ' ').title()}: {count}{Style.RESET_ALL}")
        
        # Print table
        print(f"\n{Fore.CYAN}🎯 Top Matches:{Style.RESET_ALL}")
        headers = ["Company", "Position", "Category", "Location", "Score", "Tier"]
        print(tabulate(table_data[:30], headers=headers, tablefmt="grid"))  # Show top 30
        
        if len(jobs) > 30:
            print(f"\n{Fore.YELLOW}... and {len(jobs) - 30} more positions{Style.RESET_ALL}")
        
        # Print errors if any
        if summary['scraping_errors']:
            print(f"\n{Fore.RED}⚠️  Scraping Errors:{Style.RESET_ALL}")
            for error in summary['scraping_errors'][:5]:  # Show first 5 errors
                print(f"  {Fore.RED}• {error}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✨ Happy job hunting!{Style.RESET_ALL}")
    
    def save_to_json(self, results: List[ScrapingResult], filename: str = None) -> str:
        """Save results to JSON file"""
        formatted_data = self.format_results(results)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.get('filename_prefix', 'jobs_')}{timestamp}.json"
        
        file_path = self.output_dir / filename
        
        # Convert jobs to dictionaries for JSON serialization
        json_data = {
            'jobs': [job.to_dict() for job in formatted_data['jobs']],
            'summary': formatted_data['summary'],
            'generated_at': formatted_data['generated_at']
        }
        
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        return str(file_path)
    
    def save_to_csv(self, results: List[ScrapingResult], filename: str = None) -> str:
        """Save results to CSV file"""
        formatted_data = self.format_results(results)
        jobs = formatted_data['jobs']
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.get('filename_prefix', 'jobs_')}{timestamp}.csv"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Company', 'Title', 'Category', 'Location', 'URL', 
                'Company Tier', 'Match Score', 'Found At'
            ])
            
            # Write job data
            for job in jobs:
                writer.writerow([
                    job.company,
                    job.title,
                    job.category.value if job.category else 'unknown',
                    job.location,
                    job.url,
                    job.company_tier.value if job.company_tier else 'unknown',
                    f"{job.match_score:.3f}",
                    job.found_at.strftime("%Y-%m-%d %H:%M:%S")
                ])
        
        return str(file_path)
    
    def _get_category_color(self, category: JobCategory) -> str:
        """Get color for job category"""
        color_map = {
            JobCategory.SOFTWARE_ENGINEERING: Fore.BLUE,
            JobCategory.MACHINE_LEARNING: Fore.MAGENTA,
            JobCategory.QUANTITATIVE_RESEARCH: Fore.GREEN,
            JobCategory.DATA_SCIENCE: Fore.CYAN,
        }
        return color_map.get(category, Fore.WHITE)