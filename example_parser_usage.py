"""
Example usage of the LLM-based resume parser with Pydantic models.
"""
from resume_parser import LLMResumeParser, ResumeData
from pdf_generator import ResumePDFGenerator
import json


def example_parse_resume():
    """Example: Parse a resume and display structured data."""
    
    sample_resume = """
John Doe
john.doe@email.com | (555) 123-4567 | San Francisco, CA | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years in full-stack development, specializing in Python and cloud technologies.

EXPERIENCE

Senior Software Engineer
TechCorp Inc., San Francisco, CA
Jan 2021 - Present
• Led development of microservices architecture serving 1M+ users
• Reduced API response time by 40% through optimization
• Mentored team of 5 junior engineers

Software Engineer
StartupXYZ, Remote
Jun 2019 - Dec 2020
• Built RESTful APIs using Python/Django and PostgreSQL
• Implemented CI/CD pipelines with GitHub Actions
• Collaborated with cross-functional teams on product features

EDUCATION

Bachelor of Science in Computer Science
University of California, Berkeley
Aug 2015 - May 2019
GPA: 3.8/4.0
Honors: Dean's List, Summa Cum Laude

SKILLS
Python, JavaScript, React, Django, Flask, PostgreSQL, MongoDB, AWS, Docker, Kubernetes, Git, CI/CD

PROJECTS

E-commerce Platform
Jan 2023 - Mar 2023
• Built full-stack e-commerce application with React and Django
• Integrated Stripe payment processing
• Technologies: React, Django, PostgreSQL, Redis, AWS

CERTIFICATIONS
AWS Certified Solutions Architect - Amazon Web Services - 2022
"""
    
    # Initialize parser
    parser = LLMResumeParser(model="gpt-4o-mini")
    
    if not parser.available:
        print("❌ OpenAI API key not configured. Set OPENAI_API_KEY and try again.")
        return
    
    print("🔍 Parsing resume with LLM...")
    
    try:
        # Parse resume
        resume_data = parser.parse_resume(sample_resume)
        
        # Display structured data
        print("\n✅ Resume parsed successfully!\n")
        
        print("=" * 60)
        print("CONTACT INFORMATION")
        print("=" * 60)
        print(f"Name: {resume_data.contact.name}")
        print(f"Email: {resume_data.contact.email}")
        print(f"Phone: {resume_data.contact.phone}")
        print(f"Location: {resume_data.contact.location}")
        print(f"LinkedIn: {resume_data.contact.linkedin}")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(resume_data.summary)
        
        print("\n" + "=" * 60)
        print(f"EXPERIENCE ({len(resume_data.experience)} entries)")
        print("=" * 60)
        for i, exp in enumerate(resume_data.experience, 1):
            print(f"\n{i}. {exp.title} at {exp.company}")
            print(f"   {exp.start_date} - {exp.end_date}")
            print(f"   Achievements: {len(exp.bullets)} bullets")
        
        print("\n" + "=" * 60)
        print(f"EDUCATION ({len(resume_data.education)} entries)")
        print("=" * 60)
        for edu in resume_data.education:
            print(f"• {edu.degree}")
            print(f"  {edu.institution} - {edu.end_date}")
            if edu.gpa:
                print(f"  GPA: {edu.gpa}")
        
        print("\n" + "=" * 60)
        print(f"SKILLS ({len(resume_data.skills)} skills)")
        print("=" * 60)
        print(", ".join(resume_data.skills))
        
        print("\n" + "=" * 60)
        print(f"PROJECTS ({len(resume_data.projects)} projects)")
        print("=" * 60)
        for proj in resume_data.projects:
            print(f"• {proj.title}")
            if proj.technologies:
                print(f"  Tech: {', '.join(proj.technologies)}")
        
        print("\n" + "=" * 60)
        print(f"CERTIFICATIONS ({len(resume_data.certifications)} certs)")
        print("=" * 60)
        for cert in resume_data.certifications:
            print(f"• {cert.name} - {cert.issuer}")
        
        # Export as JSON
        print("\n" + "=" * 60)
        print("JSON EXPORT")
        print("=" * 60)
        json_output = resume_data.model_dump_json(indent=2)
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
        
        # Save to file
        with open("parsed_resume.json", "w") as f:
            f.write(json_output)
        print("\n💾 Full JSON saved to: parsed_resume.json")
        
    except Exception as e:
        print(f"❌ Error parsing resume: {e}")


def example_generate_pdf_with_llm():
    """Example: Generate PDF using LLM parser."""
    
    sample_resume = """
Jane Smith
jane.smith@email.com | (555) 987-6543 | New York, NY

SUMMARY
Data scientist with expertise in machine learning and statistical analysis.

EXPERIENCE

Data Scientist
DataCorp, New York, NY
2022 - Present
• Developed ML models improving prediction accuracy by 25%
• Built data pipelines processing 10TB+ daily

EDUCATION

Master of Science in Data Science
MIT
2020 - 2022
GPA: 3.9/4.0

SKILLS
Python, R, TensorFlow, PyTorch, SQL, Tableau
"""
    
    print("📄 Generating PDF with LLM-based parsing...")
    
    try:
        # Create generator with LLM parsing enabled
        generator = ResumePDFGenerator(use_llm_parser=True, model="gpt-4o-mini")
        
        # Generate PDF
        pdf_bytes = generator.generate_pdf(sample_resume)
        
        # Save to file
        with open("resume_llm_parsed.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        print("✅ PDF generated successfully!")
        print("💾 Saved to: resume_llm_parsed.pdf")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")


def example_compare_parsers():
    """Example: Compare LLM vs regex parsing."""
    
    sample_resume = """
Alex Johnson
alex@email.com | 555-1234

EXPERIENCE
Software Developer
TechCo
2020-2023
• Built web applications
• Improved performance

SKILLS
Python, JavaScript, React
"""
    
    print("🔬 Comparing LLM vs Regex parsing...\n")
    
    # LLM parsing
    print("1️⃣ LLM-based parsing:")
    try:
        parser = LLMResumeParser()
        if parser.available:
            resume_data = parser.parse_resume(sample_resume)
            print(f"   ✅ Extracted {len(resume_data.experience)} experience entries")
            print(f"   ✅ Extracted {len(resume_data.skills)} skills")
            print(f"   ✅ Contact: {resume_data.contact.name}")
        else:
            print("   ⚠️ OpenAI API not available")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Regex parsing
    print("\n2️⃣ Regex-based parsing:")
    try:
        generator = ResumePDFGenerator(use_llm_parser=False)
        data = generator._parse_resume(sample_resume)
        print(f"   ✅ Name: {data['name']}")
        print(f"   ✅ Sections: {list(data['sections'].keys())}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 LLM Resume Parser Examples\n")
    
    # Run examples
    print("=" * 60)
    print("EXAMPLE 1: Parse and display structured data")
    print("=" * 60)
    example_parse_resume()
    
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: Generate PDF with LLM parsing")
    print("=" * 60)
    example_generate_pdf_with_llm()
    
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: Compare parsing methods")
    print("=" * 60)
    example_compare_parsers()
    
    print("\n\n✨ All examples completed!")
