# 🏦 LoanBot — AI Personal Loan Eligibility Assistant

Built by B T Sai Teja

## What It Does
LoanBot is an AI-powered personal loan eligibility assistant that:
- Instantly checks loan eligibility based on salary, CIBIL, employment type
- Calculates EMI estimates using real lending formulas
- Explains rejection reasons clearly
- Answers personal loan FAQs via conversational AI
- Uses prompt engineering to prevent hallucinations in financial decisions

## Why I Built This
Managing a ₹35,000 Cr personal loan portfolio at Axis Bank, I saw that 40%+ of RM bandwidth was spent answering repetitive eligibility queries that are entirely rule-based. LoanBot automates this — freeing relationship managers for high-value conversion conversations.

## Tech Stack
- **LLM:** Arcee-ai trinity-large
- **Framework:** Streamlit
- **Language:** Python
- **Prompt Engineering:** Chain-of-thought + structured JSON output + hallucination guardrails

## How To Run

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Run the app
```bash
streamlit run app.py
```

### Step 3 — Enter your OpenAI API key in the sidebar
Get a free key at platform.openai.com (comes with $5 free credit)

## Key Technical Decisions

### Hallucination Prevention
The biggest challenge with LLMs in financial applications is hallucination — the model confidently giving wrong eligibility verdicts. Solved by:
1. Forcing structured JSON output format
2. Explicit instruction to return "REVIEW NEEDED" when inputs are ambiguous
3. Low temperature (0.1) for deterministic financial reasoning
4. Chain-of-thought reasoning embedded in system prompt

### Domain Knowledge Encoding
Encoded real personal lending eligibility rules into the system prompt:
- FOIR (Fixed Obligation to Income Ratio) calculation
- CIBIL score thresholds
- Employment stability requirements
- City-wise minimum income thresholds
- Loan amount to salary ratio limits

## Modes
1. **Eligibility Checker** — Structured form input → AI eligibility verdict with EMI estimate
2. **Loan FAQ Chat** — Free-form conversational Q&A about personal loans

## Future Improvements
- Connect to live CIBIL API for real score fetch
- Add bank-specific eligibility rules (Axis, HDFC, ICICI)
- Add document checklist generator
- WhatsApp bot integration for broader reach
