from core.table_extractor import extract_tables
from agents.model_detector import detect_models
from agents.text_spec_extractor import extract_specs_from_text
from core.image_extractor import extract_text_from_images


class ExtractionAgent:

    def run(self, pdf_path, parsed_text):

        tables = extract_tables(pdf_path)

        models = detect_models(parsed_text)

        text_specs = extract_specs_from_text(parsed_text)

        image_text = extract_text_from_images(pdf_path)

        image_specs = extract_specs_from_text(image_text)

        specs = {}

        specs.update(text_specs)
        specs.update(image_specs)

        for table in tables:

            for row in table:

                key = row.get("key")
                value = row.get("value")

                if not key or not value:
                    continue

                key = key.lower()

                if "voltage" in key:
                    specs["voltage"] = value

                if "amp" in key:
                    specs["amperage"] = value

                if "capacity" in key:
                    specs["capacity"] = value

        return {
            "models": models,
            "specifications": specs
        }