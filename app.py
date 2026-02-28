import streamlit as st
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from database import JobDatabase
from resume_tailor import ResumeTailor
from pdf_generator import ResumePDFGenerator
from dotenv import load_dotenv
import os
import io
import re
from docx import Document

# Load environment variables - use explicit path for Poetry
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Try to load from Streamlit secrets if .env fails
if 'OPENAI_API_KEY' not in os.environ:
    try:
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
            print("✅ Loaded OPENAI_API_KEY from Streamlit secrets")
    except Exception:
        pass

# Debug: Check if API key is loaded
print(f"📁 Looking for .env at: {env_path}")
print(f"📁 .env exists: {env_path.exists()}")
if 'OPENAI_API_KEY' in os.environ:
    api_key_preview = os.environ['OPENAI_API_KEY']
    print(f"✅ OPENAI_API_KEY loaded (starts with: {api_key_preview[:7]}...)")
else:
    print("⚠️ OPENAI_API_KEY not found in app.py environment")
    print(f"⚠️ Current working directory: {os.getcwd()}")
    print(f"⚠️ Available OPENAI vars: {[k for k in os.environ.keys() if 'OPENAI' in k]}")

# Page configuration
st.set_page_config(
    page_title="Job Search Application",
    page_icon="🔍",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_database():
    return JobDatabase('jobs.db')

db = get_database()


@st.cache_resource
def get_tailoring_executor():
    """Get shared thread pool for background tailoring tasks."""
    return ThreadPoolExecutor(max_workers=2)


def _safe_filename_part(value: str) -> str:
    """Sanitize text for filesystem-safe filenames."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    return cleaned.strip("_") or "unknown"


def _background_tailor_resume_pdf(
    job_id: int,
    job_title: str,
    company: str,
    job_description: str,
    resume_text: str,
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Tailor a resume and persist both text (DB) and PDF (filesystem) in a background thread.
    """
    resume_tailor = ResumeTailor(model=model)
    if not resume_tailor.available:
        raise ValueError("OpenAI API key not configured.")

    result = resume_tailor.tailor_resume_agent(
        resume_text=resume_text,
        job_description=job_description,
        job_title=job_title,
        company=company,
        target_score=83.0,
    )

    tailored_text = result.resume_text
    ats_scores = resume_tailor.get_ats_score(tailored_text, job_description)

    # Use a fresh DB session in the worker thread.
    worker_db = JobDatabase("jobs.db")
    worker_db.save_tailored_resume(job_id, tailored_text, ats_scores)

    pdf_generator = ResumePDFGenerator()
    pdf_bytes = pdf_generator.generate_pdf(
        result.resume,
        job_title=job_title,
        company=company,
    )

    output_dir = Path(__file__).parent / "generated_resumes"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"resume_job_{job_id}_"
        f"{_safe_filename_part(company)}_"
        f"{_safe_filename_part(job_title)}_"
        f"{timestamp}.pdf"
    )
    pdf_path = output_dir / filename
    pdf_path.write_bytes(pdf_bytes)

    return {
        "job_id": job_id,
        "pdf_path": str(pdf_path.resolve()),
        "tailored_text": tailored_text,
        "ats_scores": ats_scores,
    }


