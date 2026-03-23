import streamlit as st
import openai
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LoanBot – AI Loan Eligibility Assistant",
    page_icon="🏦",
    layout="centered"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stApp { max-width: 750px; margin: auto; }
    .loan-header {
        background: linear-gradient(135deg, #1A56DB 0%, #1e40af 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .loan-header h1 { color: white; font-size: 1.8rem; margin: 0; }
    .loan-header p { color: #bfdbfe; margin: 0.5rem 0 0 0; font-size: 0.95rem; }
    .result-box {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #1A56DB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-top: 1rem;
    }
    .eligible { border-left-color: #16a34a !important; }
    .not-eligible { border-left-color: #dc2626 !important; }
    .review { border-left-color: #d97706 !important; }
    .chat-msg-user {
        background: #EBF0FF;
        border-radius: 12px 12px 2px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .chat-msg-bot {
        background: white;
        border-radius: 12px 12px 12px 2px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border: 1px solid #e2e8f0;
    }
    .disclaimer {
        font-size: 0.75rem;
        color: #94a3b8;
        text-align: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="loan-header">
    <h1>🏦 LoanBot</h1>
    <p>AI-powered Personal Loan Eligibility Assistant · Built on BFSI domain expertise</p>
</div>
""", unsafe_allow_html=True)

# ── API Key input ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Get your free API key at platform.openai.com"
    )
    st.markdown("---")
    st.markdown("### 📊 About LoanBot")
    st.markdown("""
    LoanBot uses GPT-4 with domain-specific prompt engineering to:
    - Check personal loan eligibility instantly
    - Calculate EMI estimates
    - Explain rejection reasons clearly
    - Guide on document requirements
    - Answer loan FAQs
    
    Built using real BFSI domain knowledge from managing a ₹35,000 Cr personal loan portfolio.
    """)
    st.markdown("---")
    mode = st.radio(
        "Mode",
        ["Eligibility Checker", "Loan FAQ Chat"],
        help="Switch between structured eligibility check and free-form Q&A"
    )

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are LoanBot, an expert AI assistant for personal loan eligibility assessment built on deep BFSI domain knowledge.

You assess personal loan eligibility based on these rules:

ELIGIBILITY CRITERIA:
1. Age: 21-58 years for salaried, 25-65 for self-employed
2. Minimum net monthly salary: ₹20,000 for tier-2 cities, ₹25,000 for metro cities
3. CIBIL score: 750+ = Strong, 700-749 = Review needed, below 700 = Likely rejected
4. Employment stability: Minimum 1 year at current employer for salaried
5. FOIR (Fixed Obligation to Income Ratio): Total EMIs including new loan should not exceed 50% of net monthly income
6. Loan amount: Typically up to 20-24x net monthly salary
7. Employment type: Salaried (PSU/MNC preferred), Self-employed with ITR proof

EMI CALCULATION:
- Use approximate formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
- Standard interest rate: 10.5% to 14% per annum for eligible candidates
- Use 12% as default for calculations
- Convert annual rate to monthly: r = 12%/12 = 1% per month

RESPONSE FORMAT:
Always respond in this exact JSON format:
{
  "verdict": "ELIGIBLE" or "NOT ELIGIBLE" or "REVIEW NEEDED",
  "confidence": "High" or "Medium" or "Low",
  "summary": "One line verdict summary",
  "reasons": ["reason 1", "reason 2"],
  "emi_estimate": "₹X,XXX per month" or "N/A",
  "max_loan_amount": "₹X lakhs approximately" or "N/A",
  "improvements": ["improvement 1 if not eligible"] or [],
  "documents_needed": ["doc1", "doc2", "doc3"],
  "next_steps": "What the applicant should do next"
}

HALLUCINATION PREVENTION RULES:
- If any critical input is missing, set verdict to "REVIEW NEEDED" and list missing info in reasons
- Never guess or assume income, CIBIL score, or loan amount if not provided
- Always base EMI on actual inputs, never fabricate numbers
- If scenario is genuinely ambiguous, say so clearly

For FAQ mode: Answer concisely in plain English without JSON format. Be helpful, accurate, and never give wrong financial advice. Always add a disclaimer to consult the bank directly for final decisions."""

FAQ_SYSTEM_PROMPT = """You are LoanBot, a friendly and knowledgeable personal loan FAQ assistant with deep BFSI expertise.

Answer questions about:
- Personal loan interest rates (typical range 10.5%-24% in India)
- EMI calculations and prepayment
- CIBIL score and how to improve it
- Documents required for personal loans
- Loan tenure options (12-60 months typically)
- Top-up loans, balance transfer
- Rejection reasons and how to overcome them
- Processing fees, foreclosure charges
- Difference between secured and unsecured loans

Rules:
- Be concise and helpful
- Use simple language
- Give specific numbers where possible
- Always add: "For final decisions, please consult your bank directly."
- Never give wrong financial advice
- If unsure, say so clearly"""


def check_eligibility(inputs: dict, api_key: str) -> dict:
    """Call OpenAI API to check loan eligibility"""
    client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

    user_message = f"""Check personal loan eligibility for this applicant:

- Age: {inputs['age']} years
- Employment Type: {inputs['employment_type']}
- Net Monthly Salary: ₹{inputs['salary']:,}
- Current Employer Tenure: {inputs['tenure']} years
- CIBIL Score: {inputs['cibil']}
- Requested Loan Amount: ₹{inputs['loan_amount']:,}
- Preferred Tenure: {inputs['loan_tenure']} months
- Existing Monthly EMIs: ₹{inputs['existing_emis']:,}
- City Type: {inputs['city_type']}

Assess eligibility and respond in the exact JSON format specified."""

    response = client.chat.completions.create(
        model="google/gemma-3-12b-it:free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=800
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def chat_faq(messages: list, api_key: str) -> str:
    """Call OpenAI API for FAQ chat"""
    client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)
    response = client.chat.completions.create(
        model="google/gemma-3-12b-it:free",
        messages=[{"role": "system", "content": FAQ_SYSTEM_PROMPT}] + messages,
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content


# ── ELIGIBILITY CHECKER MODE ──────────────────────────────────────────────────
if mode == "Eligibility Checker":
    st.markdown("### 📋 Enter Applicant Details")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age (years)", min_value=18, max_value=70, value=28)
        employment_type = st.selectbox(
            "Employment Type",
            ["Salaried - MNC/Large Company", "Salaried - SME/Startup",
             "Salaried - Government/PSU", "Self Employed - Business", "Self Employed - Professional"]
        )
        salary = st.number_input(
            "Net Monthly Salary (₹)",
            min_value=10000,
            max_value=500000,
            value=50000,
            step=5000,
            format="%d"
        )
        tenure = st.selectbox(
            "Years at Current Employer",
            [0.5, 1, 2, 3, 5, 7, 10],
            index=2
        )

    with col2:
        cibil = st.number_input("CIBIL Score", min_value=300, max_value=900, value=750)
        loan_amount = st.number_input(
            "Loan Amount Required (₹)",
            min_value=50000,
            max_value=5000000,
            value=500000,
            step=50000,
            format="%d"
        )
        loan_tenure = st.selectbox(
            "Preferred Loan Tenure (months)",
            [12, 24, 36, 48, 60],
            index=2
        )
        existing_emis = st.number_input(
            "Existing Monthly EMIs (₹)",
            min_value=0,
            max_value=200000,
            value=0,
            step=1000,
            format="%d"
        )

    city_type = st.selectbox(
        "City Type",
        ["Metro (Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata)",
         "Tier-2 City (Vizag, Pune, Jaipur, etc.)",
         "Tier-3 / Small City"]
    )

    st.markdown("")
    check_btn = st.button("🔍 Check Eligibility", type="primary", use_container_width=True)

    if check_btn:
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar to use LoanBot.")
        else:
            with st.spinner("Analysing eligibility using AI..."):
                try:
                    inputs = {
                        "age": age,
                        "employment_type": employment_type,
                        "salary": salary,
                        "tenure": tenure,
                        "cibil": cibil,
                        "loan_amount": loan_amount,
                        "loan_tenure": loan_tenure,
                        "existing_emis": existing_emis,
                        "city_type": city_type
                    }
                    result = check_eligibility(inputs, api_key)

                    # Determine styling
                    verdict = result.get("verdict", "REVIEW NEEDED")
                    box_class = "eligible" if verdict == "ELIGIBLE" else \
                                "not-eligible" if verdict == "NOT ELIGIBLE" else "review"
                    verdict_emoji = "✅" if verdict == "ELIGIBLE" else \
                                    "❌" if verdict == "NOT ELIGIBLE" else "⚠️"
                    verdict_color = "#16a34a" if verdict == "ELIGIBLE" else \
                                    "#dc2626" if verdict == "NOT ELIGIBLE" else "#d97706"

                    st.markdown(f"""
                    <div class="result-box {box_class}">
                        <h3 style="color:{verdict_color}; margin:0">{verdict_emoji} {verdict}</h3>
                        <p style="color:#64748b; margin:0.25rem 0 0 0; font-size:0.9rem">
                            Confidence: {result.get('confidence','N/A')} &nbsp;|&nbsp; {result.get('summary','')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Estimated EMI", result.get("emi_estimate", "N/A"))
                    with col_b:
                        st.metric("Max Eligible Amount", result.get("max_loan_amount", "N/A"))

                    if result.get("reasons"):
                        st.markdown("#### 📌 Key Factors")
                        for r in result["reasons"]:
                            st.markdown(f"- {r}")

                    if result.get("improvements"):
                        st.markdown("#### 💡 How To Improve Eligibility")
                        for imp in result["improvements"]:
                            st.markdown(f"- {imp}")

                    if result.get("documents_needed"):
                        st.markdown("#### 📄 Documents Required")
                        docs = result["documents_needed"]
                        cols = st.columns(2)
                        for i, doc in enumerate(docs):
                            cols[i % 2].markdown(f"✓ {doc}")

                    if result.get("next_steps"):
                        st.info(f"**Next Steps:** {result['next_steps']}")

                    st.markdown('<p class="disclaimer">⚠️ This is an AI-powered indicative assessment only. Final eligibility is determined by the bank based on their internal policies and credit assessment.</p>', unsafe_allow_html=True)

                except json.JSONDecodeError:
                    st.error("Could not parse AI response. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ── FAQ CHAT MODE ─────────────────────────────────────────────────────────────
else:
    st.markdown("### 💬 Ask Me Anything About Personal Loans")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hi! I'm LoanBot 👋 Ask me anything about personal loans — interest rates, EMI calculations, CIBIL scores, documents, or anything else. How can I help?"
        })

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-bot">🏦 {msg["content"]}</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Ask about personal loans...")

    if user_input:
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.markdown(f'<div class="chat-msg-user">👤 {user_input}</div>', unsafe_allow_html=True)

            with st.spinner("Thinking..."):
                try:
                    chat_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                    reply = chat_faq(chat_history, api_key)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.markdown(f'<div class="chat-msg-bot">🏦 {reply}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.markdown('<p class="disclaimer">⚠️ LoanBot provides informational guidance only. Always consult your bank for final loan decisions.</p>', unsafe_allow_html=True)
