import re
from sklearn.feature_extraction.text import TfidfVectorizer

def clean_text(text):
    return re.sub(r'\s+', ' ', text.lower())

def extract_keywords(text, top_n=3):
    text = clean_text(text)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
    sorted_words = sorted(scores, key=lambda x: x[1], reverse=True)
    return [word for word, score in sorted_words[:top_n]]

def generate_summary(text):
    sentences = text.split(".")
    return ".".join(sentences[:2])