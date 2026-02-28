# LLM-Based Resume Parser with Pydantic

This module provides intelligent resume parsing using Large Language Models (LLMs) and structured data validation with Pydantic.

## Features

✨ **Structured Data Extraction**
- Uses Pydantic models for type-safe, validated resume data
- Extracts all resume sections: contact, experience, education, skills, projects, certifications
- Preserves formatting and context better than regex-based parsing

🤖 **LLM-Powered Parsing**
- Leverages Ollama for local, private AI processing
- More accurate than traditional regex/rule-based parsers
- Handles various resume formats and styles

🔄 **Backward Compatible**
- Seamlessly integrates with existing PDF generator
- Falls back to regex parsing if LLM is unavailable
- Can be toggled on/off as needed

## Pydantic Models

### ContactInfo
```python
class ContactInfo(BaseModel):
    name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    website: Optional[str]
```

### ExperienceEntry
```python
class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: Optional[str]
    start_date: str
    end_date: str
    bullets: List[str]
```

### EducationEntry
```python
class EducationEntry(BaseModel):
    degree: str
    institution: str
    location: Optional[str]
    start_date: Optional[str]
    end_date: str
    gpa: Optional[str]
    honors: List[str]
```

### ProjectEntry
```python
class ProjectEntry(BaseModel):
    title: str
    description: Optional[str]
    technologies: List[str]
    bullets: List[str]
    date: Optional[str]
```

### CertificationEntry
```python
class CertificationEntry(BaseModel):
    name: str
    issuer: str
    date: Optional[str]
    credential_id: Optional[str]
```

### ResumeData (Main Model)
```python
class ResumeData(BaseModel):
    contact: ContactInfo
    summary: Optional[str]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    skills: List[str]
    projects: List[ProjectEntry]
    certifications: List[CertificationEntry]
```

## Usage

### Basic Parsing

```python
from resume_parser import LLMResumeParser

# Initialize parser
parser = LLMResumeParser(model="llama3.1")

# Parse resume text
resume_text = """
John Doe
john@email.com | (555) 123-4567
...
"""

resume_data = parser.parse_resume(resume_text)

# Access structured data
print(resume_data.contact.name)  # "John Doe"
print(resume_data.contact.email)  # "john@email.com"
print(len(resume_data.experience))  # Number of jobs
```

### Generate PDF with LLM Parsing

```python
from pdf_generator import ResumePDFGenerator

# Create generator with LLM parsing enabled
generator = ResumePDFGenerator(use_llm_parser=True, model="llama3.1")

# Generate PDF
pdf_bytes = generator.generate_pdf(resume_text)

# Save to file
with open("resume.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Disable LLM Parsing (Use Regex Fallback)

```python
# Use traditional regex-based parsing
generator = ResumePDFGenerator(use_llm_parser=False)
pdf_bytes = generator.generate_pdf(resume_text)
```

### Export to JSON

```python
# Parse resume
resume_data = parser.parse_resume(resume_text)

# Export as JSON
json_output = resume_data.model_dump_json(indent=2)

# Save to file
with open("resume.json", "w") as f:
    f.write(json_output)
```

### Access Individual Sections

```python
resume_data = parser.parse_resume(resume_text)

# Contact information
print(f"Name: {resume_data.contact.name}")
print(f"Email: {resume_data.contact.email}")

# Experience
for exp in resume_data.experience:
    print(f"{exp.title} at {exp.company}")
    print(f"{exp.start_date} - {exp.end_date}")
    for bullet in exp.bullets:
        print(f"  • {bullet}")

# Education
for edu in resume_data.education:
    print(f"{edu.degree} from {edu.institution}")
    if edu.gpa:
        print(f"GPA: {edu.gpa}")

# Skills
print("Skills:", ", ".join(resume_data.skills))

# Projects
for proj in resume_data.projects:
    print(f"{proj.title}")
    print(f"Technologies: {', '.join(proj.technologies)}")
```

## Installation

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Ensure Ollama is running:**
   ```bash
   # Check if Ollama is installed
   ollama --version
   
   # Pull a model (if not already done)
   ollama pull llama3.1
   
   # Ollama runs automatically, or start manually:
   ollama serve
   ```

## Running Examples

```bash
# Run the example script
python example_parser_usage.py
```

This will demonstrate:
1. Parsing a resume and displaying structured data
2. Generating a PDF with LLM-based parsing
3. Comparing LLM vs regex parsing methods

## Benefits of LLM Parsing

### Traditional Regex Parsing
- ❌ Fragile - breaks with format changes
- ❌ Requires extensive pattern matching
- ❌ Poor handling of edge cases
- ❌ No context understanding

### LLM-Based Parsing
- ✅ Robust - handles various formats
- ✅ Context-aware extraction
- ✅ Better accuracy for complex resumes
- ✅ Understands semantic meaning
- ✅ Easier to maintain

## Configuration

### Model Selection

You can use different Ollama models:

```python
# Use llama3.1 (recommended)
parser = LLMResumeParser(model="llama3.1")

# Use llama3.2
parser = LLMResumeParser(model="llama3.2")

# Use mistral
parser = LLMResumeParser(model="mistral")
```

### Temperature Settings

The parser uses low temperature (0.1) for consistent, deterministic parsing. This is configured in the `parse_resume` method.

## Error Handling

The parser includes automatic fallback:

```python
# If LLM parsing fails, automatically falls back to regex
generator = ResumePDFGenerator(use_llm_parser=True)

# This will try LLM first, then regex if needed
pdf_bytes = generator.generate_pdf(resume_text)
```

## Performance

- **LLM Parsing**: 5-15 seconds (depends on model and resume length)
- **Regex Parsing**: < 1 second
- **Recommendation**: Use LLM for accuracy, regex for speed

## Integration with Existing Code

The parser is fully integrated with the existing codebase:

1. **PDF Generator** - Automatically uses LLM parsing by default
2. **Resume Tailor** - Can be enhanced to use structured data
3. **Streamlit App** - Works seamlessly with current workflow

## Troubleshooting

### Ollama Not Available
```
Error: Ollama is not running
```
**Solution:** Start Ollama with `ollama serve`

### Model Not Found
```
Error: model 'llama3.1' not found
```
**Solution:** Pull the model with `ollama pull llama3.1`

### JSON Parsing Error
The parser includes automatic retry with fallback to regex parsing.

### Slow Performance
- Use a smaller model (e.g., `llama3.2` instead of `llama3.1`)
- Reduce resume length
- Use regex parsing for speed-critical operations

## Future Enhancements

- [ ] Add support for more resume sections (publications, awards, languages)
- [ ] Implement caching for repeated parses
- [ ] Add confidence scores for extracted data
- [ ] Support for multiple resume formats (PDF, DOCX input)
- [ ] Batch processing for multiple resumes
- [ ] Custom field extraction based on job requirements

## API Reference

### LLMResumeParser

**`__init__(model: str = "llama3.1")`**
- Initialize parser with specified Ollama model

**`parse_resume(resume_text: str) -> ResumeData`**
- Parse resume text into structured ResumeData object

**`to_legacy_format(resume_data: ResumeData) -> dict`**
- Convert ResumeData to legacy dictionary format

### ResumePDFGenerator

**`__init__(use_llm_parser: bool = True, model: str = "llama3.1")`**
- Initialize PDF generator with optional LLM parsing

**`generate_pdf(resume_text: str, job_title: str = None, company: str = None) -> bytes`**
- Generate PDF from resume text

## License

Same as parent project.
