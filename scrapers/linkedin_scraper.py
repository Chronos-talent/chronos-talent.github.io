import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
from database import SessionLocal, Job

class LinkedInScraper:
    def __init__(self):
        self.session = SessionLocal()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_jobs(self):
        """Search for tech sales jobs"""
        jobs_found = 0
        
        sample_titles = [
            'Sales Development Representative',
            'SDR',
            'Account Executive',
            'AE',
            'Business Development Representative',
            'BDR',
            'Tech Sales',
            'SaaS Sales'
        ]
        
        for title in sample_titles:
            print(f"🔍 Searching for: {title}")
            
            try:
                sample_job = {
                    'title': title,
                    'company': 'Sample Tech Company',
                    'location': 'Remote',
                    'job_url': f'https://linkedin.com/jobs/view/{title}-{int(time.time())}',
                    'source': 'LinkedIn',
                    'posted_date': datetime.now(),
                }
                
                self.save_job(sample_job)
                jobs_found += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return jobs_found
    
    def save_job(self, job_data):
        """Save job to database"""
        try:
            existing = self.session.query(Job).filter_by(job_url=job_data['job_url']).first()
            
            if not existing:
                job = Job(**job_data)
                self.session.add(job)
                self.session.commit()
                print(f"   ✅ Saved: {job_data['title']} at {job_data['company']}")
            else:
                print(f"   ⏩ Already exists: {job_data['title']}")
                
        except Exception as e:
            print(f"   ❌ Error saving: {e}")
            self.session.rollback()
    
    def close(self):
        self.session.close()