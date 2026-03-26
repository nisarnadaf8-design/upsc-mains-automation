import os
import sys
import requests
import time
from google import genai

# 1. Load your API keys
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# 2. Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    """Sends message to Telegram. Has a built-in safety net if Telegram hates the formatting."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram max message length is 4096 characters. We chunk it at 4000 to be safe.
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    
    for chunk in chunks:
        # Attempt 1: Try sending with Markdown formatting
        payload = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)
        
        # Attempt 2: If Telegram rejects it (usually because of a stray '*' symbol), send as plain text
        if response.status_code != 200:
            print(f"Telegram rejected the formatting. Error: {response.text}")
            print("Sending as plain text instead to ensure you get the message...")
            safe_payload = {"chat_id": CHAT_ID, "text": chunk} # No parse_mode
            requests.post(url, json=safe_payload)

def generate_with_retry(prompt):
    """Fetches AI response using the stable 1.5-flash model, with a retry if Google limits us."""
    model_name = "gemini-1.5-flash"
    
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Hit a Google rate limit or error: {e}")
        print("Waiting 35 seconds to clear the rate limit before trying again...")
        time.sleep(35)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

def main():
    # Figure out if it's morning (questions) or afternoon (answers)
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    
    if mode == "questions":
        print("Running in QUESTIONS mode...")
        # Added an instruction to keep formatting simple so Telegram doesn't crash
        prompt = "Provide 3 analytical UPSC GS-1 Society questions and 3 GS-4 Ethics questions. Output only the questions, numbered clearly. Do not use complex markdown formatting."
        
        try:
            output_text = generate_with_retry(prompt)
            
            # Save for the afternoon
            with open('latest_questions.txt', 'w', encoding='utf-8') as f:
                f.write(output_text)
            
            message = "🌅 **Good Morning! Today's Practice Questions:**\n\n" + output_text
            send_telegram_message(message)
            print("Questions sent successfully!")
            
        except Exception as e:
            print(f"Critical Error generating questions: {e}")
            
    elif mode == "answers":
        print("Running in ANSWERS mode...")
        try:
            with open('latest_questions.txt', 'r', encoding='utf-8') as f:
                questions = f.read()
                
            prompt = f"Provide highly structured UPSC-standard answers for these questions. For each, give 3 distinct intro options, 3 forward-looking conclusion options, and a concise body. Keep formatting simple. Question list:\n{questions}"
            
            output_text = generate_with_retry(prompt)
            message = "📚 **Afternoon Answer Key:**\n\n" + output_text
            send_telegram_message(message)
            print("Answers sent successfully!")
            
        except FileNotFoundError:
            error_msg = "⚠️ No questions found for today. The morning schedule needs to run successfully first."
            send_telegram_message(error_msg)
            print(error_msg)
        except Exception as e:
            print(f"Critical Error generating answers: {e}")

if __name__ == "__main__":
    main()
