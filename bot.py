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

# ── Model Fallback Chain ──────────────────────────────────────────────────────
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

# ── Case Study Scenario Types ─────────────────────────────────────────────────
CASE_STUDY_TYPES = [
    "civil servant facing political pressure to bend rules for a powerful politician",
    "IAS officer discovering corruption by a senior colleague during disaster relief",
    "district collector caught between orders from state government and welfare of tribal community",
    "IPS officer facing dilemma of exposing a scam that implicates his own department",
    "civil servant whose family member is involved in a case under his own jurisdiction",
    "officer managing communal tension where political masters want biased action",
    "bureaucrat pressured to manipulate data in a government welfare scheme report",
    "young IAS officer witnessing land acquisition irregularities benefiting private builders",
    "officer in-charge of relief funds during floods facing pressure to divert funds",
    "civil servant asked to overlook environmental violations by an influential industry",
    "officer facing whistleblower retaliation after reporting financial fraud",
    "administrator dealing with conflict between local community rights and national project",
    "civil servant pressured to issue false certificates to benefit a political party",
    "officer balancing transparency demands of RTI applicant against official secrecy",
    "IAS officer discovering child labour in a factory owned by a senior politician",
]

# ── 15 GS-1 Topics ────────────────────────────────────────────────────────────
GS1_TOPICS = [
    {
        "topic": "Indian Society: Diversity, Caste and Social Stratification",
        "pyq_themes": [
            "Caste as a social institution vs political mobilisation tool",
            "Sanskritisation and Westernisation — M.N. Srinivas framework",
            "Social mobility and structural barriers in Indian society",
            "Reservation policy and its impact on social justice and merit",
            "Intersection of caste, class and gender in India",
        ]
    },
    {
        "topic": "Role of Women: Empowerment, Violence and Representation",
        "pyq_themes": [
            "Feminisation of poverty — causes and intergenerational impact",
            "Self Help Groups as grassroots instruments of women empowerment",
            "Women in political representation — 33% reservation debate",
            "Domestic violence, POCSO Act and legal safeguards for women",
            "Gender gap in workforce participation — LFPR data from NFHS-5",
        ]
    },
    {
        "topic": "Communalism, Regionalism and Secularism",
        "pyq_themes": [
            "Constitutional secularism vs Western secularism — key differences",
            "Communalism as a political mobilisation tool in electoral democracy",
            "Regionalism — threat or opportunity for national integration",
            "Role of media and social media in amplifying communal narratives",
            "Composite culture and syncretic traditions as India's strength",
        ]
    },
    {
        "topic": "Population: Demographic Dividend, Ageing and Migration",
        "pyq_themes": [
            "Demographic dividend — preconditions and risk of missing the window",
            "Ageing population and social security challenges in India",
            "Rural to urban migration — push pull factors and consequences",
            "Population policy beyond fertility control — holistic approach",
            "Brain drain vs brain gain — Indian diaspora and remittances",
        ]
    },
    {
        "topic": "Poverty, Social Exclusion and Inclusive Growth",
        "pyq_themes": [
            "Multidimensional poverty beyond income — MPI India 2023 findings",
            "Social exclusion of Scheduled Tribes, Dalits and minorities",
            "Role of MGNREGA in rural poverty alleviation — achievements and gaps",
            "Inclusive growth vs trickle down economics — policy debate",
            "Linkage between poverty, lack of education and social immobility",
        ]
    },
    {
        "topic": "Urbanisation: Smart Cities, Slums and Urban Governance",
        "pyq_themes": [
            "Slum formation as a consequence of governance failure and migration",
            "Smart Cities Mission — promise vs ground reality on the field",
            "Urban local bodies and 74th Constitutional Amendment — decentralisation",
            "Push pull factors of rural to urban migration and urban infrastructure stress",
            "Urban waste management — solid waste, plastic and water challenges",
        ]
    },
    {
        "topic": "Globalisation and Its Impact on Indian Society",
        "pyq_themes": [
            "Cultural homogenisation vs cultural diversity under globalisation",
            "Globalisation and widening income inequality in India",
            "Impact on Indian family structure — rise of nuclear families and individualism",
            "Gig economy and changing nature of work and labour rights",
            "Globalisation and women — empowerment or new forms of exploitation",
        ]
    },
    {
        "topic": "Social Movements and Civil Society in India",
        "pyq_themes": [
            "Role of civil society in strengthening democracy and accountability",
            "New social movements — environment, gender, tribal rights",
            "Naxalism as a socioeconomic problem — causes and government response",
            "Anti-corruption movements and their impact on governance",
            "Role of NGOs in development and their regulation challenges",
        ]
    },
    {
        "topic": "Education: Access, Equity, Quality and NEP 2020",
        "pyq_themes": [
            "NEP 2020 — key features, significance and implementation challenges",
            "Digital divide and its impact on education equity in India",
            "Dropout rates among girls, SC/ST communities — causes and solutions",
            "Commercialisation of education and its impact on quality",
            "Role of education in social mobility and breaking poverty cycle",
        ]
    },
    {
        "topic": "Health: Public Health System and Social Determinants",
        "pyq_themes": [
            "Social determinants of health — poverty, gender, caste and nutrition",
            "Ayushman Bharat — achievements and gaps in universal health coverage",
            "Mental health as a public health challenge in India",
            "Malnutrition — stunting, wasting and anaemia data from NFHS-5",
            "Urban-rural divide in healthcare access and infrastructure",
        ]
    },
    {
        "topic": "Tribal Communities: Issues, Rights and Constitutional Safeguards",
        "pyq_themes": [
            "Fifth and Sixth Schedule — constitutional safeguards for tribal areas",
            "Forest Rights Act 2006 — implementation challenges and conflicts",
            "Displacement of tribal communities due to development projects",
            "Naxalism and tribal grievances — developmental vs security approach",
            "Cultural identity and assimilation vs integration debate for tribals",
        ]
    },
    {
        "topic": "Minority Issues, Secularism and Social Harmony",
        "pyq_themes": [
            "Constitutional provisions for protection of minorities in India",
            "Communal harmony and role of state in managing diversity",
            "Linguistic minorities and protection under Article 29 and 30",
            "Religious conversion debate — freedom vs allegations of coercion",
            "Uniform Civil Code — debate on personal laws and gender justice",
        ]
    },
    {
        "topic": "Child Labour, Bonded Labour and Human Trafficking",
        "pyq_themes": [
            "Child labour — causes, legal framework and ground reality in India",
            "Bonded labour as a form of modern slavery — extent and response",
            "Human trafficking — vulnerable groups, routes and legal provisions",
            "Role of education and poverty alleviation in eliminating child labour",
            "International conventions — ILO, UNCRC and India's obligations",
        ]
    },
    {
        "topic": "Social Capital, NGOs and Voluntary Sector",
        "pyq_themes": [
            "Social capital — concept, types and its role in development",
            "Role of NGOs in bridging state and citizen — examples from India",
            "FCRA amendments and their impact on civil society space",
            "Cooperative movement — success of Amul and lessons for rural development",
            "Community participation in governance — SHGs, gram sabhas, water committees",
        ]
    },
    {
        "topic": "Media, Social Media and Their Role in Society",
        "pyq_themes": [
            "Media as the fourth pillar of democracy — responsibility and accountability",
            "Fake news and misinformation — threat to social harmony and democracy",
            "Social media and political mobilisation — positive and negative dimensions",
            "Digital divide and unequal access to information in India",
            "Regulation of media and social media — free speech vs hate speech debate",
        ]
    },
]

