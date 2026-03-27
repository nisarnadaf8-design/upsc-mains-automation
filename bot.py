import os
import sys
import json
import requests
import time
from datetime import datetime, timezone, timedelta
from google import genai
 
# ── API Keys ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID        = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_KEY     = os.environ.get('GEMINI_API_KEY')
 
client = genai.Client(api_key=GEMINI_KEY)
MODEL  = "gemini-2.5-pro"
 
# ── Topic Rotation (changes daily, never repeats same day) ────────────────────
GS1_TOPICS = [
    "Indian Society: Diversity, Unity, Caste and Class",
    "Role of Women: Empowerment, Violence, Political Representation",
    "Communalism, Regionalism and Secularism",
    "Population: Demographic Dividend, Ageing, Migration",
    "Poverty, Social Exclusion and Inclusive Growth",
    "Urbanisation: Smart Cities, Slums, Urban Governance",
    "Globalisation and Its Effects on Indian Society",
]
 
GS4_TOPICS = [
    "Ethics and Human Interface: Essence and Determinants",
    "Attitude: Formation, Change and Moral Influence",
    "Civil Services Values: Integrity, Impartiality, Empathy",
    "Emotional Intelligence in Governance",
    "Moral Thinkers: Gandhi, Ambedkar, Aristotle, Kant",
    "Probity in Governance: Transparency and Accountability",
    "Case Studies: Conflict of Interest and Whistleblowing",
]
 
def today_topics():
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    day = ist.timetuple().tm_yday
    gs1 = GS1_TOPICS[day % len(GS1_TOPICS)]
    gs4 = GS4_TOPICS[day % len(GS4_TOPICS)]
    return gs1, gs4, ist.strftime("%d %b %Y")
 
# ── Telegram ──────────────────────────────────────────────────────────────────
def send_message(text: str):
    url    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        payload = {"chat_id": CHAT_ID, "text": chunk}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if not r.ok:
                print(f"Telegram error {r.status_code}: {r.text}")
            else:
                print("Chunk sent OK.")
        except Exception as e:
            print(f"Telegram exception: {e}")
        time.sleep(1)
 
def send_error(context: str, err: Exception):
    msg = f"BOT ERROR [{context}]\n{type(err).__name__}: {err}"
    print(msg)
    send_message(msg)
 