def _find_latest_pdf_for_job(job_id: int) -> str:
    """Find the most recent generated PDF path for a given job ID."""
    output_dir = Path(__file__).parent / "generated_resumes"
    if not output_dir.exists():
        return ""
    candidates = sorted(
        output_dir.glob(f"resume_job_{job_id}_*.pdf"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return ""
    return str(candidates[0].resolve())

# Title and description
st.title("🔍 Job Search Application")
st.markdown("Search for jobs across multiple platforms using advanced filters")

# Add tabs for different sections
main_tab, saved_jobs_tab, resume_tab, stats_tab = st.tabs(["🔍 Search Jobs", "💼 Saved Jobs", "📄 Resume Tailor", "📊 Statistics"])

# Sidebar filters
st.sidebar.header("Search Filters")

# Job title input
job_title = st.sidebar.text_input(
    "Job Title",
    placeholder="e.g., Software Engineer, Data Analyst",
    help="Enter the job title you're searching for"
)

# Years of experience
years_experience = st.sidebar.number_input(
    "Years of Experience",
    min_value=0,
    max_value=30,
    value=0,
    step=1,
    help="Minimum years of experience required"
)

# Location input
location = st.sidebar.text_input(
    "Location",
    placeholder="e.g., San Francisco, CA or Remote",
    help="Enter the job location"
)

# Hours old filter
hours_old = st.sidebar.number_input(
    "Posted Within (Hours)",
    min_value=1,
    max_value=720,  # 30 days
    value=24,
    step=1,
    help="Filter jobs posted within the last N hours"
)

# Description quality filter
require_description = st.sidebar.checkbox(
    "Only Jobs With Description",
    value=True,
    help="Show and prioritize jobs that include a non-empty description"
)

# Number of results
results_wanted = st.sidebar.number_input(
    "Number of Results",
    min_value=1,
    max_value=100,
    value=20,
    step=5,
    help="Maximum number of job listings to retrieve"
)

# Site selection with checkboxes
st.sidebar.subheader("Job Sites")
st.sidebar.markdown("Select the sites to search:")

site_indeed = st.sidebar.checkbox("Indeed", value=True)
site_linkedin = st.sidebar.checkbox("LinkedIn", value=True)
site_zip_recruiter = st.sidebar.checkbox("ZipRecruiter", value=True)
site_google = st.sidebar.checkbox("Google", value=False)

# Build site list based on selections
selected_sites = []
if site_indeed:
    selected_sites.append("indeed")
if site_linkedin:
    selected_sites.append("linkedin")
if site_zip_recruiter:
    selected_sites.append("zip_recruiter")
if site_google:
    selected_sites.append("google")

# Search button
search_button = st.sidebar.button("🔎 Search Jobs", type="primary", width="stretch")

# Main tab content
with main_tab:
    if search_button:
        if not job_title:
            st.error("⚠️ Please enter a job title to search")
        elif not selected_sites:
            st.error("⚠️ Please select at least one job site")
        else:
            with st.spinner(f"Searching for {job_title} jobs on {', '.join(selected_sites)}..."):
                try:
                    # Perform job search
                    jobs_df = scrape_jobs(
                        site_name=selected_sites,
                        search_term=job_title,
                        location=location if location else None,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        country_indeed='USA'  # Can be made configurable
                    )
                    
                    if jobs_df is not None and len(jobs_df) > 0:
                        original_count = len(jobs_df)

                        # Normalize/clean description values once so filtering and storage are consistent.
                        if 'description' in jobs_df.columns:
                            has_description_mask = (
                                jobs_df['description'].notna()
                                & jobs_df['description'].astype(str).str.strip().ne('')
                            )
                        else:
                            has_description_mask = pd.Series(False, index=jobs_df.index)

                        # Optional UI filter: only show jobs with non-empty descriptions.
                        if require_description:
                            jobs_df = jobs_df[has_description_mask].copy()

                        # Save jobs to database
                        with st.spinner("Saving jobs to database..."):
                            # Always store only jobs with non-empty descriptions.
                            jobs_to_store_df = jobs_df[has_description_mask.loc[jobs_df.index]].copy()
                            saved_count = db.add_jobs_from_dataframe(jobs_to_store_df)
                            if require_description:
                                st.success(
                                    f"✅ Found {len(jobs_df)} job listings with descriptions "
                                    f"(from {original_count} total). ({saved_count} new/updated in database)"
                                )
                            else:
                                st.success(
                                    f"✅ Found {len(jobs_df)} job listings total; "
                                    f"stored {len(jobs_to_store_df)} with descriptions only. "
                                    f"({saved_count} new/updated in database)"
                                )
                        
                        # Filter by years of experience if specified
                        if years_experience > 0:
                            st.info(f"ℹ️ Note: Experience filter ({years_experience} years) applied as a reference. Review job descriptions for actual requirements.")
                        
                        # Display summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Jobs", len(jobs_df))
                        with col2:
                            unique_companies = jobs_df['company'].nunique() if 'company' in jobs_df.columns else 0
                            st.metric("Companies", unique_companies)
                        with col3:
                            remote_jobs = len(jobs_df[jobs_df['location'].str.contains('Remote', case=False, na=False)]) if 'location' in jobs_df.columns else 0
                            st.metric("Remote Jobs", remote_jobs)
                        with col4:
                            sites_found = jobs_df['site'].nunique() if 'site' in jobs_df.columns else 0
                            st.metric("Sites", sites_found)
                        
                        st.divider()
                        
                        # Display filters for results
                        st.subheader("Filter Results")
                        filter_col1, filter_col2 = st.columns(2)
                        
                        with filter_col1:
                            if 'site' in jobs_df.columns:
                                site_filter = st.multiselect(
                                    "Filter by Site",
                                    options=jobs_df['site'].unique().tolist(),
                                    default=jobs_df['site'].unique().tolist()
                                )
                                jobs_df = jobs_df[jobs_df['site'].isin(site_filter)]
                        
                        with filter_col2:
                            if 'company' in jobs_df.columns:
                                company_filter = st.multiselect(
                                    "Filter by Company",
                                    options=sorted(jobs_df['company'].dropna().unique().tolist()),
                                    default=None
                                )
                                if company_filter:
                                    jobs_df = jobs_df[jobs_df['company'].isin(company_filter)]
                        
                        st.divider()
                        
                        # Display job listings
                        st.subheader("Job Listings")
                        
                        # Create tabs for different views
                        tab1, tab2 = st.tabs(["📋 Card View", "📊 Table View"])
                        
                        with tab1:
                            # Card view for each job
                            for idx, row in jobs_df.iterrows():
                                # Get job from database to check application status
                                db_job = db.get_job_by_url(row.get('job_url')) if row.get('job_url') else None
                                
                                with st.container():
                                    col_a, col_b = st.columns([3, 1])
                                    
                                    with col_a:
                                        title_text = f"### {row.get('title', 'N/A')}"
                                        if db_job and db_job.applied:
                                            title_text += " ✅"
                                        st.markdown(title_text)
                                        st.markdown(f"**Company:** {row.get('company', 'N/A')}")
                                        st.markdown(f"**Location:** {row.get('location', 'N/A')}")
                                        
                                        if 'description' in row and pd.notna(row['description']):
                                            with st.expander("View Full Description", expanded=False):
                                                st.markdown(row['description'])
                                    
                                    with col_b:
                                        st.markdown(f"**Site:** {row.get('site', 'N/A')}")
                                        if 'date_posted' in row and pd.notna(row['date_posted']):
                                            st.markdown(f"**Posted:** {row['date_posted']}")
                                        if 'job_url' in row and pd.notna(row['job_url']):
                                            st.link_button("View Job", row['job_url'], width="stretch")
                                        
                                        # Application status toggle
                                        if db_job:
                                            if db_job.applied:
                                                if st.button("Mark Not Applied", key=f"unapply_{db_job.id}", width="stretch"):
                                                    db.mark_as_not_applied(db_job.id)
                                                    st.rerun()
                                            else:
                                                if st.button("Mark as Applied", key=f"apply_{db_job.id}", width="stretch", type="primary"):
                                                    db.mark_as_applied(db_job.id)
                                                    st.rerun()
                                    
                                    st.divider()
                        
                        with tab2:
                            # Table view
                            display_columns = ['title', 'company', 'location', 'site', 'date_posted']
                            available_columns = [col for col in display_columns if col in jobs_df.columns]
                            
                            st.dataframe(
                                jobs_df[available_columns],
                                width="stretch",
                                hide_index=True
                            )
                        
                        # Download button
                        st.divider()
                        csv = jobs_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv,
                            file_name=f"job_search_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            width="stretch"
                        )
                        
                    else:
                        st.warning("⚠️ No jobs found matching your criteria. Try adjusting your filters.")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred while searching for jobs: {str(e)}")
                    st.info("💡 Tip: Try adjusting your search parameters or selecting different job sites.")

    else:
        # Display welcome message when no search has been performed
        st.info("👈 Use the sidebar to configure your job search filters and click 'Search Jobs' to begin.")
        
        st.markdown("""
        ### How to Use This App
        
        1. **Enter Job Title**: Specify the position you're looking for (e.g., "Software Engineer", "Data Analyst")
        2. **Set Experience Level**: Indicate your years of experience (optional)
        3. **Specify Location**: Enter a city, state, or "Remote" for remote positions
        4. **Set Time Filter**: Choose how recent the job postings should be (in hours)
        5. **Select Job Sites**: Check the boxes for the job boards you want to search
        6. **Click Search**: Hit the search button to find matching jobs
        
        ### Features
        
        - 🔍 Search across multiple job platforms simultaneously
        - 💾 Automatic database storage - no duplicate searches needed
        - ✅ Track application status for each job
        - 📊 View results in card or table format
        - 🔽 Download results as CSV for offline analysis
        - 🎯 Filter results by company and site
        - ⏰ Filter by posting date to find the freshest opportunities
        
        ### Supported Job Sites
        
        - **Indeed**: One of the largest job search engines
        - **LinkedIn**: Professional networking platform with job listings
        - **ZipRecruiter**: Job search engine and employment marketplace
        - **Google**: Google for Jobs aggregator
        """)

# Saved Jobs Tab
with saved_jobs_tab:
    st.header("💼 Saved Jobs")

    if 'saved_job_tailoring_status' not in st.session_state:
        st.session_state['saved_job_tailoring_status'] = {}
    if 'saved_job_tailoring_futures' not in st.session_state:
        st.session_state['saved_job_tailoring_futures'] = {}

    tailoring_status = st.session_state['saved_job_tailoring_status']
    tailoring_futures = st.session_state['saved_job_tailoring_futures']
    tailoring_executor = get_tailoring_executor()
    if tailoring_futures:
        st.caption("Background tailoring in progress. Status auto-refreshes every 5 seconds.")
        if hasattr(st, "autorefresh"):
            st.autorefresh(interval=5000, key="saved_jobs_tailoring_refresh")
        else:
            st.info("Click any button to refresh status.")
    
    # Filters for saved jobs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        app_status_filter = st.selectbox(
            "Application Status",
            ["All Jobs", "Not Applied", "Applied"],
            key="saved_app_filter"
        )
    
    with col2:
        search_term = st.text_input("Search in saved jobs", placeholder="Title, company, or description", key="saved_search")
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Date Posted (Newest)", "Date Posted (Oldest)", "Company", "Title"], key="saved_sort")
    
    # Get filter value
    if app_status_filter == "Applied":
        applied_filter = True
    elif app_status_filter == "Not Applied":
        applied_filter = False
    else:
        applied_filter = None
    
    # Get saved jobs
    saved_jobs_df = db.get_jobs_dataframe(applied_filter=applied_filter)
    
    if not saved_jobs_df.empty:
        # Apply search filter
        if search_term:
            mask = (
                saved_jobs_df['title'].str.contains(search_term, case=False, na=False) |
                saved_jobs_df['company'].str.contains(search_term, case=False, na=False) |
                saved_jobs_df['description'].str.contains(search_term, case=False, na=False)
            )
            saved_jobs_df = saved_jobs_df[mask]
        
        # Apply sorting
        if sort_by == "Date Posted (Newest)":
            saved_jobs_df = saved_jobs_df.sort_values('date_posted', ascending=False)
        elif sort_by == "Date Posted (Oldest)":
            saved_jobs_df = saved_jobs_df.sort_values('date_posted', ascending=True)
        elif sort_by == "Company":
            saved_jobs_df = saved_jobs_df.sort_values('company')
        elif sort_by == "Title":
            saved_jobs_df = saved_jobs_df.sort_values('title')
        
        st.success(f"Found {len(saved_jobs_df)} saved jobs")
        
        # Display saved jobs
        for idx, row in saved_jobs_df.iterrows():
            with st.container():
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    title_text = f"### {row.get('title', 'N/A')}"
                    if row.get('applied'):
                        title_text += " ✅"
                    st.markdown(title_text)
                    st.markdown(f"**Company:** {row.get('company', 'N/A')}")
                    st.markdown(f"**Location:** {row.get('location', 'N/A')}")
                    
                    if row.get('applied'):
                        st.markdown(f"**Applied on:** {row.get('applied_date')}")
                    
                    if row.get('notes'):
                        st.info(f"📝 Notes: {row['notes']}")
                    
                    if pd.notna(row.get('description')):
                        with st.expander("View Full Description", expanded=False):
                            st.markdown(row['description'])
                
                with col_b:
                    st.markdown(f"**Site:** {row.get('site', 'N/A')}")
                    if pd.notna(row.get('date_posted')):
                        st.markdown(f"**Posted:** {row['date_posted']}")
                    
                    if pd.notna(row.get('job_url')):
                        st.link_button("View Job", row['job_url'], width="stretch")

                    job_id = int(row['id'])
                    current_status = tailoring_status.get(job_id)
                    current_future = tailoring_futures.get(job_id)

                    if (
                        not current_status
                        and isinstance(row.get('tailored_resume'), str)
                        and row.get('tailored_resume').strip()
                    ):
                        current_status = {
                            'state': 'completed',
                            'message': 'Tailored resume is available for this job.',
                            'pdf_path': _find_latest_pdf_for_job(job_id),
                            'updated_at': datetime.now().isoformat(),
                        }
                        tailoring_status[job_id] = current_status

                    # Update status when background work completes.
                    if current_future and current_future.done():
                        try:
                            output = current_future.result()
                            current_status = {
                                'state': 'completed',
                                'message': 'Tailored resume is available for this job.',
                                'pdf_path': output['pdf_path'],
                                'updated_at': datetime.now().isoformat(),
                            }
                            tailoring_status[job_id] = current_status
                        except Exception as bg_error:
                            current_status = {
                                'state': 'failed',
                                'message': f"Tailoring failed: {str(bg_error)}",
                                'updated_at': datetime.now().isoformat(),
                            }
                            tailoring_status[job_id] = current_status
                        finally:
                            tailoring_futures.pop(job_id, None)
                            st.rerun()

                    if current_status and current_status.get('state') == 'running':
                        st.info("⏳ Tailoring in background...")
                    elif current_status and current_status.get('state') == 'completed':
                        st.success("✅ Tailored resume available")
                        pdf_path = current_status.get('pdf_path') or _find_latest_pdf_for_job(job_id)
                        if pdf_path:
                            st.text_input(
                                "Resume file location",
                                value=pdf_path,
                                key=f"tailored_path_{job_id}",
                                help="Copy this path to access the generated PDF.",
                            )
                        else:
                            st.caption("PDF path not found yet. Tailored text is available in the database.")
                    elif current_status and current_status.get('state') == 'failed':
                        st.error(current_status.get('message', 'Tailoring failed'))

                    tailor_disabled = bool(current_future)
                    if st.button(
                        "✨ Tailor Resume (PDF)",
                        key=f"tailor_saved_{job_id}",
                        width="stretch",
                        disabled=tailor_disabled,
                    ):
                        if pd.isna(row.get('description')) or not row.get('description'):
                            st.error("❌ This job has no description. Cannot tailor without a job description.")
                        elif 'parsed_resume_data' in st.session_state:
                            from resume_parser import LLMResumeParser
                            parser = LLMResumeParser()
                            resume_text_to_use = parser.resume_data_to_text(st.session_state['parsed_resume_data'])

                            future = tailoring_executor.submit(
                                _background_tailor_resume_pdf,
                                job_id=job_id,
                                job_title=str(row.get('title') or 'Position'),
                                company=str(row.get('company') or 'Company'),
                                job_description=str(row.get('description') or ''),
                                resume_text=resume_text_to_use,
                                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                            )
                            tailoring_futures[job_id] = future
                            tailoring_status[job_id] = {
                                'state': 'running',
                                'message': 'Tailoring started.',
                                'updated_at': datetime.now().isoformat(),
                            }
                            st.success("Tailoring started in background. Refresh this tab in a few seconds.")
                            st.rerun()
                        elif st.session_state.get('resume_text'):
                            resume_text_to_use = st.session_state['resume_text']
                            future = tailoring_executor.submit(
                                _background_tailor_resume_pdf,
                                job_id=job_id,
                                job_title=str(row.get('title') or 'Position'),
                                company=str(row.get('company') or 'Company'),
                                job_description=str(row.get('description') or ''),
                                resume_text=resume_text_to_use,
                                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                            )
                            tailoring_futures[job_id] = future
                            tailoring_status[job_id] = {
                                'state': 'running',
                                'message': 'Tailoring started.',
                                'updated_at': datetime.now().isoformat(),
                            }
                            st.success("Tailoring started in background. Refresh this tab in a few seconds.")
                            st.rerun()
                        else:
                            st.error("❌ Resume data not found. Upload or fill your resume in the Resume Tailor tab first.")
                    
                    # Application status toggle
                    if row.get('applied'):
                        if st.button("Mark Not Applied", key=f"unapply_saved_{row['id']}", width="stretch"):
                            db.mark_as_not_applied(row['id'])
                            st.rerun()
                    else:
                        if st.button("Mark as Applied", key=f"apply_saved_{row['id']}", width="stretch", type="primary"):
                            db.mark_as_applied(row['id'])
                            st.rerun()
                    
                    # Notes section
                    with st.expander("📝 Notes"):
                        notes = st.text_area(
                            "Add notes",
                            value=row.get('notes', ''),
                            key=f"notes_{row['id']}",
                            height=100
                        )
                        if st.button("Save Notes", key=f"save_notes_{row['id']}"):
                            db.update_notes(row['id'], notes)
                            st.success("Notes saved!")
                            st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_{row['id']}", width="stretch"):
                        db.delete_job(row['id'])
                        st.rerun()
                
                st.divider()
        
        # Download button
        st.divider()
        csv = saved_jobs_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Saved Jobs as CSV",
            data=csv,
            file_name=f"saved_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width="stretch"
        )
    else:
        st.info("No saved jobs found. Start searching to add jobs to your database!")