# ── 15 GS-4 Topics ────────────────────────────────────────────────────────────
GS4_TOPICS = [
    {
        "topic": "Ethics and Human Interface: Determinants of Ethical Behaviour",
        "pyq_themes": [
            "Role of family, society and educational institutions in value formation",
            "Influence of religion and culture on ethical behaviour of individuals",
            "Conscience as moral guide vs conformity to social norms",
            "Moral relativism vs universal ethics in governance context",
            "Ethics of care — Gilligan's framework applied to public service",
        ]
    },
    {
        "topic": "Attitude: Formation, Change and Social Influence",
        "pyq_themes": [
            "Cognitive dissonance and attitude change in administrators",
            "Role of attitude in ethical administrative decision making",
            "Prejudice and stereotyping — impact on governance and service delivery",
            "Social influence on individual moral choices in bureaucracy",
            "Moral courage to challenge wrong institutional attitudes",
        ]
    },
    {
        "topic": "Civil Services Values: Integrity, Impartiality and Empathy",
        "pyq_themes": [
            "Integrity beyond legal compliance — spirit vs letter of law",
            "Impartiality when political pressure conflicts with official duty",
            "Empathy as foundation of citizen-centric public service delivery",
            "Dedication to public service vs personal career advancement",
            "Objectivity and evidence based policy making in administration",
        ]
    },
    {
        "topic": "Emotional Intelligence in Governance and Leadership",
        "pyq_themes": [
            "Self awareness and self regulation in crisis management by officers",
            "Empathy as a tool for inclusive and responsive administration",
            "Emotional intelligence vs IQ in effective leadership",
            "Managing stress and preventing burnout in civil services",
            "EI in conflict resolution, team building and stakeholder management",
        ]
    },
    {
        "topic": "Moral Thinkers: Gandhi and Ambedkar",
        "pyq_themes": [
            "Gandhian ethics — trusteeship, non-violence and sarvodaya in governance",
            "Ambedkar — constitutional morality vs social morality distinction",
            "Gandhi vs Ambedkar — debate on caste, religion and social reform",
            "Relevance of Gandhian principles to modern public administration",
            "Ambedkar's vision of social justice and its constitutional embodiment",
        ]
    },
    {
        "topic": "Moral Thinkers: Aristotle, Kant, Plato and Kautilya",
        "pyq_themes": [
            "Aristotle's virtue ethics — character and habits of an ideal civil servant",
            "Kant's categorical imperative — universal maxim in administrative decisions",
            "Plato's philosopher king — relevance to civil services ideal",
            "Kautilya's Arthashastra — ethical statecraft and duties of a ruler",
            "Utilitarianism — Bentham and Mill — greatest good for greatest number",
        ]
    },
    {
        "topic": "Probity in Governance: Transparency, Accountability and RTI",
        "pyq_themes": [
            "RTI Act as a fundamental tool of democratic accountability",
            "Whistleblower protection and ethics of institutional dissent",
            "Conflict of interest — identification and management in public office",
            "Ethical dilemmas of loyalty to institution vs public interest",
            "Citizen's charter and service delivery ethics in administration",
        ]
    },
    {
        "topic": "Conflict of Interest, Whistleblowing and Ethical Governance",
        "pyq_themes": [
            "Conflict of interest — direct, indirect and revolving door problems",
            "Whistleblower dilemma — duty to expose vs loyalty and self-preservation",
            "Nolan Principles of public life — selflessness, integrity, accountability",
            "ARC recommendations on ethics in governance",
            "Role of ombudsman and Lokpal in ensuring ethical governance",
        ]
    },
    {
        "topic": "Corruption: Causes, Effects, Prevention and Ethics",
        "pyq_themes": [
            "Systemic causes of corruption — institutional, cultural and economic",
            "Corruption and its impact on development, trust and governance",
            "Prevention of Corruption Act and its effectiveness",
            "Role of technology and e-governance in reducing corruption",
            "Ethical dimensions — why good people sometimes act corruptly",
        ]
    },
    {
        "topic": "Corporate Governance and Business Ethics",
        "pyq_themes": [
            "Corporate social responsibility — legal mandate vs ethical imperative",
            "Stakeholder vs shareholder model of corporate governance",
            "Ethical issues in advertising, marketing and consumer rights",
            "Environmental ethics and corporate accountability",
            "Insider trading, fraud and ethical failures in corporate India",
        ]
    },
    {
        "topic": "Ethics in Public and Private Relationships",
        "pyq_themes": [
            "Conflict between personal ethics and official duty for civil servants",
            "Family obligations vs public duty — where to draw the line",
            "Ethics of gift-giving and hospitality in public service",
            "Friendship, loyalty and nepotism in administrative decisions",
            "Privacy and confidentiality obligations in public office",
        ]
    },
    {
        "topic": "Social Influence, Persuasion and Moral Development",
        "pyq_themes": [
            "Kohlberg's stages of moral development — relevance to civil services",
            "Social influence and groupthink in bureaucratic decision making",
            "Role of moral exemplars and leadership in shaping organisational ethics",
            "Peer pressure and institutional culture in ethical behaviour",
            "Persuasion vs manipulation — ethical boundaries in administration",
        ]
    },
    {
        "topic": "Human Values: Lessons from Lives, Literature and History",
        "pyq_themes": [
            "Lessons in public service ethics from lives of great administrators",
            "Role of literature and arts in moral development of civil servants",
            "Historical examples of ethical courage — Indian freedom struggle",
            "Values of tolerance, compassion and humility in governance",
            "Importance of role models and mentors in value formation",
        ]
    },
    {
        "topic": "Ethical Concerns in International Relations and Global Issues",
        "pyq_themes": [
            "Ethics of humanitarian intervention vs state sovereignty",
            "Climate justice — ethical responsibilities of developed vs developing nations",
            "Nuclear ethics — deterrence, disarmament and moral dilemmas",
            "Refugee crisis — ethical obligations of nations under international law",
            "Ethics of economic sanctions and their humanitarian impact",
        ]
    },
    {
        "topic": "Case Studies: Disaster, Corruption, Political Pressure and Dilemmas",
        "pyq_themes": [
            "Ethical allocation of scarce resources during disaster relief",
            "Dilemma of reporting corruption by a superior officer",
            "Handling political interference in transfer and posting decisions",
            "Ethical dimensions of implementing unpopular but necessary policies",
            "Balancing transparency demands with official secrecy obligations",
        ]
    },
]

