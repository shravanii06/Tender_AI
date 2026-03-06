import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text


def extract_keywords(text):

    words = clean_text(text).split()

    stopwords = [
        "the","is","in","and","to","for","of","on","with",
        "a","an","by","from","this","that"
    ]

    keywords = [w for w in words if w not in stopwords]

    freq = {}

    for word in keywords:
        freq[word] = freq.get(word,0) + 1

    sorted_words = sorted(freq, key=freq.get, reverse=True)

    return sorted_words[:5]


def generate_summary(title, description):

    keywords = extract_keywords(title + " " + description)

    summary = f"This tender relates to {', '.join(keywords)}."

    return summary

def summarize(text):

    sentences = re.split(r'\.|\n', text)

    summary = sentences[:2]

    return ". ".join(summary)