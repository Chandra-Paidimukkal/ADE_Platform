import os
import json

from core.pdf_reader import extract_text
from agents.schema_extractor import SchemaExtractor
from agents.ai_extractor import AIExtractor


def run_batch(folder, schema, use_ai=False):

    results = []

    schema_extractor = SchemaExtractor(schema)

    ai_extractor = None

    if use_ai:

        ai_extractor = AIExtractor(
            api_key="YOUR_API_KEY",
            endpoint="https://api.openai.com/v1/chat/completions"
        )

    for file in os.listdir(folder):

        if file.lower().endswith(".pdf"):

            path = os.path.join(folder, file)

            print(f"\nProcessing: {file}")

            text = extract_text(path)

            if use_ai:

                data = ai_extractor.extract(text, schema)

            else:

                data = schema_extractor.extract(text)

            results.append({
                "file": file,
                "data": data
            })

    return results