import openai
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_image.py [prompt]")
        sys.exit()
    prompt = ' '.join(sys.argv[1:])
    response = openai.Image.create(prompt=prompt, n=1)
    image_url = response["data"][0]["url"]
    image_data = requests.get(image_url).content
    with open("generated_image.png", "wb") as f:
        f.write(image_data)
