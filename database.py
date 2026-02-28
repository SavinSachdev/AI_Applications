"""
Database module for storing and managing job search results and resumes.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pandas as pd

Base = declarative_base()


class Job(Base):
    """Job model for storing job listings."""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_url = Column(String, unique=True, nullable=False, index=True)
    site = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, index=True)
    location = Column(String)
    description = Column(Text)
    date_posted = Column(DateTime)
    job_type = Column(String)
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String)
    
    # Application tracking fields
    applied = Column(Boolean, default=False, nullable=False, index=True)
    applied_date = Column(DateTime)
    notes = Column(Text)
    
    # Resume tailoring fields
    tailored_resume = Column(Text)
    ats_score = Column(Float)
    ats_keyword_match = Column(Float)
    ats_skills_match = Column(Float)
    ats_format_score = Column(Float)
    ats_experience_score = Column(Float)
    resume_tailored_date = Column(DateTime)
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.now, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def to_dict(self):
        """Convert job to dictionary."""
        return {
            'id': self.id,
            'job_url': self.job_url,
            'site': self.site,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'date_posted': self.date_posted,
            'job_type': self.job_type,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'applied': self.applied,
            'applied_date': self.applied_date,
            'notes': self.notes,
            'tailored_resume': self.tailored_resume,
            'ats_score': self.ats_score,
            'ats_keyword_match': self.ats_keyword_match,
            'ats_skills_match': self.ats_skills_match,
            'ats_format_score': self.ats_format_score,
            'ats_experience_score': self.ats_experience_score,
            'resume_tailored_date': self.resume_tailored_date,
            'first_seen': self.first_seen,
            'last_updated': self.last_updated
        }


class JobDatabase:
    """Database manager for job listings."""
    
    def __init__(self, db_path='jobs.db'):
        """Initialize database connection."""
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_job(self, job_data):
        """
        Add a new job to the database or update if it exists.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Job object
        """
        # Check if job already exists by URL
        existing_job = self.session.query(Job).filter_by(job_url=job_data.get('job_url')).first()
        
        if existing_job:
            # Update existing job
            for key, value in job_data.items():
                if hasattr(existing_job, key) and key not in ['id', 'first_seen', 'applied', 'applied_date', 'notes']:
                    setattr(existing_job, key, value)
            existing_job.last_updated = datetime.now()
            self.session.commit()
            return existing_job
        else:
            # Create new job
            job = Job(**job_data)
            self.session.add(job)
            self.session.commit()
            return job
    
    def add_jobs_from_dataframe(self, df):
        """
        Add multiple jobs from a pandas DataFrame.
        
        Args:
            df: Pandas DataFrame with job data
            
        Returns:
            Number of jobs added/updated
        """
        count = 0
        for _, row in df.iterrows():
            job_data = {
                'job_url': row.get('job_url'),
                'site': row.get('site'),
                'title': row.get('title'),
                'company': row.get('company'),
                'location': row.get('location'),
                'description': row.get('description'),
                'date_posted': pd.to_datetime(row.get('date_posted')) if pd.notna(row.get('date_posted')) else None,
                'job_type': row.get('job_type'),
                'salary_min': row.get('min_amount') if pd.notna(row.get('min_amount')) else None,
                'salary_max': row.get('max_amount') if pd.notna(row.get('max_amount')) else None,
                'salary_currency': row.get('currency'),
            }
            
            # Only add if job_url exists
            if job_data['job_url']:
                self.add_job(job_data)
                count += 1
        
        return count
    
    def get_all_jobs(self):
        """Get all jobs from database."""
        return self.session.query(Job).all()
    
    def get_jobs_dataframe(self, applied_filter=None):
        """
        Get jobs as a pandas DataFrame.
        
        Args:
            applied_filter: None (all), True (applied only), False (not applied only)
            
        Returns:
            Pandas DataFrame
        """
        query = self.session.query(Job)
        
        if applied_filter is not None:
            query = query.filter_by(applied=applied_filter)
        
        jobs = query.order_by(Job.date_posted.desc()).all()
        
        if not jobs:
            return pd.DataFrame()
        
        return pd.DataFrame([job.to_dict() for job in jobs])
    
    def mark_as_applied(self, job_id, notes=''):
        """
        Mark a job as applied.
        
        Args:
            job_id: Job ID
            notes: Optional notes about the application
        """
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            job.applied = True
            job.applied_date = datetime.now()
            if notes:
                job.notes = notes
            self.session.commit()
            return True
        return False
    
    def mark_as_not_applied(self, job_id):
        """
        Mark a job as not applied.
        
        Args:
            job_id: Job ID
        """
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            job.applied = False
            job.applied_date = None
            self.session.commit()
            return True
        return False
    
    def update_notes(self, job_id, notes):
        """
        Update notes for a job.
        
        Args:
            job_id: Job ID
            notes: Notes text
        """
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            job.notes = notes
            self.session.commit()
            return True
        return False
    
    def get_job_by_id(self, job_id):
        """Get a specific job by ID."""
        return self.session.query(Job).filter_by(id=job_id).first()
    
    def get_job_by_url(self, job_url):
        """Get a specific job by URL."""
        return self.session.query(Job).filter_by(job_url=job_url).first()
    
    def delete_job(self, job_id):
        """Delete a job from database."""
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            self.session.delete(job)
            self.session.commit()
            return True
        return False
    
    def get_statistics(self):
        """Get database statistics."""
        total_jobs = self.session.query(Job).count()
        applied_jobs = self.session.query(Job).filter_by(applied=True).count()
        not_applied_jobs = self.session.query(Job).filter_by(applied=False).count()
        
        return {
            'total_jobs': total_jobs,
            'applied_jobs': applied_jobs,
            'not_applied_jobs': not_applied_jobs,
            'application_rate': (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }
    
    def search_jobs(self, search_term='', site=None, company=None, applied=None):
        """
        Search jobs with filters.
        
        Args:
            search_term: Search in title, company, or description
            site: Filter by site
            company: Filter by company
            applied: Filter by application status
            
        Returns:
            List of Job objects
        """
        query = self.session.query(Job)
        
        if search_term:
            search_pattern = f'%{search_term}%'
            query = query.filter(
                (Job.title.like(search_pattern)) |
                (Job.company.like(search_pattern)) |
                (Job.description.like(search_pattern))
            )
        
        if site:
            query = query.filter_by(site=site)
        
        if company:
            query = query.filter_by(company=company)
        
        if applied is not None:
            query = query.filter_by(applied=applied)
        
        return query.order_by(Job.date_posted.desc()).all()
    
    def save_tailored_resume(self, job_id, tailored_resume_text, ats_scores):
        """
        Save tailored resume and ATS scores for a job.
        
        Args:
            job_id: Job ID
            tailored_resume_text: Tailored resume text
            ats_scores: Dictionary with ATS scores
        """
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            job.tailored_resume = tailored_resume_text
            job.ats_score = ats_scores.get('overall_score')
            job.ats_keyword_match = ats_scores.get('keyword_match')
            job.ats_skills_match = ats_scores.get('skills_match')
            job.ats_format_score = ats_scores.get('format_compatibility')
            job.ats_experience_score = ats_scores.get('experience_relevance')
            job.resume_tailored_date = datetime.now()
            self.session.commit()
            return True
        return False
    
    def get_tailored_resume(self, job_id):
        """Get tailored resume for a job."""
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job and job.tailored_resume:
            return {
                'resume_text': job.tailored_resume,
                'ats_score': job.ats_score,
                'ats_keyword_match': job.ats_keyword_match,
                'ats_skills_match': job.ats_skills_match,
                'ats_format_score': job.ats_format_score,
                'ats_experience_score': job.ats_experience_score,
                'tailored_date': job.resume_tailored_date
            }
        return None
    
    def get_jobs_with_tailored_resumes(self):
        """Get all jobs that have tailored resumes."""
        jobs = self.session.query(Job).filter(Job.tailored_resume.isnot(None)).all()
        return pd.DataFrame([job.to_dict() for job in jobs]) if jobs else pd.DataFrame()
    
    def close(self):
        """Close database connection."""
        self.session.close()
