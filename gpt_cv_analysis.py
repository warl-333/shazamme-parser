import sys
import os
import openai


openai.api_key = os.getenv("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")

def summarize_with_gpt(cv_text: str) -> dict:
    prompt = (
        "Summarise the following resume text, providing a brief overview of:\n"
        "- Role experience\n- Skills\n- Degree(s)\n- Location\n- Education institutions\n"
        "Respond in JSON format with keys: 'name', 'skills', 'degrees', 'location', "
        "'universities', 'email', 'phone', 'roles'.\n\nResume:\n\n" + cv_text
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    try:
        json_result = response['choices'][0]['message']['content']
        return eval(json_result)  # Or use `json.loads()` if it’s valid JSON
    except Exception as e:
        print("Failed to parse GPT response:", e)
        return {}

def merge_cv_data(spacy_data: dict, gpt_data: dict) -> dict:
    merged = {}

    # Merge basic fields
    keys = ["name", "email", "phone", "location"]
    for key in keys:
        merged[key] = spacy_data.get(key) or gpt_data.get(key) or ""

    # Merge lists like skills/degrees/universities
    for key in ["skills", "degrees", "universities"]:
        spacy_set = set(spacy_data.get(key, []))
        gpt_set = set(gpt_data.get(key, [])) if isinstance(gpt_data.get(key), list) else set()
        merged[key] = sorted(spacy_set.union(gpt_set))

    # Optional: include GPT role summary
    merged["roles"] = gpt_data.get("roles", "")

    return merged

# === Wrapper function to call from main parser ===
def parse_cv_with_gpt(full_text: str, filename: str, spacy_data: dict) -> dict:
    spacy_data = {
        "filename": filename,
        "name": extract_name(full_text),
        "email": extract_email(full_text),
        "phone": extract_phone(full_text),
        "skills": extract_skills(full_text),
        "degrees": extract_degrees(full_text),
        "universities": extract_universities(full_text),
        "location": extract_location(full_text),
    }

    gpt_data = summarize_with_gpt(full_text)
    combined = merge_cv_data(spacy_data, gpt_data)
    combined["full_text"] = full_text[:1000]  # Optional preview
    return combined
