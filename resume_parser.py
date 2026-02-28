"""
LLM-based resume parser using Pydantic models and OpenAI structured outputs.
"""
import json
import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI


class ContactInfo(BaseModel):
    """Contact information model."""
    name: str = Field(description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City, State or location")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL or username")
    github: Optional[str] = Field(None, description="GitHub profile URL or username")
    website: Optional[str] = Field(None, description="Personal website or portfolio URL")


class ExperienceEntry(BaseModel):
    """Work experience entry model."""
    title: Optional[str] = Field(None, description="Job title or position")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    start_date: Optional[str] = Field(None, description="Start date (e.g., 'Jan 2020', '2020')")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    bullets: List[str] = Field(default_factory=list, description="List of achievements and responsibilities")


class EducationEntry(BaseModel):
    """Education entry model."""
    degree: Optional[str] = Field(None, description="Degree name (e.g., 'Bachelor of Science in Computer Science')")
    institution: Optional[str] = Field(None, description="School or university name")
    location: Optional[str] = Field(None, description="School location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="Graduation date or expected graduation")
    gpa: Optional[str] = Field(None, description="GPA if mentioned")
    honors: List[str] = Field(default_factory=list, description="Honors, awards, or relevant coursework")


class ProjectEntry(BaseModel):
    """Project entry model."""
    title: str = Field(description="Project name")
    description: Optional[str] = Field(None, description="Brief project description")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    bullets: List[str] = Field(default_factory=list, description="Project details and achievements")
    date: Optional[str] = Field(None, description="Project date or timeframe")


class CertificationEntry(BaseModel):
    """Certification entry model."""
    name: str = Field(description="Certification name")
    issuer: str = Field(description="Issuing organization")
    date: Optional[str] = Field(None, description="Date obtained")
    credential_id: Optional[str] = Field(None, description="Credential ID if available")


class ResumeData(BaseModel):
    """Complete resume data model."""
    contact: ContactInfo
    summary: Optional[str] = Field(None, description="Professional summary or objective")
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list, description="List of skills")
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    
    def to_text(self) -> str:
        """Convert structured resume to plain text format."""
        sections = []
        
        # Contact info
        contact_parts = [self.contact.name]
        if self.contact.email:
            contact_parts.append(self.contact.email)
        if self.contact.phone:
            contact_parts.append(self.contact.phone)
        if self.contact.location:
            contact_parts.append(self.contact.location)
        if self.contact.linkedin:
            contact_parts.append(f"LinkedIn: {self.contact.linkedin}")
        if self.contact.github:
            contact_parts.append(f"GitHub: {self.contact.github}")
        if self.contact.website:
            contact_parts.append(self.contact.website)
        
        sections.append(" | ".join(contact_parts))
        
        # Summary
        if self.summary:
            sections.append("\nSUMMARY")
            sections.append(self.summary)
        
        # Experience
        if self.experience:
            sections.append("\nEXPERIENCE")
            for exp in self.experience:
                if exp.title:
                    sections.append(f"\n{exp.title}")
                if exp.company:
                    company_line = exp.company
                    if exp.location:
                        company_line += f", {exp.location}"
                    if exp.start_date or exp.end_date:
                        date_range = f"{exp.start_date or ''} - {exp.end_date or 'Present'}"
                        company_line += f" | {date_range}"
                    sections.append(company_line)
                for bullet in exp.bullets:
                    sections.append(f"- {bullet}")
        
        # Education
        if self.education:
            sections.append("\nEDUCATION")
            for edu in self.education:
                if edu.degree:
                    sections.append(f"\n{edu.degree}")
                if edu.institution:
                    edu_line = edu.institution
                    if edu.location:
                        edu_line += f", {edu.location}"
                    if edu.end_date:
                        edu_line += f" | {edu.end_date}"
                    sections.append(edu_line)
                if edu.gpa:
                    sections.append(f"GPA: {edu.gpa}")
                for honor in edu.honors:
                    sections.append(f"- {honor}")
        
        # Skills
        if self.skills:
            sections.append("\nSKILLS")
            sections.append(", ".join(self.skills))
        
        # Projects
        if self.projects:
            sections.append("\nPROJECTS")
            for proj in self.projects:
                proj_line = proj.title
                if proj.date:
                    proj_line += f" | {proj.date}"
                sections.append(f"\n{proj_line}")
                if proj.description:
                    sections.append(proj.description)
                if proj.technologies:
                    sections.append(f"Technologies: {', '.join(proj.technologies)}")
                for bullet in proj.bullets:
                    sections.append(f"- {bullet}")
        
        # Certifications
        if self.certifications:
            sections.append("\nCERTIFICATIONS")
            for cert in self.certifications:
                cert_line = f"{cert.name} - {cert.issuer}"
                if cert.date:
                    cert_line += f" | {cert.date}"
                if cert.credential_id:
                    cert_line += f" (ID: {cert.credential_id})"
                sections.append(cert_line)
        
        return "\n".join(sections)


