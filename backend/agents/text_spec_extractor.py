import re


patterns = {
    "voltage": r"(\d+\s?V)",
    "amperage": r"(\d+\.?\d*\s?A)",
    "capacity": r"(\d+\s?(cu ft|liters))",
    "power": r"(\d+\s?(W|kW))"
}


def extract_specs_from_text(text):

    specs = {}

    for key, pattern in patterns.items():

        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            specs[key] = match.group(1)

    return specs