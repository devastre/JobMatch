import re
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_MATCH_BONUS = 5.0

def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

def calculate_match_score(cv_text: str, job_text: str, cv_skills: List[str]) -> Dict[str, Any]:
    """
    Calculates a match score between a CV and a job description.
    Returns a dictionary with the score (0-100) and matched keywords.
    """
    if not cv_text or not job_text:
        return {"score": 0.0, "matched_keywords": []}

    processed_cv = preprocess_text(cv_text)
    processed_job = preprocess_text(job_text)

    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([processed_cv, processed_job])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        similarity = 0.0

    base_score = similarity * 100.0

    matched_keywords = []
    skill_boost = 0.0
    
    for skill in cv_skills:
        processed_skill = preprocess_text(skill).strip()
        if not processed_skill:
            continue
            
        if processed_skill in processed_job:
            matched_keywords.append(skill)
            skill_boost += SKILL_MATCH_BONUS

    final_score = min(100.0, base_score + skill_boost)

    return {
        "score": round(final_score, 2),
        "matched_keywords": matched_keywords
    }
