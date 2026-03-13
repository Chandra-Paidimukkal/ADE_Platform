import requests
import json


class AIExtractor:

    def __init__(self, api_key, endpoint):

        self.api_key = api_key
        self.endpoint = endpoint


    def extract(self, text, schema):

        prompt = f"""
Extract structured data from the document.

Schema:
{json.dumps(schema)}

Document text:
{text}

Return JSON only.
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }

        response = requests.post(self.endpoint, headers=headers, json=payload)

        result = response.json()

        content = result["choices"][0]["message"]["content"]

        return json.loads(content)