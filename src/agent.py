import os
from dotenv import load_dotenv
from openai import OpenAI
from src.text_prompt import build_prompt
import re
import json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

MODEL_NAME = "gpt-4o-mini"

def _call_openai(prompt: str, temperature=0.7, max_tokens=400):
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def generate_headlines(topic, tone=None, profile_summary=None, n_variations=3):
    prompt = build_prompt("headline", topic=topic, tone=tone, profile_summary=profile_summary)
    text = _call_openai(prompt, temperature=0.8, max_tokens=200)
    lines = [l.strip(" -–•0123456789.") .strip() for l in text.split("\n") if l.strip()]
    return lines[:n_variations] if lines else [text]

def generate_body(headline, tone=None, audience=None, keywords=None, adaptive_keywords=None, profile_summary=None):
    combined_keywords = ""
    if keywords:
        combined_keywords += keywords
    if adaptive_keywords:
        combined_keywords += ", " + ", ".join(adaptive_keywords)
    prompt = build_prompt(
        "body",
        headline=headline,
        tone=tone,
        audience=audience,
        keywords=combined_keywords if combined_keywords else None,
        profile_summary=profile_summary
    )
    return _call_openai(prompt, temperature=0.75, max_tokens=500)

def generate_ctas(topic, profile_summary=None):
    prompt = build_prompt("cta", topic=topic, profile_summary=profile_summary)
    text = _call_openai(prompt, temperature=0.7, max_tokens=150)
    lines = [l.strip("-•0123456789. ") for l in text.split("\n") if l.strip()]
    return lines[:3] if lines else [text]

def generate_engagement_score(headline, body, audience=None, profile_summary=None):
    prompt = build_prompt("engagement", headline=headline, keywords=body, audience=audience, topic=headline, profile_summary=profile_summary)
    resp = _call_openai(prompt, temperature=0.3, max_tokens=80)
    m = re.search(r"([1-9]|10)", resp)
    score = m.group(0) if m else resp
    return str(score) + " — " + resp

def refine_post(refinement_input, draft, mode=None):
    prompt = build_prompt(
        "rewrite",
        headline=draft.get("body"),
        keywords=refinement_input,
        mode=mode,
        profile_summary=draft.get("profile_summary")
    )
    return _call_openai(prompt, temperature=0.75, max_tokens=400)

def extract_tone_from_profile(profile_summary):
    prompt = build_prompt("extract_tone", profile_summary=profile_summary)
    resp = _call_openai(prompt, temperature=0.2, max_tokens=300)
    try:
        obj = json.loads(resp)
        return obj
    except Exception:
        return {"tone_summary": resp}

def generate_adaptive_keywords(topic, profile_summary=None, n=10):
    """
    Generates strong adaptive keywords that are different from user keywords
    for natural incorporation into the post body.
    """
    # Use the valid "keywords" stage
    prompt = build_prompt("keywords", topic=topic, profile_summary=profile_summary)
    text = _call_openai(prompt, temperature=0.6, max_tokens=150)
    
    # Split and clean keywords
    items = [k.strip(" .-#") for k in text.replace("\n", ",").split(",") if k.strip()]
    
    # Remove duplicates and return top n
    seen = set()
    out = []
    for k in items:
        if k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out[:n]

# -----------------------------------------------------------
# Conversational follow-up agent to ask clarifying questions
# -----------------------------------------------------------

def conversational_followup(draft):
    """
    Ask a follow-up question based on gaps in the draft.
    """
    topic = draft.get("topic", "")
    tone = draft.get("tone")
    audience = draft.get("audience")
    keywords = draft.get("user_keywords")
    profile = draft.get("profile_summary")

    if not tone:
        return "Do you want this post to sound more professional, casual, or story-driven?"

    if not audience:
        return "Who are you hoping this post resonates with? (e.g., hiring managers, peers, founders)"

    if not keywords:
        return "Any keywords you'd like included? (e.g., AI, leadership, biotech, product thinking)"

    if topic and len(topic) < 10:
        return "Could you tell me a bit more about what angle you want to take on this topic?"

    return "Would you like this to be more concise, more narrative, or more punchy?"


