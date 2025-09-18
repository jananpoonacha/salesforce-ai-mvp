# services/openai_service.py

import streamlit as st
from openai import OpenAI
import json
from prompts import (
    get_triage_prompt, 
    get_final_solution_prompt, 
    get_technical_solution_prompt, 
    get_code_generation_prompt,
    get_chat_system_prompt
)

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None

def analyze_story(user_story):
    """
    Sends the user story to the AI for initial analysis.
    Returns a parsed JSON object or None if an error occurs.
    """
    if not client:
        st.error("OpenAI client not initialized. Check your API key.")
        return None
        
    prompt = get_triage_prompt(user_story)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}")
        return None

def generate_solution_with_answers(user_story, context_from_answers):
    """
    Generates the Solution Overview after the user answers questions.
    Returns the solution text as a string.
    """
    if not client: return "Error: OpenAI client not initialized."
    prompt = get_final_solution_prompt(user_story, context_from_answers)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_technical_solution(user_story, solution_overview):
    """
    Generates the technical solution based on the approved Solution Overview.
    Returns the technical solution text as a string.
    """
    if not client: return "Error: OpenAI client not initialized."
    prompt = get_technical_solution_prompt(user_story, solution_overview)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_salesforce_code(user_story, solution_overview, technical_solution):
    """
    Generates Salesforce code files based on the full context.
    Returns a parsed JSON object with a list of files.
    """
    if not client:
        st.error("OpenAI client not initialized. Check your API key.")
        return None

    prompt = get_code_generation_prompt(user_story, solution_overview, technical_solution)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"An error occurred during code generation: {e}")
        return None

def get_chat_response(messages):
    """
    Gets a response from the AI based on conversation history.
    """
    if not client: return "Error: OpenAI client not initialized."
    system_prompt = {"role": "system", "content": get_chat_system_prompt()}
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_prompt] + messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}")
        return "Sorry, I encountered an error. Please try again."