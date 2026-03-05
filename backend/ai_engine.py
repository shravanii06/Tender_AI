def calculate_relevance(description):
    keywords = ["road", "construction", "bridge", "software", "ai", "it"]
    score = 0
    for word in keywords:
        if word in description.lower():
            score += 15
    return score


def calculate_risk(description, emd):
    score = 0
    if emd >= 500000:
        score += 30
    elif emd >= 200000:
        score += 15

    risky_words = ["penalty", "blacklist", "litigation"]
    for word in risky_words:
        if word in description.lower():
            score += 20
    return score


def calculate_difficulty(description, emd):
    score = 0
    if emd >= 300000:
        score += 20
    if len(description) > 120:
        score += 20
    return score


def calculate_fit(emd):
    if emd < 200000:
        return 80
    elif emd < 400000:
        return 60
    else:
        return 40
    