class LLMResumeParser:
    """Parse resumes using OpenAI structured output with Pydantic models."""
    
    def __init__(self, model: str = None, api_key: str = None):
        """
        Initialize the parser.
        
        Args:
            model: OpenAI model name (default: gpt-4o-mini or from env OPENAI_MODEL)
            api_key: OpenAI API key (default: from env OPENAI_API_KEY)
        """
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if OpenAI API key is available."""
        if not self.api_key:
            return False
        try:
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception:
            return False
    
    def _clean_json_response(self, text: str) -> str:
        """Extract and clean JSON from LLM response."""
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text
    
    def parse_resume(self, resume_text: str) -> ResumeData:
        """
        Parse resume text into structured data using OpenAI structured outputs.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            ResumeData object with parsed information
            
        Raises:
            ValueError: If OpenAI API key is not configured or parsing fails
        """
        if not self.available:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Extract structured resume information. "
                            "Preserve original date formats. "
                            "If information is missing, use null or empty arrays."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Extract contact info, summary, experience, education, skills, projects, and certifications "
                            f"from this resume text:\n\n{resume_text}"
                        ),
                    },
                ],
                text_format=ResumeData,
                temperature=0.1,
            )
            # Add log message to print the response
            print(f"OpenAI parse response: {response.model_dump_json(indent=2)}")
            parsed = response.output_parsed
            
            if parsed is None:
                raise ValueError("OpenAI did not return structured resume data.")
            return parsed
            
        except Exception as e:
            # Fallback: try with a more detailed prompt
            print(f"LLM parsing failed: {str(e)}. Using fallback parser.")
            return self._fallback_parse(resume_text)
    
    def _fallback_parse(self, resume_text: str) -> ResumeData:
        """
        Fallback parser using JSON-mode completion when structured parsing fails.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            ResumeData object with basic parsing
        """
        # Create a simpler prompt for fallback
        prompt_template = """Extract information from the following resume and return ONLY a valid JSON object with this structure:

