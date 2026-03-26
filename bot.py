import os
import sys
import requests
import time
from google import genai

# 1. Load Keys from GitHub Secrets
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# 2. Initialize Gemini Client (2026 SDK)
client = genai.Client(api_key=GEMINI_KEY)

def clean_text(text):
    """Removes symbols that confuse Telegram's formatting parser."""
    return text.replace('*', '').replace('_', '').replace('`', '').replace('#', '')

def send_telegram_message(text):
    """Sends clean text in small chunks to avoid Telegram 'Bad Request' errors."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Remove problematic markdown for maximum reliability
    safe_text = clean_text(text)
    
    # Split into 3000-character chunks (Telegram limit is 4096)
    chunks = [safe_text[i:i+3000] for i in range(0, len(safe_text), 3000)]
    
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk
        }
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"TELEGRAM ERROR: {response.text}")
        else:
            print("Chunk delivered successfully!")

def generate_with_retry(prompt):
    """Calls the 2026 stable Gemini 2.5 Flash model."""
    model_id = "gemini-2.5-flash"
    try:
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}. Retrying in 15 seconds...")
        time.sleep(15)
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        prompt = "Provide 3 analytical UPSC GS-1 Society questions and 3 GS-4 Ethics questions. Number them clearly."
        try:
            output = generate_with_retry(prompt)
            # Save for afternoon use
            with open('latest_questions.txt', 'w', encoding='utf-8') as f:
                f.write(output)
            
            send_telegram_message("🌅 GOOD MORNING! TODAY'S QUESTIONS:\n\n" + output)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            sys.exit(1)
            
    elif mode == "answers":
        try:
            with open('latest_questions.txt', 'r', encoding='utf-8') as f:
                questions = f.read()
            
            prompt = f"Provide structured UPSC answers (3 intro options, 3 conclusion options, and body) for these questions:\n{questions}"
            output = generate_with_retry(prompt)
            
            send_telegram_message("📚 AFTERNOON ANSWER KEY:\n\n" + output)
        except FileNotFoundError:
            print("No questions file found.")
            sys.exit(1)
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
