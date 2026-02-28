"""
Resume tailoring module using OpenAI structured output.
"""
import os
from typing import Dict
from docx import Document
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field
from openai import OpenAI

# Import existing resume models from resume_parser
from resume_parser import ResumeData


class AgentTailoringResult(BaseModel):
    """Structured result from agent-based resume tailoring."""
    resume: ResumeData = Field(description="Structured tailored resume using ResumeData model")
    resume_text: str = Field(description="The final tailored resume as plain text")


class ResumeTailor:
    """AI-powered resume tailoring using OpenAI structured output."""
    
    def __init__(self, model: str = None, api_key: str = None):
        """
        Initialize with OpenAI model.
        
        Args:
            model: OpenAI model name (default: gpt-4o-mini or from env OPENAI_MODEL)
            api_key: OpenAI API key (default: from env OPENAI_API_KEY)
        """
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        # Debug: Check if API key is loaded
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not found in environment variables")
            print("Available env vars:", [k for k in os.environ.keys() if 'OPENAI' in k or 'API' in k])
        else:
            print(f"✅ OpenAI API key loaded (length: {len(self.api_key)})")
        
        # Check if OpenAI API key is available
        if not self.api_key:
            self.available = False
            self.client = None
            print("❌ ResumeTailor not available - no API key")
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.available = True
                print(f"✅ ResumeTailor initialized with model: {self.model}")
            except Exception as e:
                print(f"❌ Error initializing ResumeTailor: {str(e)}")
                self.available = False
                self.client = None
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def extract_text_from_docx(self, docx_file) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(docx_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def extract_text_from_file(self, file) -> str:
        """Extract text from uploaded file (PDF or DOCX)."""
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file)
        elif file_extension in ['docx', 'doc']:
            return self.extract_text_from_docx(file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def tailor_resume_agent(
        self, 
        resume_text: str, 
        job_description: str, 
        job_title: str,
        company: str, 
        target_score: float = 83.0
    ) -> AgentTailoringResult:
        """
        Tailor resume using OpenAI structured output.
        
        Args:
            resume_text: Original resume text
            job_description: Job description to match
            job_title: Job title
            company: Company name
            target_score: Target ATS score (default 83%) - not used currently
            
        Returns:
            AgentTailoringResult: Structured result with resume and text
        """
        if not self.available:
            raise ValueError("OpenAI API key not configured.")
        
        # Validate inputs
        if not resume_text or not isinstance(resume_text, str):
            raise ValueError("Resume text is empty or invalid")
        
        if not job_description or not isinstance(job_description, str):
            raise ValueError("Job description is empty or invalid")
        
        if not job_title or not isinstance(job_title, str):
            job_title = "Position"
        
        if not company or not isinstance(company, str):
            company = "Company"
        
        # Create prompt for structured output
        prompt_template = f"""You are an expert resume tailoring specialist. Given the resume text and job description below, improve the text of the resume. The resume should be improved using the content from the provided text only.

IMPORTANT RULES:
1. Use ONLY content from the provided resume text - do not invent or add fake experience
2. Reorganize and rephrase existing content to better match the job description
3. Highlight relevant skills and experience that align with the job requirements
4. Use keywords from the job description naturally throughout the resume
5. Maintain the candidate's authentic experience and qualifications
6. Ensure the resume remains truthful and accurate
7. KEEP ALL BULLET POINTS DETAILED AND COMPREHENSIVE - do not shorten or summarize them
8. Each experience bullet should be 1-5 lines long with specific details, metrics, and technologies
9. Aim for a FULL 1-2 PAGE resume - do not make it shorter than the original

BULLET POINT GUIDELINES:
- Each bullet should be detailed and specific (15-25 words minimum)
- **ALWAYS add quantifiable metrics and achievements** (percentages, numbers, time saved, users impacted, etc.)
- If metrics are not in the original, infer reasonable estimates based on the role and responsibilities
- Mention specific technologies, tools, and methodologies used
- Use strong action verbs (Developed, Architected, Optimized, Led, Implemented, Designed, etc.)
- Follow the STAR format: Action + Technology + Result/Impact
- Examples of good metrics:
  * "Reduced API response time by 40%" 
  * "Improved system throughput to handle 10,000 requests/second"
  * "Led team of 4 engineers"
  * "Deployed to 50,000+ users"
  * "Reduced deployment time from 2 hours to 15 minutes"
- Preserve all important details from the original resume
- DO NOT condense or summarize - maintain or expand detail level with metrics

JOB INFORMATION:
- Title: {job_title}
- Company: {company}

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_text}

TASK:
Analyze the resume and job description, then create an optimized version of the resume that:
1. Better highlights relevant experience and skills for this specific job
2. Incorporates important keywords from the job description naturally
3. Reorganizes content to emphasize the most relevant qualifications
4. Uses ONLY information from the original resume (no fabrication)
5. Maintains proper resume structure with clear sections
6. PRESERVES or EXPANDS the level of detail in bullet points - never shorten them
7. Ensures the resume is comprehensive and fills 1-2 pages appropriately
8. **ENHANCES every bullet point in Experience and Projects with specific metrics and quantifiable achievements**
9. **For Projects: Include technical details, technologies used, and measurable outcomes**
10. **For Experience: Emphasize impact, scale, and results with numbers**

SPECIAL FOCUS ON METRICS:
- Review each bullet point and add at least one quantifiable metric
- If the original lacks metrics, infer reasonable ones based on:
  * Team size (e.g., "Led team of X engineers")
  * Performance improvements (e.g., "Improved speed by X%")
  * Scale (e.g., "Serving X users", "Processing X requests/day")
  * Time savings (e.g., "Reduced time from X to Y")
  * Business impact (e.g., "Increased efficiency by X%")

Return a structured ResumeData object with all sections properly filled with detailed, comprehensive, metric-rich content."""

        try:
            print(f"\n{'='*60}")
            print(f"🤖 Starting Resume Tailoring")
            print(f"{'='*60}")
            print(f"Job: {job_title} at {company}")
            print(f"{'='*60}\n")
            
            response = self.client.responses.parse(
                model=self.model,
                instructions=(
                    "You are an expert resume tailoring specialist. "
                    "Return a structured result that matches the provided schema exactly."
                ),
                input=prompt_template,
                text_format=AgentTailoringResult,
                temperature=0.5,
                max_output_tokens=10000,
            )

            result = response.output_parsed
            if result is None:
                raise ValueError("OpenAI did not return structured resume tailoring output.")

            # Ensure plain text stays synchronized with structured resume.
            result.resume_text = result.resume.to_text()
            
            print(f"\n{'='*60}")
            print(f"✅ Resume Tailoring Complete")
            print(f"📊 Structured Resume Created:")
            print(f"   - Skills: {len(result.resume.skills)}")
            print(f"   - Experience Entries: {len(result.resume.experience)}")
            print(f"   - Education Entries: {len(result.resume.education)}")
            print(f"   - Projects: {len(result.resume.projects)}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"Resume tailoring failed: {str(e)}")
            raise
    
    def get_ats_score(self, resume_text: str, job_description: str) -> Dict[str, float]:
        """
        Get ATS score for a resume against a job description.
        Note: This is a placeholder - actual scoring would need to be implemented.
        """
        # For now, return a dummy score
        return {
            'overall_score': 75.0,
            'keyword_match': 70.0,
            'skills_match': 75.0,
            'experience_relevance': 80.0,
            'format_compatibility': 85.0
        }
