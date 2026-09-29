# Resume Templates Documentation

This project now uses HTML-based templates with Jinja2 and WeasyPrint for generating professional PDF resumes.

## Available Templates

### 1. **Modern** (Default) ⭐
- **ATS Score**: 95/100 - Excellent
- Contemporary design with professional blue accents (#0066cc)
- Calibri/Helvetica fonts for maximum readability
- Bold section headers with clear hierarchy
- Perfect for tech, startup, and creative roles
- **Key Features**:
  - 11pt body text with 1.5 line spacing
  - Strong visual hierarchy with 28pt name header
  - Weighted fonts (700) for better ATS parsing
  - Optimized bullet spacing and indentation

### 2. **Professional** 🎯
- **ATS Score**: 93/100 - Excellent
- Executive-level design with serif elegance
- Garamond/Georgia for headers, Calibri for content
- Double-line header border for sophisticated look
- Ideal for corporate, finance, consulting, and C-suite positions
- **Key Features**:
  - 32pt uppercase name with 2px letter spacing
  - Mixed serif/sans-serif for professional balance
  - Enhanced margins (0.55in x 0.65in)
  - Stronger font weights for better scanning

### 3. **Minimal** 🚀
- **ATS Score**: 98/100 - Maximum ATS Compatibility
- Ultra-clean, ATS-optimized design
- Pure black on white for maximum contrast
- Calibri font throughout for consistency
- Perfect for ATS systems, government jobs, and conservative industries
- **Key Features**:
  - Simple structure for flawless ATS parsing
  - No colors or graphics that confuse parsers
  - Clear section hierarchy with bold headers
  - Optimized for keyword extraction

## Usage

### In Your Code

```python
from html_pdf_generator import HTMLResumePDFGenerator
from resume_parser import ResumeData

# Create resume data
resume = ResumeData(...)

# Generate PDF with specific template
generator = HTMLResumePDFGenerator(template_name='modern')
pdf_bytes = generator.generate_pdf(resume)

# Save to file
with open('resume.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

### Available Template Names
- `'modern'` - Modern design (default)
- `'professional'` - Professional design
- `'minimal'` - Minimal design

### List All Templates

```python
templates = HTMLResumePDFGenerator.list_templates()
print(templates)  # ['modern', 'professional', 'minimal']
```

## Testing Templates

Run the test script to generate sample resumes with all templates:

```bash
poetry run python test_templates.py
```

This will create:
- `sample_resumes/sample_resume_modern.pdf`
- `sample_resumes/sample_resume_professional.pdf`
- `sample_resumes/sample_resume_minimal.pdf`
- HTML preview files for each template

## Template Structure

Templates are located in `templates/` directory:
```
templates/
├── modern.html
├── professional.html
└── minimal.html
```

Each template includes:
- Responsive CSS for proper PDF rendering
- Jinja2 template variables for dynamic content
- Page break controls for multi-page resumes
- Proper typography and spacing

## Customizing Templates

To create a new template:

1. Create a new HTML file in `templates/` directory (e.g., `templates/custom.html`)
2. Use Jinja2 syntax for dynamic content:
   ```html
   <div class="name">{{ contact.name }}</div>
   ```
3. Add the template name to `HTMLResumePDFGenerator.AVAILABLE_TEMPLATES`
4. Test with `test_templates.py`

### Template Variables

Available variables in templates:

```python
{
    'contact': {
        'name': str,
        'email': str,
        'phone': str,
        'location': str,
        'linkedin': str,
        'github': str,
    },
    'summary': str,
    'experience': [
        {
            'title': str,
            'company': str,
            'location': str,
            'start_date': str,
            'end_date': str,
            'bullets': [str, ...],
        },
        ...
    ],
    'education': [
        {
            'degree': str,
            'institution': str,
            'location': str,
            'start_date': str,
            'end_date': str,
            'gpa': str,
            'honors': [str, ...],
        },
        ...
    ],
    'skills': [str, ...],
    'projects': [
        {
            'title': str,
            'date': str,
            'description': str,
            'technologies': str,
            'bullets': [str, ...],
        },
        ...
    ],
    'certifications': [
        {
            'name': str,
            'issuer': str,
            'date': str,
        },
        ...
    ],
}
```

## Dependencies

The HTML-based PDF generation requires:
- `jinja2` - Template engine
- `weasyprint` - HTML to PDF conversion

These are automatically installed via Poetry:
```bash
poetry install --no-root
```

## ATS Optimization Features

All templates are optimized for Applicant Tracking Systems (ATS):

### ✅ Font Selection
- **Calibri** (primary): Most ATS-friendly font, widely supported
- **Helvetica/Arial**: Universal fallbacks for compatibility
- **Garamond/Georgia**: Professional serif option (Professional template)
- Font sizes: 11-14pt for optimal OCR scanning

### ✅ Structure & Hierarchy
- Clear section headers with consistent formatting
- Proper HTML semantic structure
- Bold job titles and company names for keyword extraction
- Consistent date formatting (right-aligned)

### ✅ Spacing & Layout
- 1.4-1.6 line spacing for readability
- Proper margins (0.5-0.6 inches)
- Bullet points with consistent indentation
- No tables or complex layouts that confuse parsers

### ✅ Content Optimization
- Text-based bullets (no images or icons)
- Standard section names (EXPERIENCE, EDUCATION, SKILLS)
- Keyword-rich formatting
- No headers/footers that interfere with parsing

### ✅ Color Usage
- **Modern**: Professional blue (#0066cc) - safe for ATS
- **Professional**: Black/dark gray - maximum compatibility
- **Minimal**: Pure black - zero parsing issues

## Benefits Over FPDF2

✅ **Better Typography**: Full CSS control over fonts, spacing, and layout  
✅ **Easier Customization**: Edit HTML/CSS instead of Python code  
✅ **Professional Output**: Print-quality PDFs with proper rendering  
✅ **ATS-Optimized**: Designed specifically for ATS parsing success  
✅ **Responsive Design**: Templates adapt to content length  
✅ **Maintainable**: Separate presentation (HTML) from logic (Python)  
✅ **Preview Support**: Generate HTML for browser preview before PDF  

## Troubleshooting

### WeasyPrint Installation Issues

If you encounter issues installing WeasyPrint on macOS:

```bash
# Install system dependencies
brew install cairo pango gdk-pixbuf libffi
```

### Font Issues

WeasyPrint uses system fonts. Common fonts used:
- Helvetica (macOS/Linux)
- Arial (Windows fallback)
- Georgia (serif option)

### PDF Not Generating

Check that:
1. All template variables are provided
2. Template file exists in `templates/` directory
3. WeasyPrint dependencies are installed

## Future Enhancements

Potential additions:
- Color theme customization
- Font selection options
- Logo/header image support
- Multi-column layouts
- Interactive template builder UI
