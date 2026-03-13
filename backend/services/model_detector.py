import re

MODEL_PATTERNS = [
    r"\b[A-Z]{2,}\d+[A-Z0-9-]*\b",
    r"\b\d+[A-Z]+\b"
]


def detect_models(text):

    models = set()

    for pattern in MODEL_PATTERNS:

        matches = re.findall(pattern, text)

        for m in matches:
            if len(m) > 3:
                models.add(m)

    return list(models)