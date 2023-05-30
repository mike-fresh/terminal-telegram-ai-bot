import re


def clean_username(username: str) -> str:
    username = username.replace(" ", "_")
    username = replace_umlauts(username)
    username = re.sub(r'[^a-zA-Z_-]', '', username)
    if len(username) > 64:
        username = username[:64]
    return username


def replace_umlauts(text: str) -> str:
    umlauts = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}
    for umlaut, replacement in umlauts.items():
        text = text.replace(umlaut, replacement)
    return text
