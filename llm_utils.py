import os
from openai import OpenAI
import json
import re

client = OpenAI(base_url= "https://api.groq.com/openai/v1")

# # expects OPENAI_API_KEY in env
# openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_profile(profile: dict) -> str:
    prompt = (
        "/no_think Given this wallet profile JSON, provide a concise health score (0–100) "
        "and highlight strengths/weaknesses:  \n\n"
        f"{profile}\n\nSummary:"
    )
    resp = client.chat.completions.create(model="mistral-saba-24b",
    messages=[{"role":"user","content": prompt}],
    temperature=0.7,
    max_tokens=2000)

    content = resp.choices[0].message.content.strip()
    content_clean = re.sub(r"^<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content_clean

def generate_handle(profile: dict) -> str:
    prompt = (
        "/no_think Generate a unique, wallet-themed social handle (no spaces) for a user "
        "based on this profile:\n\n"
        f"{profile}\n\nHandle:"
    )
    resp = client.chat.completions.create(model="mistral-saba-24b",
    messages=[{"role":"user","content": prompt}],
    temperature=0.9,
    max_tokens=10,)
    content = resp.choices[0].message.content.strip()
    content_clean = re.sub(r"^<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content_clean

def analyze_entities(transactions: list) -> dict:
    """
    Send up to ~2000 tokens of raw transaction data to the LLM and
    return a dict with 'prominent_entities', 'usernames', 'companies', and other 'insights'.
    """
    # truncate or sample to fit token budget
    sample = transactions[:100]
    prompt = (
        "Given this JSON array of Aptos transactions, identify:\n"
        "- prominent_entities (contracts, modules, addresses)\n"
        "- usernames mentioned in arguments\n"
        "- companies or organizations interacted with\n"
        "- action_categories and any notable patterns\n"
        "Return ONLY a JSON object with keys:\n"
        "  'prominent_entities': [],\n"
        "  'usernames': [],\n"
        "  'companies': [],\n"
        "  'action_categories': [],\n"
        "  'insights': {}\n\n"
        f"{json.dumps(sample)}"
    )
    resp = client.chat.completions.create(
        model="qwen-qwq-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    print(f"LLM response: {content}")  # debug output
    # remove any <think>...</think> wrapper
    content_clean = re.sub(r"^<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    try:
        return json.loads(content_clean)
    except json.JSONDecodeError:
        return {"error": "invalid JSON from LLM", "raw": content_clean}
