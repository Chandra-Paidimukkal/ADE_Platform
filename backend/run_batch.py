import json

from utils.batch_pipeline import run_batch


with open("schemas/schema.json") as f:

    schema = json.load(f)


results = run_batch(
    folder="pdfs",
    schema=schema,
    use_ai=True
)


for r in results:

    print("\n----------------------")

    print("File:", r["file"])

    print("Data:", r["data"])