def today_topics():
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    day = ist.timetuple().tm_yday
    gs1       = GS1_TOPICS[day % len(GS1_TOPICS)]
    gs4       = GS4_TOPICS[day % len(GS4_TOPICS)]
    case_type = CASE_STUDY_TYPES[day % len(CASE_STUDY_TYPES)]
    return gs1, gs4, case_type, ist.strftime("%d %b %Y")

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

# ── Gemini with Fallback ──────────────────────────────────────────────────────
def generate(prompt: str) -> str:
    for model in MODELS:
        for attempt in range(2):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                print(f"Success with model: {model}")
                return resp.text
            except Exception as e:
                if "429" in str(e):
                    print(f"{model} quota exhausted, switching to next model...")
                    break
                print(f"{model} attempt {attempt+1} failed: {e}")
                if attempt == 0:
                    time.sleep(15)
    raise RuntimeError("All models exhausted. Check your Gemini API quota.")

# ── Question Prompt ───────────────────────────────────────────────────────────
QUESTION_PROMPT = """You are a senior UPSC Mains paper setter with 20 years of experience.
You have studied all UPSC GS-1 and GS-4 papers from 2013 to 2024 in detail.

DATE: {date_str}

TODAY'S TOPICS:
GS-1 (Society): {gs1_topic}
PYQ Themes: {gs1_themes}

GS-4 (Ethics): {gs4_topic}
PYQ Themes: {gs4_themes}

Today's Case Study Scenario Type: {case_type}

YOUR TASK:
Generate exactly 6 FRESH questions specific to {date_str}.
Every question must be brand new — never reuse wording from any previous set.
Do NOT copy previous year questions directly.
Frame fresh questions inspired by the PYQ themes from a unique angle suited for {date_str}.

OUTPUT FORMAT (plain text only, no asterisks, no symbols, no markdown):

========================================
GS-1 SOCIETY: {gs1_topic}
========================================

Q1. (10 Marks | 150 words)
[Write one analytical question of 2-3 sentences.
Must test conceptual understanding and analytical ability, not memory recall.
Style: "Examine the...", "Discuss the...", "Analyse the role of..."]

Q2. (10 Marks | 150 words)
[Write one different conceptual question of 2-3 sentences.
Must approach the topic from a different angle than Q1.
Style: "What do you understand by...", "How has... shaped...", "Critically examine..."]

Q3. (15 Marks | 250 words)
[Write one question of 3-4 sentences requiring multi-dimensional analysis.
Must demand coverage of at least 3 dimensions: social, economic, political, gender or legal.
Style: "Critically analyse...", "Examine the... in the context of...", "Discuss... with suitable examples."]

========================================
GS-4 ETHICS: {gs4_topic}
========================================

Q4. (10 Marks | 150 words)
[Write one conceptual ethics theory question of 2-3 sentences.
Must test understanding of ethical concepts, values and philosophical ideas.
Must relate to civil services or governance context.
Style: "What do you understand by...", "Explain the significance of...", "How does... influence..."]

Q5. (10 Marks | 150 words)
[Write one applied ethics question of 2-3 sentences.
Must require application of ethical concepts to real administrative situations.
Different angle from Q4.
Style: "How should a civil servant...", "Examine the ethical dimensions of...", "What are the challenges of..."]

Q6. (20 Marks | 300 words) — CASE STUDY
[Write a full UPSC-style case study exactly as follows:

Paragraph 1 — Background and Context (3-4 lines):
Introduce the civil servant by name (use common Indian name), designation, department and location.
Describe the work situation and background in specific detail.

Paragraph 2 — The Dilemma (3-4 lines):
Describe the ethical conflict that arises involving: {case_type}
Show pressure from multiple sides: superior, political leader, public, institution or family.
Make the dilemma realistic, complex and specific — not generic.

Paragraph 3 — Stakeholders and Consequences (2-3 lines):
Mention who will be affected by the officer's decision and in what way.
Show that both action and inaction have serious consequences.

Sub-questions (exactly as UPSC format):
(a) Identify and discuss the ethical issues involved in this case. (50 words)
(b) What are the options available to [officer name]? Evaluate each option with its merits and demerits. (100 words)
(c) What course of action would you recommend and why? How would you handle the pressures involved? (150 words)]

STRICT RULES:
- Follow marks and word limits exactly as specified
- No sub-parts for Q1 to Q5
- Case study must be detailed and realistic — not a one-liner
- Plain text only — no asterisks, hashtags or symbols
- Questions must be analytical not factual recall
- Each question must approach the topic from a different angle
"""

