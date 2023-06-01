import openai
import requests
import os
from dotenv import load_dotenv
import argparse

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY


def generate_image(prompt):
    try:
        prompt_text = " ".join(prompt)
        response = openai.Image.create(prompt=prompt_text, n=1)
        image_url = response["data"][0]["url"]
        image_data = requests.get(image_url).content
        with open("generated_image.png", "wb") as f:
            f.write(image_data)
        print("Image generated successfully!")
    except Exception as e:
        print(f"Error generating image: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an image based on a prompt.")
    parser.add_argument("prompt", nargs="+", type=str, help="The prompt to generate the image from.")
    args = parser.parse_args()

    generate_image(args.prompt)
