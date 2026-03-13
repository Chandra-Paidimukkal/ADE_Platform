import os
import requests

API = "http://127.0.0.1:8000/api/v1/documents/upload"

def process_folder(folder):

    results = []

    for file in os.listdir(folder):

        if file.endswith(".pdf"):

            path = os.path.join(folder, file)

            with open(path, "rb") as f:
                r = requests.post(API, files={"file": f})

            results.append(r.json())

    return results