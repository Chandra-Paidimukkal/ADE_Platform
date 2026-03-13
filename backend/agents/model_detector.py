import re


MODEL_REGEX = r"[A-Z0-9]{2,}-?[A-Z0-9]+"


def detect_models(text):

    models = re.findall(MODEL_REGEX, text)

    unique_models = list(set(models))

    return unique_models