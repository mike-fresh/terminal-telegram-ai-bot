import openai
import requests
from modules.config import Config
from modules.database import Database
import datetime


class Picture:
    config = Config()
    db = Database(config.DB_URI)

    def __init__(self, description: str) -> None:
        self.prompt = description
        self.response = openai.Image.create(prompt=self.prompt, n=1)
        self.image_url = self.response["data"][0]["url"]
        self.image_data = requests.get(self.image_url).content
        self.timestamp_string = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.picture_file = f"generated_image-{self.timestamp_string}.png"
        with open(self.picture_file, "wb") as f:
            f.write(self.image_data)
