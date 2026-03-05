from scraper import scrape_tenders
from ocr_engine import extract_text_from_pdf
from nlp import extract_keywords, calculate_scores

def full_pipeline():
    tenders = scrape_tenders()

    for tender in tenders:
        pdf_path = "pdfs/sample.pdf" 
        text = extract_text_from_pdf(pdf_path)

        keywords = extract_keywords(text)
        relevance, risk, difficulty, fit = calculate_scores(text)

        print("Title:", tender["title"])
        print("Keywords:", keywords)
        print("Scores:", relevance, risk, difficulty, fit)