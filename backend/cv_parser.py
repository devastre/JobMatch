import logging
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
from sqlalchemy.orm import Session
from models import CV

logger = logging.getLogger(__name__)
MAX_EDUCATION_ENTRIES = 5

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as exc:
        logger.warning("PDF text extraction failed for %s: %s", file_path, exc)
    
    # Fallback to OCR if no text extracted (scanned PDF)
    if not text.strip():
        try:
            images = convert_from_path(file_path)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
        except Exception as e:
            raise Exception(f"OCR fallback failed: {str(e)}")
            
    if not text.strip():
        raise Exception("Could not extract text from PDF.")
        
    return text

def parse_cv_text(text: str) -> dict:
    text_lower = text.lower()
    
    # Extract skills (deduplicated, case-insensitive, non-empty)
    skill_keywords = [
        "python", "java", "c++", "sql", "machine learning", "react", "node.js", 
        "aws", "docker", "kubernetes", "fastapi", "django", "javascript", 
        "typescript", "html", "css", "git", "linux", "azure", "gcp"
    ]
    extracted_skills = list({
        skill.strip().title() for skill in skill_keywords 
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower) and skill.strip()
    })
    
    # Extract languages
    language_keywords = [
        "english", "spanish", "french", "german", "mandarin", "arabic", 
        "hindi", "portuguese", "russian", "japanese"
    ]
    extracted_languages = list({
        lang.strip().title() for lang in language_keywords 
        if re.search(r'\b' + re.escape(lang) + r'\b', text_lower) and lang.strip()
    })
    
    # Extract titles
    title_keywords = [
        "engineer", "developer", "manager", "scientist", "analyst", 
        "consultant", "architect", "designer", "administrator"
    ]
    extracted_titles = list({
        title.strip().title() for title in title_keywords 
        if re.search(r'\b' + re.escape(title) + r'\b', text_lower) and title.strip()
    })
    
    # Extract education
    education_keywords = [
        "bachelor", "master", "phd", "bsc", "msc", "b.s.", "m.s.", 
        "university", "college", "institute", "degree"
    ]
    extracted_education = []
    for line in text.split('\n'):
        if any(edu in line.lower() for edu in education_keywords) and len(line.strip()) > 5:
            extracted_education.append(line.strip())
    
    # Extract years of experience
    years_experience = 0
    exp_match = re.search(r'(\d+)\+?\s*(?:years|yrs)(?:\s+of)?\s+experience', text_lower)
    if exp_match:
        try:
            years_experience = int(exp_match.group(1))
        except ValueError:
            pass
            
    return {
        "skills": extracted_skills,
        "titles": extracted_titles,
        "years_experience": years_experience,
        "languages": extracted_languages,
        "education": list(set(extracted_education))[:MAX_EDUCATION_ENTRIES],
        "raw_text": text
    }

def process_cv(cv_id: int, file_path: str, db: Session):
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        return
        
    try:
        cv.status = "processing"
        db.commit()
        
        text = extract_text_from_pdf(file_path)
        parsed_data = parse_cv_text(text)
        
        cv.parsed_json = parsed_data
        cv.status = "completed"
        db.commit()
    except Exception as e:
        db.rollback()
        cv.status = "error"
        cv.parsed_json = {"error": str(e)}
        db.commit()
