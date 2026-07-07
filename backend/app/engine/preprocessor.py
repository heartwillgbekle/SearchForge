import re


STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "to", "of", "in",
    "on", "for", "from", "by", "with", "them", "it"
}


def tokenize(text):
    text = text.lower()
    words = re.findall(r"\b[a-z]+\b", text)

    tokens = []

    for word in words:
        if word not in STOP_WORDS:
            tokens.append(word)

    return tokens