# ── Answer Prompt ─────────────────────────────────────────────────────────────
ANSWER_PROMPT = """You are a UPSC Mains topper and expert answer writer.
You have scored above 130 in GS-1 and GS-4. Write model answers for all 6 questions below.

ANSWER STRUCTURE FOR Q1 TO Q5:

Q[number]. [Topic] | [Marks] | [Word Limit]

INTRODUCTION:
[2-3 lines. Choose one style:
- Powerful quote by Gandhi, Ambedkar, Aristotle, Kant or Supreme Court judgment
- Shocking fact or data point that defines the problem
- Constitutional article or SDG goal linkage
- Aspirational or futuristic opening line
Never start with "In India..." or "Since ancient times..." or "It is said that..."]

BODY:
[Numbered points with CAPITAL HEADING on its own line.
Under each heading: 2 crisp lines of explanation using UPSC keywords.
Then: one specific Indian example — name the scheme, case, committee, state or year.
Number of points by marks:
- 10 marks: 3 points
- 15 marks: 5 points]

WAY FORWARD: (include only where policy reform or future action is relevant)
- 3 specific bullet points
- Link to committees, NEP 2020, SDG goals, Vision India 2047 or government schemes

CONCLUSION:
[1-2 lines. Choose one style:
- SDG goal linkage with specific goal number
- Vision India 2047 or Amrit Kaal reference
- Futuristic or aspirational closing
- Relevant quote
Never repeat the introduction.]

---

ANSWER STRUCTURE FOR Q6 CASE STUDY (20 Marks | 300 words):

Q6. Case Study | 20 Marks | 300 words

INTRODUCTION:
[2 lines identifying the core ethical conflict in the case.]

(a) ETHICAL ISSUES INVOLVED: (50 words)
[List as numbered points:
1. [Issue name]: one line explanation
2. [Issue name]: one line explanation
3. [Issue name]: one line explanation
Cover: conflict of interest, integrity, loyalty vs public interest, moral courage, probity]

(b) OPTIONS AVAILABLE TO [OFFICER NAME]: (100 words)
[List each option clearly:
Option 1 — [Action]: Merit: ... Demerit: ...
Option 2 — [Action]: Merit: ... Demerit: ...
Option 3 — [Action]: Merit: ... Demerit: ...
Evaluate honestly — no option is perfect]

(c) RECOMMENDED COURSE OF ACTION: (150 words)
[Clearly state which option you recommend and why.
Show how to handle each pressure mentioned in the case.
Reference: Nolan Principles / ARC recommendations / relevant Supreme Court judgment.
End with how this upholds constitutional values and public trust.]

CONCLUSION:
[1-2 lines. Quote or value-based closing on ethical governance.]

---

WORD LIMITS (strictly follow):
- 10-mark answer: 150 words
- 15-mark answer: 250 words
- 20-mark case study: 300 words total across all sub-parts

DIMENSIONS TO COVER:
GS-1 Society: Social / Economic / Political / Gender / Legal / Regional / Data / Global comparison
GS-4 Ethics: Individual ethics / Institutional ethics / Constitutional morality /
             Philosophical backing (Gandhi, Kant, Aristotle, Ambedkar) /
             Emotional intelligence / Governance reform / Stakeholder impact

UPSC KEYWORDS — USE NATURALLY:
GS-1: social capital, demographic dividend, feminisation of poverty, social mobility,
      constitutional morality, majoritarianism, composite culture, intersectionality,
      social stratification, inclusive growth, SDG-1, SDG-5, SDG-10
GS-4: moral courage, conflict of interest, probity, public trust, value pluralism,
      whistleblower, consequentialism, deontological ethics, categorical imperative,
      Nolan principles, emotional intelligence, constitutional ethics,
      ARC recommendations, fiduciary duty

DATA TO CITE WHERE RELEVANT:
NFHS-5 (2021), NCRB 2023, Economic Survey 2024, Census 2011,
World Bank Report, UNDP HDI 2024, MoSPI, ILO Report 2023,
Supreme Court judgments, CAG reports, SECC data, NEP 2020

LANGUAGE RULES:
- Simple and direct English — avoid complex vocabulary
- Every sentence must add value — no filler phrases
- Plain text only — no asterisks, hashtags or markdown symbols
- Indian examples must be specific — name the scheme, officer, state or year
- Answers must feel like a topper wrote them — structured, confident, precise

QUESTIONS TO ANSWER:
{questions}
"""

