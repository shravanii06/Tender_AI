# ---------------- RELEVANCE ----------------

def calculate_relevance(title, description):

    score = 0

    keywords = [
        "construction",
        "road",
        "bridge",
        "software",
        "it",
        "electrical",
        "education"
    ]

    text = (title + " " + description).lower()

    for word in keywords:
        if word in text:
            score += 15

    return min(score, 100)


# ---------------- RISK ----------------

def calculate_risk(deadline, emd):

    score = 0

    # EMD risk
    if emd >= 500000:
        score += 40
    elif emd >= 200000:
        score += 20

    # Deadline risk
    from datetime import datetime

    try:
        d = datetime.strptime(deadline, "%d-%m-%Y")
        days = (d - datetime.now()).days

        if days <= 3:
            score += 40
        elif days <= 10:
            score += 20

    except:
        pass

    return min(score, 100)


# ---------------- DIFFICULTY ----------------

def calculate_difficulty(title, category):

    score = 0

    hard_words = [
        "technical",
        "compliance",
        "certification",
        "qualification"
    ]

    text = (title + " " + category).lower()

    for w in hard_words:
        if w in text:
            score += 25

    return min(score, 100)


# ---------------- FIT SCORE ----------------

def calculate_fit(relevance, risk, difficulty):

    fit = relevance - risk - difficulty

    if fit < 0:
        fit = 0

    return fit