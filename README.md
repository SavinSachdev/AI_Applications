# Job Search Application 🔍

A modern, user-friendly job search application built with Streamlit and powered by python-jobspy. Search for jobs across multiple platforms (Indeed, LinkedIn, ZipRecruiter, and Google) with advanced filtering options, database storage, and application tracking.

## Features ✨

- **Multi-Platform Search**: Search across Indeed, LinkedIn, ZipRecruiter, and Google simultaneously
- **Database Integration**: 
  - Automatic storage of all job search results in SQLite database
  - No need to re-search - all jobs are saved locally
  - Prevents duplicate entries
- **AI-Powered Resume Tailoring** 🆕:
  - Upload your resume (PDF or DOCX)
  - Automatically tailor it for each job using OpenAI via LlamaIndex
  - Target 83%+ ATS (Applicant Tracking System) compatibility
  - Get detailed ATS score breakdown
  - Powered by GPT-4o-mini for fast, accurate results
  - Download tailored resumes as professionally formatted PDF or TXT
  - PDF follows resume best practices with proper formatting and structure
- **Application Tracking**:
  - Mark jobs as "Applied" or "Not Applied"
  - Add notes to each job listing
  - Track application dates
  - Filter saved jobs by application status
- **Advanced Filters**: 
  - Job title search
  - Years of experience
  - Location-based filtering
  - Time-based filtering (hours since posting)
  - Customizable number of results
- **Interactive UI**: Clean, modern Streamlit interface with:
  - Three main tabs: Search Jobs, Saved Jobs, Statistics
  - Card view for detailed job information with full descriptions
  - Table view for quick scanning
  - Real-time filtering by site and company
  - Search within saved jobs
- **Export Functionality**: Download search results as CSV for offline analysis
- **Statistics Dashboard**: 
  - View total jobs saved, application rate, and more
  - Visualize jobs by site and top companies
  - Track recent activity

## Prerequisites 📋

- Python 3.10 or higher
- Poetry (for dependency management)
- **OpenAI API Key** (for AI resume tailoring) - Get one at https://platform.openai.com/api-keys

## Installation 🚀

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/savsachd/projects/splunk/Bb
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Configure OpenAI API Key** (for resume tailoring):
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your-api-key-here
   ```
   
   Or set it as an environment variable:
   ```bash
   export OPENAI_API_KEY=your-api-key-here
   ```

5. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Usage 🎯

1. **Run the application**:
   ```bash
   poetry run streamlit run app.py
   ```
   
   Or if you're already in the Poetry shell:
   ```bash
   streamlit run app.py
   ```

2. **Access the application**:
   - The app will automatically open in your default browser
   - If not, navigate to `http://localhost:8501`

3. **Search for jobs** (Search Jobs tab):
   - Enter a job title (e.g., "Software Engineer", "Data Analyst")
   - Set your years of experience (optional)
   - Specify a location or leave blank for all locations
   - Set the time filter (how recent the postings should be)
   - Select which job sites to search
   - Click "Search Jobs"
   - Jobs are automatically saved to the database

4. **View and manage results**:
   - Browse results in card or table view
   - View full job descriptions (no truncation)
   - Mark jobs as "Applied" or "Not Applied"
   - Filter by specific companies or sites
   - Click "View Job" to open the listing in a new tab
   - Download results as CSV for further analysis

5. **Manage saved jobs** (Saved Jobs tab):
   - View all jobs saved in the database
   - Filter by application status (All/Applied/Not Applied)
   - Search within saved jobs by title, company, or description
   - Sort by date, company, or title
   - Add notes to job listings
   - Mark jobs as applied/not applied
   - Delete jobs from the database

6. **Tailor your resume** (Resume Tailor tab):
   - Upload your resume (PDF or DOCX)
   - Select a saved job to tailor for
   - Choose target ATS score (default 83%)
   - Click "Tailor Resume" and wait 30-60 seconds
   - View ATS score breakdown
   - Download tailored resume as PDF (professionally formatted) or TXT
   - Re-tailor or view existing tailored resumes

7. **View statistics** (Statistics tab):
   - See total jobs saved and application rate
   - View charts of jobs by site and top companies
   - Track recent activity

## Configuration ⚙️

### Customizing Search Parameters

You can modify the default values in `app.py`:

- **Default hours old**: Line with `value=24` in the hours_old input
- **Default results wanted**: Line with `value=20` in the results_wanted input
- **Default country**: Line with `country_indeed='USA'` in the scrape_jobs call

### Adding More Job Sites

The python-jobspy library supports additional sites. To add more, update the checkbox section in `app.py` and add the corresponding site name to the `selected_sites` list.

## Project Structure 📁

```
.
├── app.py              # Main Streamlit application
├── database.py         # Database module for job storage and tracking
├── pyproject.toml      # Poetry configuration and dependencies
├── jobs.db             # SQLite database (created automatically)
└── README.md           # This file
```

## Dependencies 📦

- **streamlit**: Web UI framework
- **pandas**: Data manipulation and analysis
- **python-jobspy**: Job scraping library supporting multiple platforms
- **sqlalchemy**: Database ORM for SQLite integration
- **ollama**: Local AI/LLM integration for resume tailoring
- **python-docx**: DOCX file processing
- **pypdf2**: PDF file processing
- **python-dotenv**: Environment variable management
- **reportlab**: Professional PDF generation (industry standard)

## Troubleshooting 🔧

### Common Issues

1. **Import Error**: Make sure you're running the app within the Poetry environment
   ```bash
   poetry shell
   streamlit run app.py
   ```

2. **No results found**: 
   - Try broadening your search criteria
   - Increase the "hours old" filter
   - Try different job sites
   - Check your internet connection

3. **Slow search**: 
   - Reduce the number of results wanted
   - Search fewer sites at once
   - Some sites may be slower to respond

4. **Ollama not running**:
   - Check if Ollama is installed: `ollama --version`
   - Start Ollama: `ollama serve`
   - Pull a model if needed: `ollama pull llama3.1`
   - Verify models are available: `ollama list`

5. **Resume tailoring is slow**:
   - This is normal - AI processing takes 30-60 seconds
   - Larger models (70B+) will be slower but more accurate
   - Consider using smaller models like llama3.1 (8B) for faster results

## Tips for Best Results 💡

### Job Search
- Use specific job titles for more relevant results
- Try variations of job titles (e.g., "Software Engineer" vs "Software Developer")
- For remote jobs, include "Remote" in the location field
- Increase the hours old filter if you're not finding enough results
- Use the company filter to focus on specific employers

### Resume Tailoring
- Use a comprehensive master resume with all your skills and experiences
- The AI will emphasize relevant parts for each job
- Review and edit the tailored resume before submitting
- Higher target ATS scores (85%+) may require more iterations
- Different Ollama models produce different writing styles - experiment to find your preference
- Recommended models:
  - **llama3.1** (8B): Fast, good quality, recommended for most users
  - **llama3.1:70b**: Slower but higher quality output
  - **mistral**: Alternative option with different writing style

## Development 🛠️

### Running Tests

```bash
poetry run pytest
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is provided as-is for educational and personal use.

## Acknowledgments 🙏

- Built with [Streamlit](https://streamlit.io/)
- Job data powered by [python-jobspy](https://github.com/Bunsly/JobSpy)
- Data handling with [pandas](https://pandas.pydata.org/)

## Support 💬

For issues, questions, or suggestions, please open an issue in the project repository.

---

**Happy Job Hunting! 🎉**