# ── Files ─────────────────────────────────────────────────────────────────────
QUESTIONS_FILE = "latest_questions.txt"
META_FILE      = "latest_meta.json"

# ── Morning: Send Questions ───────────────────────────────────────────────────
def run_questions():
    gs1, gs4, case_type, date_str = today_topics()
    print(f"Date: {date_str}")
    print(f"GS1: {gs1['topic']} | GS4: {gs4['topic']}")

    # Check if today's questions already sent — skip if same date
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            existing_meta = json.load(f)
        if existing_meta.get("date") == date_str:
            print(f"Questions for {date_str} already sent today. Skipping.")
            return

    prompt = QUESTION_PROMPT.format(
        date_str   = date_str,
        gs1_topic  = gs1["topic"],
        gs1_themes = "\n- ".join(gs1["pyq_themes"]),
        gs4_topic  = gs4["topic"],
        gs4_themes = "\n- ".join(gs4["pyq_themes"]),
        case_type  = case_type,
    )

    print("Generating new questions from Gemini...")
    questions = generate(prompt)
    print("Questions generated successfully.")

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        f.write(f"Date: {date_str}\n\n")
        f.write(questions)

    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "gs1": gs1["topic"],
            "gs4": gs4["topic"],
            "date": date_str
        }, f)

    print(f"Files saved: {QUESTIONS_FILE}, {META_FILE}")

    header = (
        f"UPSC MAINS DAILY PRACTICE\n"
        f"Date: {date_str}\n"
        f"========================================\n"
        f"GS-1 Topic : {gs1['topic']}\n"
        f"GS-4 Topic : {gs4['topic']}\n"
        f"========================================\n\n"
        f"Total: 6 Questions | 75 Marks\n"
        f"Q1, Q2 — 10M each (GS-1 Society)\n"
        f"Q3     — 15M (GS-1 Society)\n"
        f"Q4, Q5 — 10M each (GS-4 Ethics Theory)\n"
        f"Q6     — 20M Case Study (GS-4 Ethics)\n\n"
        f"Write your answers before 1:00 PM IST.\n"
        f"Model answer key drops at 1:00 PM.\n\n"
        f"TODAY'S QUESTIONS:\n\n"
    )

    send_message(header + questions)
    print("Questions sent successfully.")