# Resume Tailor Tab
with resume_tab:
    st.header("📄 AI Resume Tailor with ATS Scoring")
    st.markdown("Tailor your resume for each job using OpenAI to achieve 83%+ ATS match")
    
    # Check if OpenAI API key is configured
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if openai_api_key:
        openai_available = True
        st.success("✅ OpenAI API key configured")
        
        # Available models
        model_names = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        st.info(f"📦 Available models: {', '.join(model_names)}")
            
    else:
        openai_available = False
        st.error("❌ OpenAI API key not configured")
        st.info("""
        **To use resume tailoring, you need to configure your OpenAI API key:**
        
        1. Get an API key from https://platform.openai.com/api-keys
        2. Create a `.env` file in the project root
        3. Add: `OPENAI_API_KEY=your-api-key-here`
        4. Refresh this page
        
        Alternatively, you can set the environment variable:
        ```bash
        export OPENAI_API_KEY=your-api-key-here
        ```
        """)
    
    if openai_available:
        # Simplified Resume Input
        st.divider()
        
        col_header, col_clear = st.columns([4, 1])
        with col_header:
            st.subheader("1️⃣ Your Resume")
        with col_clear:
            # Clear button to reset resume data
            if st.button("🗑️ Clear", help="Clear all resume data and start fresh"):
                keys_to_clear = ['resume_text', 'resume_filename', 'parsed_resume_data']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("✅ Resume data cleared!")
                st.rerun()
        
        # Optional: Upload resume to auto-populate form
        with st.expander("📤 Upload Resume (Optional - Auto-populates form)", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload your resume (PDF or DOCX)",
                type=['pdf', 'docx'],
                help="Upload to automatically parse and populate the form below",
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                # Check if this is a new file (different from cached one)
                is_new_file = (
                    'resume_filename' not in st.session_state or 
                    st.session_state.get('resume_filename') != uploaded_file.name
                )
                
                # Store resume in session state
                if is_new_file:
                    with st.spinner("Parsing resume..."):
                        try:
                            resume_tailor = ResumeTailor()
                            resume_text = resume_tailor.extract_text_from_file(uploaded_file)
                            
                            # Clear old data first
                            st.session_state['resume_text'] = resume_text
                            st.session_state['resume_filename'] = uploaded_file.name
                            
                            # Parse to ResumeData for form population
                            from resume_parser import LLMResumeParser
                            parser = LLMResumeParser()
                            new_resume_data = parser.parse_resume(resume_text)
                            
                            # Replace old parsed data with new one
                            st.session_state['parsed_resume_data'] = new_resume_data
                            
                            st.success(f"✅ {uploaded_file.name} parsed successfully! Form populated below.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error parsing resume: {str(e)}")
                else:
                    st.info(f"✅ Using: {uploaded_file.name}")
        
        st.divider()
        
        # Always show the form (pre-populated if resume was uploaded)
        from resume_form import render_resume_form
        
        # Pre-populate with parsed data if available
        pre_populated = st.session_state.get('parsed_resume_data', None)
        
        if pre_populated:
            st.info("💡 Form is pre-populated from your uploaded resume. Edit any fields as needed.")
        else:
            st.info("💡 Fill out the form below manually, or upload a resume above to auto-populate.")
        
        resume_data = render_resume_form(pre_populated)
        
        if resume_data:
            # Store in session state
            st.session_state['parsed_resume_data'] = resume_data
            # Keep the original resume text if it exists
            if 'resume_text' not in st.session_state:
                st.session_state['resume_text'] = "Manual entry"
        
        # Continue only if we have resume data
        if 'parsed_resume_data' in st.session_state:
            st.divider()
            
            # Select job to tailor resume for
            st.subheader("2️⃣ Select Job to Tailor Resume")
            
            saved_jobs_df = db.get_jobs_dataframe()
            
            if not saved_jobs_df.empty:
                # Create a display name for each job
                saved_jobs_df['display_name'] = saved_jobs_df.apply(
                    lambda row: f"{row['title']} at {row['company']} ({row['site']})", axis=1
                )
                
                selected_job_display = st.selectbox(
                    "Choose a job",
                    options=saved_jobs_df['display_name'].tolist(),
                    help="Select a job from your saved jobs to tailor your resume"
                )
                
                if selected_job_display:
                    selected_job = saved_jobs_df[saved_jobs_df['display_name'] == selected_job_display].iloc[0]
                    
                    # Show job details
                    with st.expander("📋 Job Details", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Title:** {selected_job['title']}")
                            st.markdown(f"**Company:** {selected_job['company']}")
                            st.markdown(f"**Location:** {selected_job['location']}")
                        with col2:
                            st.markdown(f"**Site:** {selected_job['site']}")
                            st.markdown(f"**Posted:** {selected_job['date_posted']}")
                            if pd.notna(selected_job.get('job_url')):
                                st.link_button("View Job", selected_job['job_url'])
                        
                        if pd.notna(selected_job.get('description')):
                            st.markdown("**Job Description:**")
                            st.text_area("Description", selected_job['description'], height=150, disabled=True)
                    
                    st.divider()
                    
                    # Tailoring options
                    st.subheader("3️⃣ Tailor Resume")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        target_score = st.slider(
                            "Target ATS Score (%)",
                            min_value=70,
                            max_value=95,
                            value=83,
                            help="Target ATS compatibility score"
                        )
                    
                    with col2:
                        model_choice = st.selectbox(
                            "OpenAI Model",
                            options=model_names,
                            index=1,  # Default to gpt-4o-mini
                            help="Select which OpenAI model to use"
                        )
                    
                    # Check if already tailored (from DB or just tailored in this session)
                    existing_tailored = db.get_tailored_resume(selected_job['id'])
                    
                    # Check if we just tailored this job in the current session
                    just_tailored = st.session_state.get('just_tailored', {})
                    if just_tailored.get('job_id') == selected_job['id']:
                        # Use the just-tailored data
                        existing_tailored = {
                            'resume_text': just_tailored['text'],
                            'ats_score': just_tailored['scores']['overall_score'],
                            'ats_keyword_match': just_tailored['scores']['keyword_match'],
                            'ats_skills_match': just_tailored['scores']['skills_match'],
                            'ats_format_score': just_tailored['scores']['format_compatibility'],
                            'ats_experience_score': just_tailored['scores'].get('experience_match', 0),
                            'tailored_date': 'Just now'
                        }
                    
                    if existing_tailored:
                        st.info(f"📝 Resume already tailored for this job (ATS Score: {existing_tailored['ats_score']:.1f}%) on {existing_tailored['tailored_date']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            tailor_button = st.button("🔄 Re-tailor Resume", type="secondary", width="stretch")
                        with col_b:
                            view_existing = st.button("👁️ View Existing", type="primary", width="stretch")
                    else:
                        tailor_button = st.button("✨ Tailor Resume", type="primary", width="stretch")
                        view_existing = False
                    
                    # Tailor resume
                    if tailor_button:
                        # Validate job description exists
                        if pd.isna(selected_job.get('description')) or not selected_job.get('description'):
                            st.error("❌ This job has no description. Cannot tailor resume without a job description.")
                        else:
                            with st.spinner(f"🤖 Tailoring resume using {model_choice} Agent... This may take 30-60 seconds..."):
                                try:
                                    resume_tailor = ResumeTailor(model=model_choice)
                                    
                                    # Use the edited parsed_resume_data if available, otherwise fall back to resume_text
                                    if 'parsed_resume_data' in st.session_state:
                                        # Convert ResumeData to text format for tailoring
                                        from resume_parser import LLMResumeParser
                                        parser = LLMResumeParser()
                                        resume_text_to_use = parser.resume_data_to_text(st.session_state['parsed_resume_data'])
                                    else:
                                        resume_text_to_use = st.session_state['resume_text']
                                    
                                    # Use agent-based method for autonomous iterative improvement
                                    result = resume_tailor.tailor_resume_agent(
                                        resume_text=resume_text_to_use,
                                        job_description=str(selected_job['description']),
                                        job_title=str(selected_job['title']),
                                        company=str(selected_job['company']),
                                        target_score=target_score
                                    )
                                    
                                    # Extract data from Pydantic model
                                    tailored_text = result.resume_text
                                    
                                    # Get ATS scores (placeholder for now)
                                    ats_scores = resume_tailor.get_ats_score(tailored_text, str(selected_job['description']))
                                    
                                    # Save to database
                                    db.save_tailored_resume(selected_job['id'], tailored_text, ats_scores)
                                    
                                    # Display success
                                    st.success(f"✅ Resume tailored successfully!")
                                    
                                    # Show structured resume details
                                    with st.expander("📋 Structured Resume Details", expanded=False):
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Skills", len(result.resume.skills))
                                        with col2:
                                            st.metric("Experience", len(result.resume.experience))
                                        with col3:
                                            st.metric("Education", len(result.resume.education))
                                        with col4:
                                            st.metric("Projects", len(result.resume.projects))
                                        
                                        st.markdown("**Contact:**")
                                        st.text(result.resume.contact.name)
                                        if result.resume.contact.email:
                                            st.text(f"Email: {result.resume.contact.email}")
                                        if result.resume.contact.phone:
                                            st.text(f"Phone: {result.resume.contact.phone}")
                                    
                                    # Store in session state to show results immediately
                                    st.session_state['just_tailored'] = {
                                        'job_id': selected_job['id'],
                                        'text': tailored_text,
                                        'scores': ats_scores,
                                        'resume_data': result.resume  # Store structured data
                                    }
                                    
                                    # Cache the ResumeData to avoid re-parsing when viewing later
                                    cache_key = f"resume_data_{selected_job['id']}"
                                    st.session_state[cache_key] = result.resume
                                    
                                    # Display ATS scores
                                    st.subheader("📊 ATS Score Breakdown")
                                    score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                                    
                                    with score_col1:
                                        st.metric("Overall Score", f"{ats_scores['overall_score']:.1f}%")
                                    with score_col2:
                                        st.metric("Keyword Match", f"{ats_scores['keyword_match']:.1f}%")
                                    with score_col3:
                                        st.metric("Skills Match", f"{ats_scores['skills_match']:.1f}%")
                                    with score_col4:
                                        st.metric("Format Score", f"{ats_scores['format_compatibility']:.1f}%")
                                    
                                    # Display tailored resume
                                    st.divider()
                                    st.subheader("📄 Tailored Resume")
                                    st.text_area("Tailored Resume Content", tailored_text, height=400)
                                    
                                    # Download buttons
                                    st.markdown("### Download Options")
                                    col_dl1, col_dl2 = st.columns(2)
                                    
                                    with col_dl1:
                                        st.download_button(
                                            label="📥 Download as TXT",
                                            data=tailored_text,
                                            file_name=f"resume_{selected_job['company']}_{selected_job['title'].replace(' ', '_')}.txt",
                                            mime="text/plain",
                                            width="stretch"
                                        )
                                    
                                    with col_dl2:
                                        # Generate PDF from structured ResumeData
                                        try:
                                            pdf_generator = ResumePDFGenerator()
                                            pdf_bytes = pdf_generator.generate_pdf(
                                                result.resume,  # Pass ResumeData directly
                                                job_title=selected_job['title'],
                                                company=selected_job['company']
                                            )
                                            st.download_button(
                                                label="📥 Download as PDF",
                                                data=pdf_bytes,
                                                file_name=f"resume_{selected_job['company']}_{selected_job['title'].replace(' ', '_')}.pdf",
                                                mime="application/pdf",
                                                width="stretch",
                                                type="primary"
                                            )
                                        except Exception as pdf_error:
                                            st.error(f"❌ PDF Generation Error: {str(pdf_error)}")
                                            st.info("💡 You can still download as TXT")
                                            print(f"\n{'='*60}")
                                            print(f"❌ PDF GENERATION ERROR (New Resume)")
                                            print(f"{'='*60}")
                                            print(f"Error type: {type(pdf_error).__name__}")
                                            print(f"Error message: {str(pdf_error)}")
                                            import traceback
                                            traceback.print_exc()
                                            print(f"{'='*60}\n")
                                    
                                except Exception as e:
                                    st.error(f"❌ Error tailoring resume: {str(e)}")
                    
                    # View existing tailored resume
                    elif view_existing and existing_tailored:
                        st.subheader("📊 ATS Score Breakdown")
                        score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                        
                        with score_col1:
                            st.metric("Overall Score", f"{existing_tailored['ats_score']:.1f}%")
                        with score_col2:
                            st.metric("Keyword Match", f"{existing_tailored['ats_keyword_match']:.1f}%")
                        with score_col3:
                            st.metric("Skills Match", f"{existing_tailored['ats_skills_match']:.1f}%")
                        with score_col4:
                            st.metric("Format Score", f"{existing_tailored['ats_format_score']:.1f}%")
                        
                        st.divider()
                        st.subheader("📄 Tailored Resume")
                        st.text_area("Tailored Resume Content", existing_tailored['resume_text'], height=400)
                        
                        # Download buttons
                        st.markdown("### Download Options")
                        col_dl1, col_dl2, col_dl3 = st.columns(3)
                        
                        with col_dl1:
                            st.download_button(
                                label="📥 Download as TXT",
                                data=existing_tailored['resume_text'],
                                file_name=f"resume_{selected_job['company']}_{selected_job['title'].replace(' ', '_')}.txt",
                                mime="text/plain",
                                width="stretch"
                            )
                        
                        with col_dl2:
                            # Generate PDF - check cache first to avoid re-parsing
                            try:
                                # Check if we have cached ResumeData for this job
                                cache_key = f"resume_data_{selected_job['id']}"
                                if cache_key in st.session_state:
                                    resume_data = st.session_state[cache_key]
                                    print("✅ Using cached ResumeData (no API call)")
                                else:
                                    # Parse text to ResumeData (calls OpenAI API)
                                    from resume_parser import LLMResumeParser
                                    print("⚠️ Parsing resume to ResumeData (OpenAI API call)")
                                    parser = LLMResumeParser()
                                    resume_data = parser.parse_resume(existing_tailored['resume_text'])
                                    # Cache it for future use
                                    st.session_state[cache_key] = resume_data
                                
                                pdf_generator = ResumePDFGenerator()
                                pdf_bytes = pdf_generator.generate_pdf(
                                    resume_data,  # Pass ResumeData
                                    job_title=selected_job['title'],
                                    company=selected_job['company']
                                )
                                st.download_button(
                                    label="📥 Download as PDF",
                                    data=pdf_bytes,
                                    file_name=f"resume_{selected_job['company']}_{selected_job['title'].replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    width="stretch",
                                    type="primary"
                                )
                            except Exception as pdf_error:
                                st.error(f"❌ PDF Generation Error: {str(pdf_error)}")
                                print(f"\n{'='*60}")
                                print(f"❌ PDF GENERATION ERROR")
                                print(f"{'='*60}")
                                print(f"Error type: {type(pdf_error).__name__}")
                                print(f"Error message: {str(pdf_error)}")
                                import traceback
                                traceback.print_exc()
                                print(f"{'='*60}\n")
                        
                        with col_dl3:
                            # Generate DOCX
                            from docx import Document
                            from docx.shared import Pt, RGBColor, Inches
                            from docx.enum.text import WD_ALIGN_PARAGRAPH
                            import io
                            import re
                            
                            doc = Document()
                            
                            # Set narrow margins
                            sections = doc.sections
                            for section in sections:
                                section.top_margin = Inches(0.5)
                                section.bottom_margin = Inches(0.5)
                                section.left_margin = Inches(0.5)
                                section.right_margin = Inches(0.5)
                            
                            # Helper function to check if line is a date
                            def is_date_line(line):
                                return bool(re.search(r'\d{4}\s*[-–—]\s*(\d{4}|Present|Current)', line))
                            
                            # Helper function to check if line is a job/school title
                            def is_title_line(line):
                                return len(line) < 100 and not line.startswith(('•', '-', '*'))
                            
                            # Add resume content
                            lines = existing_tailored['resume_text'].split('\n')
                            current_section = None
                            
                            # Add name (first line, centered, bold, large)
                            if lines:
                                name_para = doc.add_paragraph(lines[0])
                                name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                name_run = name_para.runs[0]
                                name_run.font.size = Pt(16)
                                name_run.font.bold = True
                                lines = lines[1:]
                            
                            # Process rest of content
                            i = 0
                            while i < len(lines):
                                line = lines[i].strip()
                                
                                if not line:
                                    i += 1
                                    continue
                                
                                # Check if section heading
                                if line.upper() in ['SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'CERTIFICATIONS', 'AWARDS', 'PROFESSIONAL SUMMARY', 'WORK EXPERIENCE']:
                                    current_section = line.upper()
                                    para = doc.add_paragraph()
                                    run = para.add_run(line)
                                    run.font.size = Pt(12)
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(44, 90, 160)
                                    # Add underline
                                    run.underline = True
                                    para.space_after = Pt(6)
                                
                                # Check if it's a job/school title (bold)
                                elif is_title_line(line) and not is_date_line(line) and current_section in ['EXPERIENCE', 'EDUCATION', 'PROJECTS', 'WORK EXPERIENCE']:
                                    para = doc.add_paragraph()
                                    run = para.add_run(line)
                                    run.font.size = Pt(11)
                                    run.font.bold = True
                                    para.space_after = Pt(2)
                                
                                # Check if it's a date line (italic, gray)
                                elif is_date_line(line):
                                    para = doc.add_paragraph()
                                    run = para.add_run(line)
                                    run.font.size = Pt(10)
                                    run.font.italic = True
                                    run.font.color.rgb = RGBColor(74, 74, 74)
                                    para.space_after = Pt(4)
                                
                                # Check if it's a bullet point
                                elif line.startswith(('•', '-', '*', '–', '—')):
                                    bullet_text = line[1:].strip()
                                    
                                    # Check if GPA in education section
                                    if current_section == 'EDUCATION' and re.search(r'\bGPA\b|Grade Point Average', bullet_text, re.IGNORECASE):
                                        para = doc.add_paragraph()
                                        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                                        run = para.add_run(bullet_text)
                                        run.font.size = Pt(10)
                                        para.space_after = Pt(2)
                                    else:
                                        para = doc.add_paragraph(bullet_text, style='List Bullet')
                                        run = para.runs[0]
                                        run.font.size = Pt(10)
                                        para.space_after = Pt(2)
                                
                                # Regular text
                                else:
                                    para = doc.add_paragraph()
                                    run = para.add_run(line)
                                    run.font.size = Pt(10)
                                    para.space_after = Pt(4)
                                
                                i += 1
                            
                            # Save to bytes
                            docx_buffer = io.BytesIO()
                            doc.save(docx_buffer)
                            docx_buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Download as DOCX",
                                data=docx_buffer.getvalue(),
                                file_name=f"resume_{selected_job['company']}_{selected_job['title'].replace(' ', '_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                width="stretch",
                                type="primary"
                            )
            else:
                st.info("No saved jobs found. Search for jobs first to tailor your resume!")

# Statistics Tab
with stats_tab:
    st.header("📊 Job Search Statistics")
    
    stats = db.get_statistics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs Saved", stats['total_jobs'])
    
    with col2:
        st.metric("Applied", stats['applied_jobs'])
    
    with col3:
        st.metric("Not Applied", stats['not_applied_jobs'])
    
    with col4:
        st.metric("Application Rate", f"{stats['application_rate']:.1f}%")
    
    st.divider()
    
    # Get all jobs for analysis
    all_jobs_df = db.get_jobs_dataframe()
    
    if not all_jobs_df.empty:
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Jobs by Site")
            site_counts = all_jobs_df['site'].value_counts()
            st.bar_chart(site_counts)
        
        with col_b:
            st.subheader("Top Companies")
            company_counts = all_jobs_df['company'].value_counts().head(10)
            st.bar_chart(company_counts)
        
        st.divider()
        
        st.subheader("Recent Activity")
        recent_jobs = all_jobs_df.sort_values('first_seen', ascending=False).head(10)
        st.dataframe(
            recent_jobs[['title', 'company', 'location', 'site', 'applied', 'first_seen']],
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No data available yet. Start searching for jobs to see statistics!")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px;'>
        <small>Job Search Application | Powered by python-jobspy & Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)