{{
  "contact": {{
    "name": "Full Name",
    "email": "email@example.com or null",
    "phone": "phone number or null",
    "location": "city, state or null",
    "linkedin": "LinkedIn URL or null",
    "github": "GitHub URL or null",
    "website": "website URL or null"
  }},
  "summary": "professional summary text or null",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State or null",
      "start_date": "Start Date",
      "end_date": "End Date or Present",
      "bullets": ["achievement 1", "achievement 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "School Name",
      "location": "City, State or null",
      "start_date": "Start Date or null",
      "end_date": "Graduation Date or null",
      "gpa": "GPA or null",
      "honors": ["honor 1", "honor 2"]
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "projects": [
    {{
      "title": "Project Name",
      "description": "Brief description or null",
      "technologies": ["tech1", "tech2"],
      "bullets": ["detail 1", "detail 2"],
      "date": "Date or null"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "issuer": "Issuing Organization",
      "date": "Date or null",
      "credential_id": "ID or null"
    }}
  ]
}}

CRITICAL: Return ONLY the JSON object with actual extracted data. Do NOT return the schema. Do NOT include explanations.

RESUME TEXT:
{resume_text}

JSON:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Return only valid JSON. Do not include markdown fences or explanations.",
                    },
                    {"role": "user", "content": prompt_template.format(resume_text=resume_text)},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_content = response.choices[0].message.content or "{}"
            cleaned_json = self._clean_json_response(raw_content)
            return ResumeData.model_validate(json.loads(cleaned_json))
            
        except Exception as e2:
            print(f"Fallback parsing also failed: {str(e2)}. Using regex parser.")
            return self._regex_fallback_parse(resume_text)
    
    def _regex_fallback_parse(self, resume_text: str) -> ResumeData:
        """
        Fallback parser using simpler regex-based extraction.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            ResumeData object with basic parsed information
        """
        lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
        
        # Extract name (first line)
        name = lines[0] if lines else "Unknown"
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
        email = email_match.group(0) if email_match else None
        
        # Extract phone
        phone_match = re.search(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', resume_text)
        phone = phone_match.group(0) if phone_match else None
        
        # Create basic contact info
        contact = ContactInfo(
            name=name,
            email=email,
            phone=phone
        )
        
        # Return minimal resume data
        return ResumeData(
            contact=contact,
            summary=None,
            experience=[],
            education=[],
            skills=[],
            projects=[],
            certifications=[]
        )
    
    def to_legacy_format(self, resume_data: ResumeData) -> dict:
        """
        Convert ResumeData to legacy format for backward compatibility.
        
        Args:
            resume_data: Parsed ResumeData object
            
        Returns:
            Dictionary in the old format used by PDF generator
        """
        contact_lines = []
        if resume_data.contact.email:
            contact_lines.append(resume_data.contact.email)
        if resume_data.contact.phone:
            contact_lines.append(resume_data.contact.phone)
        if resume_data.contact.location:
            contact_lines.append(resume_data.contact.location)
        if resume_data.contact.linkedin:
            contact_lines.append(resume_data.contact.linkedin)
        if resume_data.contact.github:
            contact_lines.append(resume_data.contact.github)
        
        sections = {}
        
        # Summary
        if resume_data.summary:
            sections['SUMMARY'] = [resume_data.summary]
        
        # Experience
        if resume_data.experience:
            exp_lines = []
            for exp in resume_data.experience:
                exp_lines.append(exp.title)
                company_date = f"{exp.company}"
                if exp.location:
                    company_date += f", {exp.location}"
                exp_lines.append(company_date)
                exp_lines.append(f"{exp.start_date} - {exp.end_date}")
                for bullet in exp.bullets:
                    exp_lines.append(f"• {bullet}")
            sections['EXPERIENCE'] = exp_lines
        
        # Education
        if resume_data.education:
            edu_lines = []
            for edu in resume_data.education:
                edu_lines.append(edu.degree)
                edu_lines.append(edu.institution)
                if edu.location:
                    edu_lines.append(edu.location)
                edu_lines.append(edu.end_date)
                if edu.gpa:
                    edu_lines.append(f"GPA: {edu.gpa}")
                for honor in edu.honors:
                    edu_lines.append(f"• {honor}")
            sections['EDUCATION'] = edu_lines
        
        # Skills
        if resume_data.skills:
            sections['SKILLS'] = [', '.join(resume_data.skills)]
        
        # Projects
        if resume_data.projects:
            proj_lines = []
            for proj in resume_data.projects:
                proj_lines.append(proj.title)
                if proj.date:
                    proj_lines.append(proj.date)
                if proj.description:
                    proj_lines.append(proj.description)
                if proj.technologies:
                    proj_lines.append(f"Technologies: {', '.join(proj.technologies)}")
                for bullet in proj.bullets:
                    proj_lines.append(f"• {bullet}")
            sections['PROJECTS'] = proj_lines
        
        # Certifications
        if resume_data.certifications:
            cert_lines = []
            for cert in resume_data.certifications:
                cert_line = f"{cert.name} - {cert.issuer}"
                if cert.date:
                    cert_line += f" ({cert.date})"
                cert_lines.append(cert_line)
            sections['CERTIFICATIONS'] = cert_lines
        
        return {
            'name': resume_data.contact.name,
            'contact': contact_lines,
            'sections': sections
        }
    
    def resume_data_to_text(self, resume_data: ResumeData) -> str:
        """
        Convert ResumeData object to formatted text string.
        
        Args:
            resume_data: ResumeData object
            
        Returns:
            Formatted resume text string
        """
        lines = []
        
        # Name
        lines.append(resume_data.contact.name)
        lines.append("")
        
        # Contact
        contact_parts = []
        if resume_data.contact.email:
            contact_parts.append(resume_data.contact.email)
        if resume_data.contact.phone:
            contact_parts.append(resume_data.contact.phone)
        if resume_data.contact.location:
            contact_parts.append(resume_data.contact.location)
        if resume_data.contact.linkedin:
            contact_parts.append(resume_data.contact.linkedin)
        if resume_data.contact.github:
            contact_parts.append(resume_data.contact.github)
        
        if contact_parts:
            lines.append(" | ".join(contact_parts))
            lines.append("")
        
        # Summary
        if resume_data.summary:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append(resume_data.summary)
            lines.append("")
        
        # Experience
        if resume_data.experience:
            lines.append("EXPERIENCE")
            for exp in resume_data.experience:
                if exp.title:
                    lines.append(exp.title)
                company_line = []
                if exp.company:
                    company_line.append(exp.company)
                if exp.location:
                    company_line.append(exp.location)
                if company_line:
                    lines.append(", ".join(company_line))
                if exp.start_date or exp.end_date:
                    lines.append(f"{exp.start_date or ''} - {exp.end_date or 'Present'}")
                for bullet in exp.bullets:
                    lines.append(f"• {bullet}")
                lines.append("")
        
        # Education
        if resume_data.education:
            lines.append("EDUCATION")
            for edu in resume_data.education:
                if edu.degree:
                    lines.append(edu.degree)
                if edu.institution:
                    inst_line = edu.institution
                    if edu.location:
                        inst_line += f", {edu.location}"
                    lines.append(inst_line)
                if edu.end_date:
                    lines.append(edu.end_date)
                if edu.gpa:
                    lines.append(f"GPA: {edu.gpa}")
                for honor in edu.honors:
                    lines.append(f"• {honor}")
                lines.append("")
        
        # Skills
        if resume_data.skills:
            lines.append("SKILLS")
            lines.append(", ".join(resume_data.skills))
            lines.append("")
        
        # Projects
        if resume_data.projects:
            lines.append("PROJECTS")
            for proj in resume_data.projects:
                title_line = proj.title
                if proj.date:
                    title_line += f" ({proj.date})"
                lines.append(title_line)
                if proj.description:
                    lines.append(proj.description)
                if proj.technologies:
                    lines.append(f"Technologies: {', '.join(proj.technologies)}")
                for bullet in proj.bullets:
                    lines.append(f"• {bullet}")
                lines.append("")
        
        # Certifications
        if resume_data.certifications:
            lines.append("CERTIFICATIONS")
            for cert in resume_data.certifications:
                cert_line = cert.name
                if cert.issuer:
                    cert_line += f" - {cert.issuer}"
                if cert.date:
                    cert_line += f" ({cert.date})"
                lines.append(cert_line)
            lines.append("")
        
        return "\n".join(lines)
