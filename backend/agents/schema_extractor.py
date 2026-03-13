import re


class SchemaExtractor:

    def __init__(self, schema):

        self.fields = schema.get("fields", [])

    def extract(self, text):

        results = {}

        for field in self.fields:

            pattern = rf"{field}\s*[:\-]?\s*([^\n]+)"

            match = re.search(pattern, text, re.IGNORECASE)

            if match:

                results[field] = match.group(1).strip()

        return results