# services/claude_service.py

import streamlit as st
import anthropic
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
    if "ANTHROPIC_API_KEY" in st.secrets and st.secrets["ANTHROPIC_API_KEY"]:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        CLIENT_INITIALIZED = True
except Exception as e:
    st.error(f"Failed to initialize Anthropic client. Error: {e}")

ANALYSIS_MODEL_NAME = "claude-sonnet-4-20250514"
CODE_GENERATION_MODEL_NAME = "claude-opus-4-20250514" 

def _is_client_configured():
    if not CLIENT_INITIALIZED:
        st.error("Anthropic API key not found. Please add it to your secrets.")
    return CLIENT_INITIALIZED

def extract_entities_from_story(user_story):
    if not _is_client_configured(): return []
    user_prompt = get_entity_extraction_prompt(user_story)
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=1024,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        response_text = response.content[0].text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:-3]
        response_data = json.loads(response_text)
        return response_data.get("objects", []) if response_data else []
    except Exception as e:
        st.error(f"An error occurred during entity extraction: {e}"); return []

def analyze_story(user_story, schema_context):
    if not _is_client_configured(): return None
    user_prompt = get_triage_prompt(user_story, schema_context)
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=2048,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        response_text = response.content[0].text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:-3]
        return json.loads(response_text)
    except Exception as e:
        st.error(f"An error occurred during story analysis: {e}"); return None

def generate_solution_with_answers(user_story, context_from_answers, schema_context):
    if not _is_client_configured(): return "Error: Anthropic client not initialized."
    user_prompt = get_final_solution_prompt(user_story, context_from_answers, schema_context)
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=4096,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        return response.content[0].text
    except Exception as e:
        st.error(f"An error occurred with the Anthropic API: {e}"); return "Sorry, an error occurred with the AI."

def generate_technical_solution(user_story, solution_overview, schema_context):
    if not _is_client_configured(): return "Error: Anthropic client not initialized."
    user_prompt = get_technical_solution_prompt(user_story, solution_overview, schema_context)
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=4096,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        return response.content[0].text
    except Exception as e:
        st.error(f"An error occurred with the Anthropic API: {e}"); return "Sorry, an error occurred with the AI."

def get_generation_order(filenames):
    if not _is_client_configured(): return filenames
    user_prompt = get_dependency_analysis_prompt(filenames)
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=1024,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        response_text = response.content[0].text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:-3]
        response_data = json.loads(response_text)
        return response_data.get("generation_order", filenames)
    except Exception as e:
        st.warning(f"Could not determine file dependencies, using default order. Reason: {e}")
        return filenames

def generate_single_file_code(full_context, file_path):
    if not _is_client_configured(): return None
    user_prompt = get_single_file_code_prompt(full_context, file_path)
    try:
        response = client.messages.create(model=CODE_GENERATION_MODEL_NAME, max_tokens=4096,temperature=0.0, messages=[{"role": "user", "content": user_prompt}])
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            first_newline = response_text.find('\n')
            if first_newline != -1: response_text = response_text[first_newline+1:]
            if response_text.endswith("```"): response_text = response_text[:-3]
        return response_text.strip()
    except Exception as e:
        st.error(f"An error occurred during code generation: {e}"); return f"// Error generating code for {file_path}: {e}"

def get_chat_response(messages):
    if not _is_client_configured(): return "Error: Anthropic client not initialized."
    system_prompt = get_chat_system_prompt()
    claude_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    try:
        response = client.messages.create(model=ANALYSIS_MODEL_NAME, max_tokens=4096,temperature=0.0, system=system_prompt, messages=claude_messages)
        return response.content[0].text
    except Exception as e:
        st.error(f"An error occurred with the Anthropic API: {e}"); return "Sorry, I encountered an error. Please try again."