# list_models.py
from google import genai
import os

# Set your API key here (or via environment variable GOOGLE_API_KEY)
API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")

# Initialize client
client = genai.Client(api_key=API_KEY)

def list_models():
    try:
        pager = client.models.list()  # returns a Pager object
        print("Available models:")
        for m in pager:  # iterate over Pager to get each model
            print(f"- {m.name}  |  {getattr(m, 'description', 'No description')}")
    except Exception as e:
        print("Error fetching models:", e)

if __name__ == "__main__":
    list_models()
