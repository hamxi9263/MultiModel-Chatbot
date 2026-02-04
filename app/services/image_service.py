from PIL import Image
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def load_image(uploaded_file):
    return Image.open(uploaded_file)

def generate_image(prompt, model="openai/dall-e-3"):
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = "https://openrouter.ai/api/v1"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "512x512"
    }

    response = requests.post(f"{base_url}/images/generations", headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        image_url = result['data'][0]['url']
        return image_url
    else:
        raise Exception(f"Image generation failed: {response.text}")
