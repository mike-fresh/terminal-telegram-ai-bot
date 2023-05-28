# Terminal and Telegram Chatbot using the OpenAI API

Chatbot written in Python that uses the OpenAI API to generate "intelligent" responses to user input. 
You can use it in your shell or run it as a Telegram bot.

It started with 4 lines of code and essentially Chat-GPT wrote its own interface. It was quite a long conversation :)

## Features
- Runs in your shell or as a Telegram bot
- Code highlighting in the shell
- Uses the OpenAI API to generate responses
- Uses the Telegram API to send and receive messages
- The bot can also be added to groups and supports chatting with multiple users
- In groups, it only responds to messages that are directed at it or when it is mentioned
- Customizable settings
- Uses a sqlite3 database to store chat history and log messages
- Generates not only text but also images! See an example below

## Setup
1. Create an OpenAI account and get the API key
2. Create a Telegram bot using the BotFather and get the API token
3. Install the bot on a linux server or on your local machine (see installation below)
4. Create a .env file in the root directory and set the configuration in it (see example.env)
5. Run it in your shell or as a Telegram bot with the `--telegram` flag

## Installation

```bash
git clone https://github.com/mike-fresh/terminal-telegram-ai-bot
cd terminal-telegram-ai-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 chatbot.py
```
Press CTRL-D in your terminal to send your message to the bot.
For starting the bot as a Telegram bot, use the `--telegram` flag.

# Generating Images
The bot can also generate images. In your shell use  
`python3 picbot.py [prompt]`

In Telegram, send a message with the command  
`/pic [promt]` to the bot.

This is an example of an image generated by the bot:

![Sample Image](sample_images/house_on_lake_in_sunset.png)



## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
GPL-3.0 License

## Project Status
This project is currently in development. 