# ── Afternoon: Send Answers ───────────────────────────────────────────────────
def run_answers():
    if not os.path.exists(QUESTIONS_FILE):
        send_message(
            "UPSC Bot Alert:\n"
            "Answer key could not be sent today.\n"
            "Reason: Morning questions file not found.\n"
            "Check if the 8 AM workflow ran and committed latest_questions.txt."
        )
        print("Questions file missing.")
        return

    meta = {}
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)

    # Validate that the questions file is from today — skip if stale
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_str = ist.strftime("%d %b %Y")
    if meta.get("date") != today_str:
        send_message(
            f"UPSC Bot Alert: Answer key skipped for {today_str}.\n"
            f"Reason: Questions file is from {meta.get('date', 'unknown')} — "
            f"morning commit/push may have failed.\n"
            f"Check GitHub Actions log for the 8 AM run."
        )
        print(f"Stale questions file (from {meta.get('date', 'unknown')}). Skipping answers.")
        return

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = f.read()

    print(f"Generating answers for: {meta}")

    prompt  = ANSWER_PROMPT.format(questions=questions)
    answers = generate(prompt)

    header = (
        f"UPSC MAINS MODEL ANSWER KEY\n"
        f"Date: {meta.get('date', 'Today')}\n"
        f"========================================\n"
        f"GS-1 : {meta.get('gs1', '')}\n"
        f"GS-4 : {meta.get('gs4', '')}\n"
        f"========================================\n\n"
        f"Compare with your answers.\n"
        f"Focus on dimensions and examples you missed.\n\n"
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
