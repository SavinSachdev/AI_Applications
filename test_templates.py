"""
Test script to generate sample resumes with different templates.
"""
from html_pdf_generator import HTMLResumePDFGenerator
from resume_parser import ResumeData, ContactInfo, ExperienceEntry, EducationEntry, ProjectEntry, CertificationEntry
from pathlib import Path


def create_sample_resume() -> ResumeData:
    """Create a sample resume for testing."""
    contact = ContactInfo(
        name="John Doe",
        email="john.doe@example.com",
        phone="(555) 123-4567",
        location="San Francisco, CA",
        linkedin="linkedin.com/in/johndoe",
        github="github.com/johndoe"
    )
    
    experience = [
        ExperienceEntry(
            title="Senior Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            start_date="Jan 2020",
            end_date="Present",
            bullets=[
                "Led development of microservices architecture serving 1M+ daily active users, improving system reliability by 45%",
                "Architected and implemented real-time data pipeline processing 500K events/second using Kafka and Spark",
                "Mentored team of 5 junior engineers, establishing code review practices that reduced bug rate by 30%",
                "Optimized database queries reducing average API response time from 800ms to 120ms (85% improvement)"
            ]
        ),
        ExperienceEntry(
            title="Software Engineer",
            company="StartupXYZ",
            location="Remote",
            start_date="Jun 2018",
            end_date="Dec 2019",
            bullets=[
                "Developed RESTful APIs using Python/Flask serving 100K+ requests per day with 99.9% uptime",
                "Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes using Jenkins and Docker",
                "Built automated testing framework increasing code coverage from 40% to 85%",
                "Collaborated with product team to deliver 15+ features across 3 major product releases"
            ]
        )
    ]
    
    education = [
        EducationEntry(
            degree="Bachelor of Science in Computer Science",
            institution="University of California",
            location="Berkeley, CA",
            start_date="2014",
            end_date="2018",
            gpa="3.8/4.0",
            honors=["Dean's List (6 semesters)", "Graduated with Honors"]
        )
    ]
    
    skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
        "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "Redis",
        "Kafka", "Spark", "Git", "CI/CD", "Agile/Scrum"
    ]
    
    projects = [
        ProjectEntry(
            title="Open Source ML Framework",
            date="2023",
            description="",
            technologies=[],
            bullets=[
                "Developed machine learning framework with 2K+ GitHub stars, enabling faster model training by 40%",
                "Implemented distributed training support using Ray, scaling to 100+ GPUs across multiple nodes",
                "Created comprehensive documentation and tutorials adopted by 500+ developers worldwide"
            ]
        ),
        ProjectEntry(
            title="Real-time Analytics Dashboard",
            date="2022",
            description="",
            technologies=[],
            bullets=[
                "Built interactive dashboard using React and D3.js visualizing 10M+ data points in real-time",
                "Integrated WebSocket connections for live data updates with sub-second latency",
                "Deployed on AWS using ECS, handling 50K concurrent users during peak traffic"
            ]
        )
    ]
    
    certifications = [
        CertificationEntry(
            name="AWS Certified Solutions Architect",
            issuer="Amazon Web Services",
            date="2022"
        ),
        CertificationEntry(
            name="Certified Kubernetes Administrator",
            issuer="CNCF",
            date="2021"
        )
    ]
    
    return ResumeData(
        contact=contact,
        summary="Results-driven Senior Software Engineer with 5+ years of experience building scalable distributed systems and leading high-performing engineering teams. Proven track record of delivering complex projects that serve millions of users while maintaining 99.9% uptime. Expert in cloud architecture, microservices, and modern development practices. Passionate about mentoring engineers and driving technical excellence.",
        experience=experience,
        education=education,
        skills=skills,
        projects=projects,
        certifications=certifications
    )


def main():
    """Generate sample resumes with all available templates."""
    print("🎨 Generating sample resumes with different templates...\n")
    
    # Create sample resume
    resume = create_sample_resume()
    
    # Output directory
    output_dir = Path(__file__).parent / "sample_resumes"
    output_dir.mkdir(exist_ok=True)
    
    # Generate PDF for each template
    templates = HTMLResumePDFGenerator.list_templates()
    
    for template_name in templates:
        print(f"📄 Generating {template_name} template...")
        
        try:
            generator = HTMLResumePDFGenerator(template_name=template_name)
            pdf_bytes = generator.generate_pdf(resume)
            
            # Save PDF
            output_path = output_dir / f"sample_resume_{template_name}.pdf"
            output_path.write_bytes(pdf_bytes)
            
            print(f"   ✅ Saved to: {output_path}")
            
            # Also save HTML for preview
            html_content = generator.generate_html(resume)
            html_path = output_dir / f"sample_resume_{template_name}.html"
            html_path.write_text(html_content, encoding='utf-8')
            
            print(f"   ✅ HTML preview: {html_path}")
            
        except Exception as e:
            import traceback
            print(f"   ❌ Error: {e}")
            print(f"   Full traceback:")
            traceback.print_exc()
        
        print()
    
    print(f"✨ Done! Check the '{output_dir}' directory for generated resumes.")
    print(f"\n📋 Available templates: {', '.join(templates)}")
    print("\nYou can now use these templates in your app by specifying:")
    print("   HTMLResumePDFGenerator(template_name='modern')  # or 'professional' or 'minimal'")


if __name__ == "__main__":
    main()
