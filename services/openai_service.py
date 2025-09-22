# services/openai_service.py

import streamlit as st
from openai import OpenAI
import json
from prompts import (
    get_triage_prompt, 
    get_final_solution_prompt, 
    get_technical_solution_prompt, 
    get_single_file_code_prompt,
    get_chat_system_prompt,
    get_entity_extraction_prompt,
    get_dependency_analysis_prompt
)

# --- Initialization ---
CLIENT_INITIALIZED = False
try:
    if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        CLIENT_INITIALIZED = True
except Exception as e:
    st.error(f"Failed to initialize OpenAI client. Error: {e}")

MODEL_NAME = "gpt-4o"

def _is_client_configured():
    if not CLIENT_INITIALIZED:
        st.error("OpenAI API key not found. Please add it to your secrets.")
    return CLIENT_INITIALIZED

def extract_entities_from_story(user_story):
    if not _is_client_configured(): return []
    prompt = get_entity_extraction_prompt(user_story)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        response_data = json.loads(response.choices[0].message.content)
        return response_data.get("objects", [])
    except Exception as e:
        st.error(f"An error occurred during entity extraction with OpenAI: {e}")
        return []

def analyze_story(user_story, schema_context):
    if not _is_client_configured(): return None
    prompt = get_triage_prompt(user_story, schema_context)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"An error occurred during story analysis with OpenAI: {e}"); return None

def generate_solution_with_answers(user_story, context_from_answers, schema_context):
    if not _is_client_configured(): return "Error: OpenAI client not initialized."
    prompt = get_final_solution_prompt(user_story, context_from_answers, schema_context)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_technical_solution(user_story, solution_overview, schema_context):
    if not _is_client_configured(): return "Error: OpenAI client not initialized."
    prompt = get_technical_solution_prompt(user_story, solution_overview, schema_context)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_generation_order(filenames):
    if not _is_client_configured(): return filenames
    prompt = get_dependency_analysis_prompt(filenames)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        response_data = json.loads(response.choices[0].message.content)
        return response_data.get("generation_order", filenames)
    except Exception as e:
        st.warning(f"Could not determine file dependencies with OpenAI, using default order. Reason: {e}")
        return filenames

def generate_single_file_code(full_context, file_name):
    if not _is_client_configured(): return None
    prompt = get_single_file_code_prompt(full_context, file_name)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.choices[0].message.content.strip()
        # Clean up markdown code blocks if the AI includes them
        if response_text.startswith("```"):
            first_newline = response_text.find('\n')
            if first_newline != -1:
                response_text = response_text[first_newline+1:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        return response_text.strip()
    except Exception as e:
        st.error(f"An error occurred during code generation with OpenAI: {e}")
        return f"// Error generating code for {file_name}: {e}"

def get_chat_response(messages):
    if not _is_client_configured(): return "Error: OpenAI client not initialized."
    system_prompt = {"role": "system", "content": get_chat_system_prompt()}
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[system_prompt] + messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}")
        return "Sorry, I encountered an error. Please try again."