import streamlit as st
from typing import Optional
from resume_parser import ResumeData, ContactInfo, ExperienceEntry, EducationEntry, ProjectEntry, CertificationEntry


def render_resume_form(pre_populated_data: Optional[ResumeData] = None) -> Optional[ResumeData]:
    """
    Render an interactive form for manual resume entry.
    
    Args:
        pre_populated_data: Optional ResumeData to pre-populate the form
        
    Returns:
        ResumeData object if form is submitted, None otherwise
    """
    
    st.markdown("### 📝 Manual Resume Entry")
    st.info("💡 Fill out the form below. You can edit any pre-populated data from your uploaded resume.")
    
    with st.form("resume_form"):
        # Contact Information
        st.subheader("👤 Contact Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Full Name *",
                value=pre_populated_data.contact.name if pre_populated_data else "",
                placeholder="John Doe"
            )
            email = st.text_input(
                "Email *",
                value=pre_populated_data.contact.email if pre_populated_data else "",
                placeholder="john.doe@email.com"
            )
            phone = st.text_input(
                "Phone",
                value=pre_populated_data.contact.phone if pre_populated_data else "",
                placeholder="+1 (555) 123-4567"
            )
        
        with col2:
            location = st.text_input(
                "Location",
                value=pre_populated_data.contact.location if pre_populated_data else "",
                placeholder="San Francisco, CA"
            )
            linkedin = st.text_input(
                "LinkedIn",
                value=pre_populated_data.contact.linkedin if pre_populated_data else "",
                placeholder="linkedin.com/in/johndoe"
            )
            github = st.text_input(
                "GitHub",
                value=pre_populated_data.contact.github if pre_populated_data else "",
                placeholder="github.com/johndoe"
            )
        
        # Summary
        st.subheader("📄 Professional Summary")
        summary = st.text_area(
            "Summary",
            value=pre_populated_data.summary if pre_populated_data else "",
            height=100,
            placeholder="Brief professional summary highlighting your key qualifications..."
        )
        
        # Experience
        st.subheader("💼 Work Experience")
        num_experience = st.number_input(
            "Number of Experience Entries",
            min_value=0,
            max_value=10,
            value=len(pre_populated_data.experience) if pre_populated_data else 1
        )
        
        experience_entries = []
        for i in range(int(num_experience)):
            with st.expander(f"Experience #{i+1}", expanded=(i == 0)):
                exp_data = pre_populated_data.experience[i] if pre_populated_data and i < len(pre_populated_data.experience) else None
                
                exp_col1, exp_col2 = st.columns(2)
                with exp_col1:
                    exp_title = st.text_input(
                        "Job Title",
                        value=exp_data.title if exp_data else "",
                        key=f"exp_title_{i}",
                        placeholder="Software Engineer"
                    )
                    exp_company = st.text_input(
                        "Company",
                        value=exp_data.company if exp_data else "",
                        key=f"exp_company_{i}",
                        placeholder="Tech Corp"
                    )
                    exp_location = st.text_input(
                        "Location",
                        value=exp_data.location if exp_data else "",
                        key=f"exp_location_{i}",
                        placeholder="San Francisco, CA"
                    )
                
                with exp_col2:
                    exp_start = st.text_input(
                        "Start Date",
                        value=exp_data.start_date if exp_data else "",
                        key=f"exp_start_{i}",
                        placeholder="Jan 2022"
                    )
                    exp_end = st.text_input(
                        "End Date",
                        value=exp_data.end_date if exp_data else "",
                        key=f"exp_end_{i}",
                        placeholder="Present"
                    )
                
                # Bullets
                bullets_text = st.text_area(
                    "Bullet Points (one per line)",
                    value="\n".join(exp_data.bullets) if exp_data else "",
                    key=f"exp_bullets_{i}",
                    height=150,
                    placeholder="- Developed microservices architecture\n- Led team of 4 engineers\n- Improved performance by 40%"
                )
                
                bullets = [b.strip().lstrip('-').strip() for b in bullets_text.split('\n') if b.strip()]
                
                if exp_title or exp_company:
                    experience_entries.append(ExperienceEntry(
                        title=exp_title,
                        company=exp_company,
                        location=exp_location,
                        start_date=exp_start,
                        end_date=exp_end,
                        bullets=bullets
                    ))
        
        # Education
        st.subheader("🎓 Education")
        num_education = st.number_input(
            "Number of Education Entries",
            min_value=0,
            max_value=5,
            value=len(pre_populated_data.education) if pre_populated_data else 1
        )
        
        education_entries = []
        for i in range(int(num_education)):
            with st.expander(f"Education #{i+1}", expanded=(i == 0)):
                edu_data = pre_populated_data.education[i] if pre_populated_data and i < len(pre_populated_data.education) else None
                
                edu_col1, edu_col2 = st.columns(2)
                with edu_col1:
                    edu_degree = st.text_input(
                        "Degree",
                        value=edu_data.degree if edu_data else "",
                        key=f"edu_degree_{i}",
                        placeholder="Bachelor of Science in Computer Science"
                    )
                    edu_institution = st.text_input(
                        "Institution",
                        value=edu_data.institution if edu_data else "",
                        key=f"edu_institution_{i}",
                        placeholder="University Name"
                    )
                    edu_location = st.text_input(
                        "Location",
                        value=edu_data.location if edu_data else "",
                        key=f"edu_location_{i}",
                        placeholder="City, State"
                    )
                
                with edu_col2:
                    edu_start = st.text_input(
                        "Start Date",
                        value=edu_data.start_date if edu_data else "",
                        key=f"edu_start_{i}",
                        placeholder="Aug 2018"
                    )
                    edu_end = st.text_input(
                        "End Date",
                        value=edu_data.end_date if edu_data else "",
                        key=f"edu_end_{i}",
                        placeholder="May 2022"
                    )
                    edu_gpa = st.text_input(
                        "GPA",
                        value=edu_data.gpa if edu_data else "",
                        key=f"edu_gpa_{i}",
                        placeholder="3.8/4.0"
                    )
                
                honors_text = st.text_area(
                    "Honors/Awards (one per line)",
                    value="\n".join(edu_data.honors) if edu_data else "",
                    key=f"edu_honors_{i}",
                    height=80,
                    placeholder="Dean's List\nSumma Cum Laude"
                )
                
                honors = [h.strip() for h in honors_text.split('\n') if h.strip()]
                
                if edu_degree or edu_institution:
                    education_entries.append(EducationEntry(
                        degree=edu_degree,
                        institution=edu_institution,
                        location=edu_location,
                        start_date=edu_start,
                        end_date=edu_end,
                        gpa=edu_gpa,
                        honors=honors
                    ))
        
        # Skills
        st.subheader("🛠️ Skills")
        skills_text = st.text_area(
            "Skills (comma-separated)",
            value=", ".join(pre_populated_data.skills) if pre_populated_data else "",
            height=100,
            placeholder="Python, JavaScript, React, Node.js, Docker, AWS, PostgreSQL"
        )
        skills = [s.strip() for s in skills_text.split(',') if s.strip()]
        
        # Projects
        st.subheader("📦 Projects")
        num_projects = st.number_input(
            "Number of Projects",
            min_value=0,
            max_value=10,
            value=len(pre_populated_data.projects) if pre_populated_data else 0
        )
        
        project_entries = []
        for i in range(int(num_projects)):
            with st.expander(f"Project #{i+1}", expanded=False):
                proj_data = pre_populated_data.projects[i] if pre_populated_data and i < len(pre_populated_data.projects) else None
                
                proj_col1, proj_col2 = st.columns(2)
                with proj_col1:
                    proj_title = st.text_input(
                        "Project Title",
                        value=proj_data.title if proj_data else "",
                        key=f"proj_title_{i}",
                        placeholder="E-commerce Platform"
                    )
                with proj_col2:
                    proj_date = st.text_input(
                        "Date",
                        value=proj_data.date if proj_data else "",
                        key=f"proj_date_{i}",
                        placeholder="Jan 2023 - Mar 2023"
                    )
                
                proj_desc = st.text_area(
                    "Description",
                    value=proj_data.description if proj_data else "",
                    key=f"proj_desc_{i}",
                    height=60,
                    placeholder="Brief project description..."
                )
                
                proj_tech = st.text_input(
                    "Technologies (comma-separated)",
                    value=", ".join(proj_data.technologies) if proj_data else "",
                    key=f"proj_tech_{i}",
                    placeholder="React, Node.js, MongoDB"
                )
                
                proj_bullets_text = st.text_area(
                    "Bullet Points (one per line)",
                    value="\n".join(proj_data.bullets) if proj_data else "",
                    key=f"proj_bullets_{i}",
                    height=100,
                    placeholder="- Implemented user authentication\n- Built RESTful API"
                )
                
                proj_bullets = [b.strip().lstrip('-').strip() for b in proj_bullets_text.split('\n') if b.strip()]
                proj_technologies = [t.strip() for t in proj_tech.split(',') if t.strip()]
                
                if proj_title:
                    project_entries.append(ProjectEntry(
                        title=proj_title,
                        date=proj_date,
                        description=proj_desc,
                        technologies=proj_technologies,
                        bullets=proj_bullets
                    ))
        
        # Certifications
        st.subheader("🏆 Certifications")
        num_certs = st.number_input(
            "Number of Certifications",
            min_value=0,
            max_value=10,
            value=len(pre_populated_data.certifications) if pre_populated_data else 0
        )
        
        certification_entries = []
        for i in range(int(num_certs)):
            cert_data = pre_populated_data.certifications[i] if pre_populated_data and i < len(pre_populated_data.certifications) else None
            
            cert_col1, cert_col2, cert_col3 = st.columns(3)
            with cert_col1:
                cert_name = st.text_input(
                    "Certification Name",
                    value=cert_data.name if cert_data else "",
                    key=f"cert_name_{i}",
                    placeholder="AWS Certified Solutions Architect"
                )
            with cert_col2:
                cert_issuer = st.text_input(
                    "Issuer",
                    value=cert_data.issuer if cert_data else "",
                    key=f"cert_issuer_{i}",
                    placeholder="Amazon Web Services"
                )
            with cert_col3:
                cert_date = st.text_input(
                    "Date",
                    value=cert_data.date if cert_data else "",
                    key=f"cert_date_{i}",
                    placeholder="Jan 2023"
                )
            
            if cert_name:
                certification_entries.append(CertificationEntry(
                    name=cert_name,
                    issuer=cert_issuer,
                    date=cert_date
                ))
        
        # Submit button
        st.divider()
        submitted = st.form_submit_button("✅ Save Resume Data", use_container_width=True, type="primary")
        
        if submitted:
            if not name or not email:
                st.error("❌ Name and Email are required!")
                return None
            
            # Create ResumeData object
            resume_data = ResumeData(
                contact=ContactInfo(
                    name=name,
                    email=email,
                    phone=phone,
                    location=location,
                    linkedin=linkedin,
                    github=github
                ),
                summary=summary,
                experience=experience_entries,
                education=education_entries,
                skills=skills,
                projects=project_entries,
                certifications=certification_entries
            )
            
            st.success("✅ Resume data saved successfully!")
            return resume_data
    
    return None
