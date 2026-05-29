import os
import telebot
import json
import re
from groq import Groq

BOT_TOKEN = os.environ['BOT_TOKEN']
GROQ_API_KEY = os.environ['GROQ_API_KEY']
SVEN_CHAT_ID = int(os.environ['SVEN_CHAT_ID'])

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

geschiedenis = {}

SYSTEM_PROMPT = """
Je bent de persoonlijke assistent van Sven.
Je beantwoordt vragen van zijn vrienden en familie.
Als iemand vraagt om Sven een melding te sturen, voeg dan toe:

<notify_sven>
{"message": "de melding voor Sven"}
</notify_sven>

Wees vriendelijk en spreek Nederlands.
"""

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.chat.id
    if user_id not in geschiedenis:
        geschiedenis[user_id] = []
    geschiedenis[user_id].append({"role": "user", "content": message.text})
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + geschiedenis[user_id]
    )
    antwoord = response.choices[0].message.content
    geschiedenis[user_id].append({"role": "assistant", "content": antwoord})
    match = re.search(r'<notify_sven>(.*?)</notify_sven>', antwoord, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        melding = f"Melding van {message.chat.first_name}:\n\n{data['message']}"
        bot.send_message(SVEN_CHAT_ID, melding)
    schoon = re.sub(r'<notify_sven>.*?</notify_sven>', '', antwoord, flags=re.DOTALL).strip()
    bot.reply_to(message, schoon)

bot.polling()
