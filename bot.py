import os
import sys
import requests
import time
from google import genai

# Load Keys
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_KEY)

def clean_text(text):
    """Removes symbols that confuse Telegram."""
    return text.replace('*', '').replace('_', '').replace('`', '').replace('#', '')

def send_telegram_message(text):
    """Sends clean text in 3000-character chunks."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    safe_text = clean_text(text)
    chunks = [safe_text[i:i+3000] for i in range(0, len(safe_text), 3000)]
    
    for chunk in chunks:
        payload = {"chat_id": CHAT_ID, "text": chunk}
        requests.post(url, json=payload)

def generate_with_retry(prompt):
    model_id = "gemini-2.5-flash"
    try:
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Provide 3 analytical UPSC GS-1 Society and 3 GS-4 Ethics questions. Keep them concise."
        output = generate_with_retry(prompt)
        with open('latest_questions.txt', 'w', encoding='utf-8') as f:
            f.write(output)
        send_telegram_message("🌅 TODAY'S QUESTIONS:\n\n" + output)
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r', encoding='utf-8') as f:
                questions = f.read()
            
            # IMPROVED PROMPT FOR CRISP ANSWERS
            prompt = (
                f"Provide short, crisp UPSC model answers for these questions. "
                f"Use high-impact bullet points. Limit each answer to 150 words. "
                f"Structure: 1-line Intro, 5-6 Body points, 1-line Conclusion.\n\n"
                f"Questions:\n{questions}"
            )
            
            output = generate_with_retry(prompt)
            send_telegram_message("📚 CRISP ANSWER KEY:\n\n" + output)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
