import os
import requests
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL")  # Example: https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")

def generate_quiz_from_watsonx(topic: str, difficulty: str):
    prompt = f"""
    Generate 3 {difficulty} multiple-choice questions on the topic \"{topic}\". 
    Each question should have 4 options and indicate the correct one.
    
    Format:
    Q1: Question?
    a) Option 1
    b) Option 2
    c) Option 3
    d) Option 4
    Answer: b
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WATSONX_API_KEY}"
    }

    data = {
        "model_id": WATSONX_MODEL_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 500
        }
    }

    response = requests.post(f"{WATSONX_URL}/ml/v1/text/generation", json=data, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    return result.get("results", [{}])[0].get("generated_text", "") 