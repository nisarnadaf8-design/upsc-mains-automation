import os
import sys
import requests
import time
from google import genai

# Load environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Break long messages to avoid Telegram limits
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            payload = {"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"}
            requests.post(url, json=payload)
    else:
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

def generate_with_retry(prompt):
    """Simple retry logic to handle minor quota hiccups"""
    try:
        # Switching to the more stable 1.5 Pro model
        return client.models.generate_content(model="gemini-1.5-pro", contents=prompt)
    except Exception as e:
        print(f"First attempt failed, waiting 10s... Error: {e}")
        time.sleep(10)
        return client.models.generate_content(model="gemini-1.5-pro", contents=prompt)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Provide 3 high-quality UPSC GS-1 Society questions and 3 GS-4 Ethics questions. Ensure they are analytical and syllabus-aligned. Output only the questions."
        response = generate_with_retry(prompt)
        
        with open('latest_questions.txt', 'w') as f:
            f.write(response.text)
            
        message = "🌅 **Good Morning! Today's Practice Questions:**\n\n" + response.text
        send_telegram_message(message)
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r') as f:
                questions = f.read()
            prompt = f"Provide structured UPSC answers for these questions. For each, give 3 intro options, 3 conclusion options, and a concise body. Question list:\n{questions}"
            response = generate_with_retry(prompt)
            message = "📚 **Afternoon Answer Key:**\n\n" + response.text
        except FileNotFoundError:
            message = "⚠️ No questions found for today. Please run the morning schedule first."
            
        send_telegram_message(message)

if __name__ == "__main__":
    main()