# ── Gemini ────────────────────────────────────────────────────────────────────
def generate(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            return resp.text
        except Exception as e:
            print(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(20)
    raise RuntimeError("Gemini API failed after all retries.")
 
# ── Prompts ───────────────────────────────────────────────────────────────────
QUESTION_PROMPT = """You are a UPSC Mains paper setter. Generate exactly 4 questions today.
 
TOPICS:
GS-1 (Society): {gs1}
GS-4 (Ethics): {gs4}
 
OUTPUT FORMAT (plain text only, no asterisks, no symbols):
 
GS-1 SOCIETY: {gs1}
 
Q1. (10 Marks)
[One crisp analytical question, 2 sentences max. Must test understanding, not memory recall.]
 
Q2. (15 Marks)
[One question requiring multi-dimensional analysis. 2 sentences max.]
 
GS-4 ETHICS: {gs4}
 
Q3. (10 Marks)
[One conceptual ethics question. 2 sentences max.]
 
Q4. (20 Marks - Case Study)
[Write a 4-line realistic scenario: A civil servant faces a tough ethical dilemma involving conflict between duty, loyalty, public interest and personal values. End with: What should the officer do? Discuss the ethical dimensions involved.]
 
RULES:
- Questions must be short, not lengthy
- No sub-parts a) b) c)
- Reflect UPSC Mains 2022-2024 style
- Plain text only
"""
 
ANSWER_PROMPT = """You are a UPSC Mains topper. Write model answers for all questions below.
 
ANSWER FORMAT (use this structure for every answer, plain text only):
 
Q[number]. [Topic]
[Marks] | [Word Limit]
 
Introduction:
[One sentence. Include a fact, constitutional article, government data, or relevant quote.]
 
[For each point use a clear heading on its own line, followed by 1-2 lines of explanation]
 
Heading 1:
Explanation with keyword or data point.
 
Heading 2:
Explanation with keyword or data point.
 
[Continue: 3 headings for 10M, 4-5 for 15M, 6-7 for 20M case study]
 
Example:
[One real post-2020 example: scheme, report, Supreme Court ruling, state initiative, or committee]
 
Conclusion:
[One sentence. Policy-oriented or value-based. Max 15 words.]
 
---------
 
WORD LIMITS (strictly follow):
10-mark answer: 150 words
15-mark answer: 200 words
20-mark case study: 250 words
 
LANGUAGE AND CONTENT RULES:
- Simple, direct English only
- Every line must add value, no filler
- Use UPSC keywords naturally:
  GS-1: social capital, demographic dividend, gender parity, constitutional morality,
         social mobility, feminisation of poverty, majoritarianism, SDG linkage
  GS-4: moral courage, conflict of interest, public trust, empathy, integrity,
         whistleblower, ethical governance, value pluralism, consequentialism
- Cite real data: NFHS-5, NCRB 2023, Census 2011, Economic Survey 2024,
  World Bank, UNDP HDI, MoSPI, SECC data
- No markdown symbols, no asterisks, no hashtags
 
QUESTIONS:
{questions}
"""
 
# ── File paths ────────────────────────────────────────────────────────────────
QUESTIONS_FILE = "latest_questions.txt"
META_FILE      = "latest_meta.json"
 
# ── Morning: Send Questions ───────────────────────────────────────────────────
def run_questions():
    gs1, gs4, date_str = today_topics()
    print(f"Topics today: GS1={gs1} | GS4={gs4}")
 
    prompt    = QUESTION_PROMPT.format(gs1=gs1, gs4=gs4)
    questions = generate(prompt)
 
    # Save to files (committed to repo for afternoon job)
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        f.write(questions)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump({"gs1": gs1, "gs4": gs4, "date": date_str}, f)
 
    header = (
        f"UPSC MAINS DAILY PRACTICE\n"
        f"Date: {date_str}\n"
        f"========================================\n"
        f"GS-1 Topic : {gs1}\n"
        f"GS-4 Topic : {gs4}\n"
        f"========================================\n\n"
        f"Write your answers before 1:00 PM IST.\n"
        f"Answer key will be sent at 1:00 PM.\n\n"
        f"TODAY'S QUESTIONS\n\n"
    )
 
    send_message(header + questions)
    print("Questions sent successfully.")
 
# ── Afternoon: Send Answers ───────────────────────────────────────────────────
def run_answers():
    if not os.path.exists(QUESTIONS_FILE):
        send_message(
            "UPSC Bot: Answer key could not be sent.\n"
            "Reason: latest_questions.txt not found.\n"
            "The morning job may not have run or committed the file."
        )
        print("Questions file missing.")
        return
 
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = f.read()
 
    meta = {}
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
 
    print(f"Generating answers for: {meta}")
    prompt  = ANSWER_PROMPT.format(questions=questions)
    answers = generate(prompt)
 
    header = (
        f"UPSC MAINS ANSWER KEY\n"
        f"Date: {meta.get('date', 'Today')}\n"
        f"========================================\n"
        f"GS-1 : {meta.get('gs1', '')}\n"
        f"GS-4 : {meta.get('gs4', '')}\n"
        f"========================================\n\n"
    )
 
    send_message(header + answers)
    print("Answers sent successfully.")
 
# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "questions"
    print(f"Running in mode: {mode}")
    try:
        if mode == "questions":
            run_questions()
        elif mode == "answers":
            run_answers()
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
    except Exception as e:
        send_error(mode, e)
        raise
 
if __name__ == "__main__":
    main()
 
