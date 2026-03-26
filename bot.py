import os
import sys
import requests
from google import genai

# Load environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize the NEW Gemini client
client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Generate 3 UPSC Mains standard questions on Indian Society (GS1) and 3 on Ethics (GS4). Output ONLY the questions, numbered clearly."
        # Using the new SDK syntax
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        
        with open('latest_questions.txt', 'w') as f:
            f.write(response.text)
            
        message = "🌅 **Good Morning! Here are your Mains Questions for today:**\n\n" + response.text
        send_telegram_message(message)
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r') as f:
                questions = f.read()
            prompt = f"Provide detailed, structured UPSC-standard answers for the following questions:\n{questions}"
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            message = "📚 **Afternoon! Here are the detailed answers:**\n\n" + response.text
        except FileNotFoundError:
            message = "⚠️ Error: Could not find today's questions to answer."
            
        send_telegram_message(message)

if __name__ == "__main__":
    main()
