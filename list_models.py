import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def list_models(version="v1beta"):
    url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
    resp = requests.get(url)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        print(f"--- Models in {version} ---")
        for m in models:
            print(m.get("name"))
    else:
        print(f"--- Failed to list models in {version} ({resp.status_code}) ---")
        print(resp.text)

list_models("v1beta")
list_models("v1")
