"""
Professional PDF resume generator using FPDF2 with LLM-based parsing.
"""
from fpdf import FPDF
import re
from typing import Dict, List, Optional
from resume_parser import LLMResumeParser, ResumeData


class ResumePDFGenerator:
    """Generate professionally formatted PDF resumes using FPDF2."""
    
    def __init__(self, use_llm_parser: bool = True, model: str = "gpt-4o-mini"):
        """
        Initialize PDF generator.
        
        Args:
            use_llm_parser: Whether to use LLM-based parsing (default: True)
            model: OpenAI model to use for parsing
        """
        self.use_llm_parser = use_llm_parser
        if use_llm_parser:
            try:
                self.parser = LLMResumeParser(model=model)
            except Exception:
                print("Warning: LLM parser not available, falling back to regex parsing")
                self.use_llm_parser = False
                self.parser = None
        else:
            self.parser = None
    
    def _clean_text(self, text: str) -> str:
        """Remove markdown formatting."""
        # Remove markdown
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_(?!_)([^_]+)_(?!_)', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        return text
    
    def _is_date_line(self, line: str) -> bool:
        """Check if line contains dates."""
        patterns = [
            r'\d{4}\s*[-–—]\s*\d{4}',
            r'\d{4}\s*[-–—]\s*(Present|Current)',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        ]
        return any(re.search(p, line, re.IGNORECASE) for p in patterns)
    
    def _parse_resume(self, text: str) -> Dict:
        """Parse resume into sections."""
        text = self._clean_text(text)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        section_keywords = {
            'SUMMARY': ['SUMMARY', 'OBJECTIVE', 'PROFILE', 'PROFESSIONAL SUMMARY'],
            'EXPERIENCE': ['EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE'],
            'EDUCATION': ['EDUCATION', 'ACADEMIC BACKGROUND'],
            'SKILLS': ['SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES'],
            'PROJECTS': ['PROJECTS', 'KEY PROJECTS'],
            'CERTIFICATIONS': ['CERTIFICATIONS', 'CERTIFICATES'],
        }
        
        result = {'name': '', 'contact': [], 'sections': {}}
        
        if lines:
            result['name'] = lines[0]
            lines = lines[1:]
        
        # Extract contact
        contact_lines = []
        section_start = 0
        for i, line in enumerate(lines[:5]):
            is_section = any(
                any(kw == line.upper() or kw in line.upper() for kw in keywords)
                for keywords in section_keywords.values()
            )
            if is_section:
                section_start = i
                break
            contact_lines.append(line)
        
        result['contact'] = contact_lines
        lines = lines[section_start:]
        
        # Parse sections
        current_section = None
        current_content = []
        
        for line in lines:
            is_section = False
            for key, keywords in section_keywords.items():
                if any(kw == line.upper() or (kw in line.upper() and len(line) < 50) for kw in keywords):
                    if current_section and current_content:
                        result['sections'][current_section] = current_content
                    current_section = key
                    current_content = []
                    is_section = True
                    break
            
            if not is_section and current_section:
                current_content.append(line)
        
        if current_section and current_content:
            result['sections'][current_section] = current_content
        
        return result
    
    def _parse_entries(self, lines: List[str]) -> List[Dict]:
        """Parse job/education entries."""
        entries = []
        current = {'title': None, 'company': None, 'date': None, 'bullets': []}
        
        for line in lines:
            if self._is_date_line(line):
                current['date'] = line
                continue
            
            if line.startswith(('•', '-', '*', '–', '—')):
                bullet = line[1:].strip()
                current['bullets'].append(bullet)
                continue
            
            # Check if new entry
            if current['title'] and len(line) < 100:
                if current['title'] or current['bullets']:
                    entries.append(current)
                current = {'title': None, 'company': None, 'date': None, 'bullets': []}
            
            if not current['title']:
                current['title'] = line
            elif not current['company']:
                current['company'] = line
        
        if current['title'] or current['bullets']:
            entries.append(current)
        
        return entries
    
    def _add_name(self, pdf: FPDF, name: str):
        """Add name header."""
        if not name:
            return
        name = ' '.join(str(name).split())
        pdf.set_font('Helvetica', 'B', 17)
        pdf.set_text_color(26, 26, 26)
        try:
            pdf.cell(0, 6, name, align='C', ln=True)
            pdf.ln(1)
        except:
            pass
    
    def _add_contact(self, pdf: FPDF, contact_info: dict):
        """Add contact information with clickable links."""
        if not contact_info:
            return
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(74, 74, 74)
        
        try:
            # Build contact parts
            parts = []
            
            # Email (clickable)
            if contact_info.get('email'):
                parts.append(('email', contact_info['email']))
            
            # Phone
            if contact_info.get('phone'):
                parts.append(('text', contact_info['phone']))
            
            # Location
            if contact_info.get('location'):
                parts.append(('text', contact_info['location']))
            
            # LinkedIn (clickable)
            if contact_info.get('linkedin'):
                parts.append(('link', contact_info['linkedin']))
            
            # GitHub (clickable)
            if contact_info.get('github'):
                parts.append(('link', contact_info['github']))
            
            if not parts:
                return
            
            # Calculate total width needed
            page_width = pdf.w
            left_margin = pdf.l_margin
            right_margin = pdf.r_margin
            available_width = page_width - left_margin - right_margin
            
            # Calculate width for each part
            separator = ' | '
            total_text = separator.join([p[1] for p in parts])
            
            # Center the contact line
            y_pos = pdf.get_y()
            
            # For simplicity, just create the text with separators
            # and add links for URLs
            contact_text = separator.join([p[1] for p in parts])
            
            # Add the text centered
            pdf.cell(available_width, 4, contact_text, align='C', ln=False)
            
            # Add clickable links on top of the text
            current_x = left_margin
            text_width = pdf.get_string_width(contact_text)
            start_x = left_margin + (available_width - text_width) / 2
            
            for i, (ptype, value) in enumerate(parts):
                if i > 0:
                    # Add separator width
                    sep_width = pdf.get_string_width(separator)
                    start_x += sep_width
                
                part_width = pdf.get_string_width(value)
                
                if ptype == 'email':
                    # Add mailto link
                    pdf.link(start_x, y_pos, part_width, 4, f'mailto:{value}')
                elif ptype == 'link':
                    # Add URL link
                    url = value if value.startswith('http') else f'https://{value}'
                    pdf.link(start_x, y_pos, part_width, 4, url)
                
                start_x += part_width
            
            pdf.ln(7)  # Move to next line with spacing
            
        except Exception as e:
            print(f"⚠️ Error adding contact info: {e}")
            # Fallback to simple text
            contact_text = ' | '.join(str(v) for v in contact_info.values() if v)
            pdf.cell(0, 4, contact_text, align='C', ln=True)
            pdf.ln(3)
    
    def _add_section_header(self, pdf: FPDF, title: str):
        """Add section header with underline."""
        if not title:
            return
        
        # Check if there's enough space for a new section
        page_height = pdf.h
        bottom_margin = pdf.b_margin
        current_y = pdf.get_y()
        
        if current_y > (page_height - bottom_margin - 30):
            print(f"⚠️ Skipping section '{title}' - not enough space (y={current_y:.1f})")
            return
            
        title = ' '.join(str(title).split())
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(44, 90, 160)
        try:
            pdf.ln(2)  # Increased from 1 to 2 for more spacing before section
            pdf.cell(0, 5, title, ln=True)
            pdf.set_draw_color(44, 90, 160)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)  # Increased from 1 to 2 for more spacing after section header
        except Exception as e:
            print(f"⚠️ Error adding section header '{title}': {e}")
            pass
    
    def _add_job_title(self, pdf: FPDF, title: str):
        """Add job/education title."""
        if not title:
            return
        
        # Check if there's enough space
        page_height = pdf.h
        bottom_margin = pdf.b_margin
        current_y = pdf.get_y()
        
        if current_y > (page_height - bottom_margin - 15):
            print(f"⚠️ Skipping job title '{title}' - not enough space (y={current_y:.1f})")
            return
            
        title = ' '.join(str(title).split())
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(26, 26, 26)
        try:
            pdf.multi_cell(0, 4, title)
        except Exception as e:
            print(f"⚠️ Error adding job title '{title}': {e}")
            pass
    
    def _add_company_date(self, pdf: FPDF, company: str, date: str):
        """Add company and date line with company left-aligned and date right-aligned."""
        print(f"\n📍 _add_company_date called:")
        print(f"   Company: '{company}'")
        print(f"   Date: '{date}'")
        
        company_text = ' '.join(str(company or '').split())
        date_text = ' '.join(str(date or '').split())
        
        print(f"   Company text: '{company_text}'")
        print(f"   Date text: '{date_text}'")

        if not company_text and not date_text:
            print(f"   ⚠️ Both company and date are empty, returning")
            return
        
        # Check if there's enough space on the page
        page_height = pdf.h
        bottom_margin = pdf.b_margin
        current_y = pdf.get_y()
        
        print(f"   Current Y: {current_y:.1f}mm")
        print(f"   Page height: {page_height:.1f}mm")
        print(f"   Bottom margin: {bottom_margin:.1f}mm")
        print(f"   Space available: {(page_height - bottom_margin - current_y):.1f}mm")
        
        # Check X position and margins
        current_x = pdf.get_x()
        left_margin = pdf.l_margin
        right_margin = pdf.r_margin
        page_width = pdf.w
        available_width = page_width - left_margin - right_margin
        
        print(f"   Current X: {current_x:.1f}mm")
        print(f"   Left margin: {left_margin:.1f}mm")
        print(f"   Right margin: {right_margin:.1f}mm")
        print(f"   Available width: {available_width:.1f}mm")
        
        # Reset X to left margin if it's off
        if current_x > left_margin + 1:  # Allow 1mm tolerance
            print(f"   ⚠️ X position off, resetting to left margin")
            pdf.set_x(left_margin)
            current_x = pdf.get_x()
            print(f"   New X: {current_x:.1f}mm")
        
        # Check if we need a page break before adding
        # FPDF sometimes has issues near page boundaries
        if current_y > (page_height - bottom_margin - 40):
            print(f"   🔄 Adding page break (within 40mm of bottom)")
            pdf.add_page()
            current_y = pdf.get_y()
            current_x = pdf.get_x()
            print(f"   New Y after page break: {current_y:.1f}mm")
            print(f"   New X after page break: {current_x:.1f}mm")
            
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(74, 74, 74)
        
        try:
            print(f"   ✅ Adding company_date to PDF with two cells...")
            
            # Save the Y position for alignment
            y_position = pdf.get_y()
            
            # Add company text (left-aligned)
            if company_text:
                pdf.set_xy(left_margin, y_position)
                # Use cell instead of multi_cell for single line
                # Width is 70% of available width for company
                company_width = available_width * 0.7
                pdf.cell(company_width, 4.5, company_text, align='L')  # Increased from 3.5 to 4.5
                print(f"      ✓ Added company (left-aligned): '{company_text}'")
            
            # Add date text (right-aligned)
            if date_text:
                # Position for right-aligned date
                pdf.set_xy(left_margin, y_position)
                # Use full width cell with right alignment
                pdf.cell(available_width, 4.5, date_text, align='R')  # Increased from 3.5 to 4.5
                print(f"      ✓ Added date (right-aligned): '{date_text}'")
            
            # Move to next line
            pdf.ln(4)
            
            print(f"   ✅ Successfully added company_date")
            print(f"   New Y position: {pdf.get_y():.1f}mm")
        except Exception as e:
            print(f"   ❌ Exception while adding company data:")
            print(f"      Error type: {type(e).__name__}")
            print(f"      Error message: {str(e)}")
            print(f"      Company: '{company_text}'")
            print(f"      Date: '{date_text}'")
            print(f"      Y position at error: {pdf.get_y():.1f}mm")
            print(f"      Skipping this element")
            # Continue without this element
            pass
    
    def _add_bullet(self, pdf: FPDF, text: str, is_gpa: bool = False):
        """Add bullet point with proper axis checking."""
        print(f"\n📍 _add_bullet called:")
        print(f"   Text: '{text[:50]}...' (length: {len(text) if text else 0})")
        print(f"   Is GPA: {is_gpa}")
        
        # Clean and validate text
        if not text or not isinstance(text, str):
            print(f"   ⚠️ Invalid text, returning")
            return
        
        # Remove any problematic characters and excessive whitespace
        text = ' '.join(text.split())
        
        # Check vertical space
        page_height = pdf.h
        bottom_margin = pdf.b_margin
        current_y = pdf.get_y()
        
        print(f"   Current Y: {current_y:.1f}mm")
        print(f"   Page height: {page_height:.1f}mm")
        print(f"   Space available: {(page_height - bottom_margin - current_y):.1f}mm")
        
        # Check if we need a page break
        if current_y > (page_height - bottom_margin - 40):
            print(f"   🔄 Adding page break before bullet")
            pdf.add_page()
            current_y = pdf.get_y()
            print(f"   New Y after page break: {current_y:.1f}mm")
        
        # Check horizontal position
        current_x = pdf.get_x()
        left_margin = pdf.l_margin
        right_margin = pdf.r_margin
        page_width = pdf.w
        available_width = page_width - left_margin - right_margin
        
        print(f"   Current X: {current_x:.1f}mm")
        print(f"   Left margin: {left_margin:.1f}mm")
        print(f"   Available width: {available_width:.1f}mm")
        
        # Reset X to left margin if needed
        if current_x > left_margin + 1:
            print(f"   ⚠️ X position off, resetting to left margin")
            pdf.set_x(left_margin)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(26, 26, 26)
        
        try:
            if is_gpa:
                # Right-aligned for GPA
                print(f"   ✅ Adding GPA (right-aligned)...")
                pdf.cell(available_width, 3.5, text, align='R', ln=True)
                print(f"   ✅ GPA added successfully")
            else:
                # Bullet point with text
                print(f"   ✅ Adding bullet point...")
                
                # Save Y position
                y_pos = pdf.get_y()
                
                # Add bullet character (use simple hyphen for ASCII compatibility)
                pdf.set_xy(left_margin, y_pos)
                pdf.cell(5, 4.5, '-', ln=False)  # Increased line height from 3.5 to 4.5
                
                # Add text with indentation and better spacing
                pdf.set_xy(left_margin + 5, y_pos)
                text_width = available_width - 5
                
                # Use cell for single line or multi_cell for wrapping with increased line height
                if len(text) < 80:  # Approximate single line
                    pdf.cell(text_width, 4.5, text, ln=True)  # Increased line height
                else:
                    pdf.multi_cell(text_width, 4.5, text)  # Increased line height
                
                print(f"   ✅ Bullet added successfully")
            
            print(f"   New Y position: {pdf.get_y():.1f}mm")
            
        except Exception as e:
            print(f"   ❌ Exception while adding bullet:")
            print(f"      Error type: {type(e).__name__}")
            print(f"      Error message: {str(e)}")
            print(f"      Text: '{text[:50]}...'")
            print(f"      Skipping this bullet")
            pass
    
    def _add_body_text(self, pdf: FPDF, text: str):
        """Add body text with proper axis checking."""
        if not text or not isinstance(text, str):
            return
        
        # Clean text
        text = ' '.join(text.split())
        
        # Check vertical space
        page_height = pdf.h
        bottom_margin = pdf.b_margin
        current_y = pdf.get_y()
        
        # Check horizontal position
        current_x = pdf.get_x()
        left_margin = pdf.l_margin
        right_margin = pdf.r_margin
        page_width = pdf.w
        available_width = page_width - left_margin - right_margin
        
        # Reset X to left margin if needed
        if current_x > left_margin + 1:
            pdf.set_x(left_margin)
        
        # Check if we need a page break
        if current_y > (page_height - bottom_margin - 40):
            print(f"🔄 Adding page break before body text (y={current_y:.1f})")
            pdf.add_page()
            current_y = pdf.get_y()
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(26, 26, 26)
        
        try:
            # Use cell for short text, multi_cell for long text with better spacing
            if len(text) < 100:
                pdf.cell(available_width, 4.5, text, ln=True)  # Increased from 3.5 to 4.5
            else:
                pdf.multi_cell(available_width, 4.5, text)  # Increased from 3.5 to 4.5
        except Exception as e:
            print(f"⚠️ Error adding body text: {e}")
            print(f"   Text: '{text[:50]}...'")
            print(f"   Y: {current_y:.1f}, X: {current_x:.1f}")
            pass
    
    def generate_pdf(self, resume: ResumeData, job_title: str = None, company: str = None) -> bytes:
        """
        Generate single-page PDF resume from ResumeData.
        
        Args:
            resume: ResumeData Pydantic model with structured resume data
            job_title: Optional job title for header
            company: Optional company name for header
            
        Returns:
            PDF file as bytes
        """
        # Create PDF instance
        pdf = FPDF()
        # Enable auto page break to allow multi-page resumes if needed
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(left=12.7, top=12.7, right=12.7)  # 0.5 inch margins
        
        # Render using Pydantic model directly
        self._render_from_pydantic(pdf, resume)
        
        # Convert bytearray to bytes for compatibility
        return bytes(pdf.output())
    
    def _render_from_pydantic(self, pdf: FPDF, resume_data: ResumeData):
        """Render PDF using Pydantic ResumeData model."""
        # Name
        self._add_name(pdf, resume_data.contact.name)
        
        # Debug: Print the resume_data
        print("\n" + "="*60)
        print("📋 ResumeData Structure:")
        print("="*60)
        print(f"Contact: {resume_data.contact.name}")
        print(f"  Email: {resume_data.contact.email}")
        print(f"  Phone: {resume_data.contact.phone}")
        print(f"  Location: {resume_data.contact.location}")
        print(f"\nSummary: {resume_data.summary[:100] if resume_data.summary else 'None'}...")
        print(f"\nExperience Entries: {len(resume_data.experience)}")
        for i, exp in enumerate(resume_data.experience[:3], 1):
            print(f"  {i}. {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})")
        print(f"\nEducation Entries: {len(resume_data.education)}")
        for i, edu in enumerate(resume_data.education, 1):
            print(f"  {i}. {edu.degree} - {edu.institution}, {edu.location}, {edu.gpa}, {edu.start_date}, {edu.end_date}")
        print(f"\nSkills: {len(resume_data.skills)} total")
        print(f"  {', '.join(resume_data.skills[:10])}{'...' if len(resume_data.skills) > 10 else ''}")
        print(f"\nProjects: {len(resume_data.projects)}")
        print(f"Certifications: {len(resume_data.certifications)}")
        print("="*60 + "\n")
        
        # Contact info with clickable links
        contact_info = {
            'email': resume_data.contact.email,
            'phone': resume_data.contact.phone,
            'location': resume_data.contact.location,
            'linkedin': resume_data.contact.linkedin,
            'github': resume_data.contact.github
        }
        
        if any(contact_info.values()):
            self._add_contact(pdf, contact_info)
        
        # Summary
        if resume_data.summary:
            self._add_section_header(pdf, "SUMMARY")
            self._add_body_text(pdf, resume_data.summary)
            pdf.ln(1)
        
        # Experience
        if resume_data.experience:
            print(f"\n{'='*60}")
            print(f"💼 EXPERIENCE SECTION")
            print(f"{'='*60}")
            print(f"Number of experience entries: {len(resume_data.experience)}")
            
            self._add_section_header(pdf, "EXPERIENCE")
            
            for exp_idx, exp in enumerate(resume_data.experience, 1):
                print(f"\n--- Experience {exp_idx}/{len(resume_data.experience)} ---")
                print(f"Title: {exp.title}")
                print(f"Company: {exp.company}")
                print(f"Location: {exp.location}")
                print(f"Start Date: {exp.start_date}")
                print(f"End Date: {exp.end_date}")
                print(f"Number of bullets: {len(exp.bullets)}")
                
                if exp.title:
                    self._add_job_title(pdf, exp.title)
                
                company_date = exp.company or ""
                if exp.location:
                    company_date += f", {exp.location}"
                
                date_range = f"{exp.start_date or 'N/A'} - {exp.end_date or 'Present'}"
                
                if company_date or date_range:
                    print(f"Adding company_date: '{company_date}' | '{date_range}'")
                    self._add_company_date(pdf, company_date, date_range)
                    pdf.ln(1)  # Add 1 line spacing after company/date before bullets
                
                # Add bullets
                if exp.bullets:
                    print(f"Adding {len(exp.bullets)} bullets...")
                    for i, bullet in enumerate(exp.bullets, 1):
                        print(f"  Bullet {i}/{len(exp.bullets)}: {bullet[:60]}...")
                        self._add_bullet(pdf, bullet)
                else:
                    print(f"⚠️ No bullets for this experience entry")
                
                pdf.ln(2)  # Increased from 1 to 2 for extra spacing between experience entries
            
            print(f"{'='*60}")
            print(f"✅ Experience section complete")
            print(f"{'='*60}\n")
        
        # Education
        if resume_data.education:
            print(f"\n{'='*60}")
            print(f"🎓 EDUCATION SECTION")
            print(f"{'='*60}")
            print(f"Number of education entries: {len(resume_data.education)}")
            
            self._add_section_header(pdf, "EDUCATION")
            
            for edu_idx, edu in enumerate(resume_data.education, 1):
                print(f"\n--- Education {edu_idx}/{len(resume_data.education)} ---")
                print(f"Degree: {edu.degree}")
                print(f"Institution: {edu.institution}")
                print(f"Location: {edu.location}")
                print(f"Start Date: {edu.start_date}")
                print(f"End Date: {edu.end_date}")
                print(f"GPA: {edu.gpa}")
                print(f"Honors: {edu.honors}")
                
                if edu.degree:
                    self._add_job_title(pdf, edu.degree)
                
                institution = edu.institution or ""
                if edu.location:
                    institution += f", {edu.location}"
                
                print(f"Final institution text: '{institution}'")
                
                if institution or edu.end_date:
                    self._add_company_date(pdf, institution, edu.end_date or "Present")
                    pdf.ln(1)  # Add spacing after institution before GPA/honors
                
                if edu.gpa:
                    self._add_bullet(pdf, f"GPA: {edu.gpa}", is_gpa=True)
                
                for honor in edu.honors:
                    self._add_bullet(pdf, honor)
                
                pdf.ln(1)
            
            print(f"{'='*60}")
            print(f"✅ Education section complete")
            print(f"{'='*60}\n")
        
        # Skills
        if resume_data.skills:
            self._add_section_header(pdf, "SKILLS")
            skills_text = ', '.join(resume_data.skills)
            self._add_body_text(pdf, skills_text)
            pdf.ln(1)
        
        # Projects
        if resume_data.projects:
            print(f"\n{'='*60}")
            print(f"📦 PROJECTS SECTION")
            print(f"{'='*60}")
            print(f"Number of projects: {len(resume_data.projects)}")
            
            self._add_section_header(pdf, "PROJECTS")
            
            for i, proj in enumerate(resume_data.projects, 1):
                print(f"\n--- Project {i}/{len(resume_data.projects)} ---")
                print(f"Title: {proj.title}")
                print(f"Date: {proj.date}")
                print(f"Description: {proj.description[:100] if proj.description else 'None'}...")
                print(f"Technologies: {proj.technologies}")
                print(f"Bullets: {len(proj.bullets)}")
                
                # Add project title with date on the same line
                if proj.title:
                    # Save Y position
                    y_pos = pdf.get_y()
                    
                    # Add title (left-aligned)
                    pdf.set_font('Helvetica', 'B', 11)
                    pdf.set_text_color(26, 26, 26)
                    pdf.cell(0, 4, proj.title, ln=False)
                    
                    # Add date on the same line (right-aligned)
                    if proj.date:
                        pdf.set_xy(pdf.l_margin, y_pos)
                        pdf.set_font('Helvetica', 'I', 10)
                        pdf.set_text_color(74, 74, 74)
                        available_width = pdf.w - pdf.l_margin - pdf.r_margin
                        pdf.cell(available_width, 4, proj.date, align='R', ln=True)
                    else:
                        pdf.ln()  # Just move to next line if no date
                
                # Reset X position to left margin after title/date line
                pdf.set_x(pdf.l_margin)
                
                # Add spacing before bullets
                pdf.ln(1)
                
                # Skip description and technologies - only show bullets
                # Add bullets (they handle their own positioning)
                if proj.bullets:
                    for j, bullet in enumerate(proj.bullets, 1):
                        print(f"Adding project bullet {j}/{len(proj.bullets)}")
                        self._add_bullet(pdf, bullet)
                else:
                    print(f"⚠️ No bullets for this project")
                
                pdf.ln(1)
            
            print(f"{'='*60}")
            print(f"✅ Projects section complete")
            print(f"{'='*60}\n")
        
        # Certifications
        if resume_data.certifications:
            self._add_section_header(pdf, "CERTIFICATIONS")
            for cert in resume_data.certifications:
                cert_text = f"{cert.name} - {cert.issuer}"
                if cert.date:
                    cert_text += f" ({cert.date})"
                self._add_bullet(pdf, cert_text)
            pdf.ln(1)
    
    def _render_from_legacy(self, pdf: FPDF, data: dict):
        """Render PDF using legacy dictionary format."""
        # Name
        if data['name']:
            self._add_name(pdf, data['name'])
        
        # Contact
        if data['contact']:
            self._add_contact(pdf, data['contact'])
        
        # Sections
        section_order = ['SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'CERTIFICATIONS']
        
        for section_name in section_order:
            if section_name not in data['sections']:
                continue
            
            content = data['sections'][section_name]
            
            # Section heading
            self._add_section_header(pdf, section_name)
            
            if section_name in ['EXPERIENCE', 'PROJECTS', 'EDUCATION']:
                entries = self._parse_entries(content)
                
                for entry in entries:
                    if entry['title']:
                        self._add_job_title(pdf, entry['title'])
                    
                    if entry['company'] or entry['date']:
                        self._add_company_date(pdf, entry['company'], entry['date'])
                    
                    # Handle bullets
                    for bullet in entry['bullets']:
                        is_gpa = section_name == 'EDUCATION' and re.search(
                            r'\bGPA\b|Grade Point Average', bullet, re.IGNORECASE
                        )
                        self._add_bullet(pdf, bullet, is_gpa)
                    
                    pdf.ln(1)
            
            elif section_name == 'SKILLS':
                full_text = ' '.join(content)
                if ',' in full_text:
                    self._add_body_text(pdf, full_text)
                else:
                    for line in content:
                        if line.startswith(('•', '-', '*')):
                            line = line[1:].strip()
                        self._add_bullet(pdf, line)
                
                pdf.ln(1)
            
            else:
                for line in content:
                    if line.startswith(('•', '-', '*')):
                        line = line[1:].strip()
                        self._add_bullet(pdf, line)
                    else:
                        self._add_body_text(pdf, line)
                
                pdf.ln(1)
