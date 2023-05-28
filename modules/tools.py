import re


def clean_username(username: str) -> str:
    username = username.replace(" ", "_")
    username = re.sub(r'[^a-zA-Z_-]', '', username)
    if len(username) > 64:
        username = username[:64]
    return username
