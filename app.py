# app.py

import streamlit as st
from openai import OpenAI

# --- Page Configuration ---
# Sets the page title and a wider layout for better readability.
st.set_page_config(
    page_title="Salesforce AI Assistant MVP",
    layout="wide"
)

# --- App Title and Description ---
st.title("Salesforce AI Assistant MVP 🤖")
st.markdown("This tool transforms a Jira user story into a business-friendly solution and then a technical blueprint.")

# --- Securely Initialize the OpenAI Client ---
# Streamlit automatically reads the OPENAI_API_KEY from the .streamlit/secrets.toml file.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    # If the key is not found, display an error message.
    st.error("OpenAI API key not found. Please add it to your .streamlit/secrets.toml file.")
    st.stop() # Stop the app from running further.

# --- Session State Initialization ---
# Streamlit reruns the script on every interaction. 'session_state' is a way to store
# variables and remember what has happened (e.g., a solution has been generated).
if 'layman_solution' not in st.session_state:
    st.session_state.layman_solution = ""
if 'technical_solution' not in st.session_state:
    st.session_state.technical_solution = ""

# --- UI: Input for User Story ---
# A text area for the user to paste their story.
user_story = st.text_area(
    "**1. Paste Your Jira User Story Here:**",
    height=150,
    placeholder="As a <type of user>, I want <some goal> so that <some reason>."
)

# --- Button to Generate Layman's Solution ---
# The 'if st.button(...)' block only runs when the user clicks the button.
if st.button("Generate Layman's Solution", type="primary"):
    if user_story:
        # A spinner shows a loading message while the AI is working.
        with st.spinner("🧠 The Business Analyst AI is thinking..."):
            layman_prompt = f"""
            You are a Salesforce Business Analyst. Your job is to read a user story and explain the functional solution in simple, non-technical terms for a business stakeholder to approve. Do not include any technical jargon. Focus on the user's experience.
            User Story:
            ---
            {user_story}
            ---
            Please generate a simple, clear explanation of what will happen in the system.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": layman_prompt}]
            )
            # We save the result to our session_state "memory".
            st.session_state.layman_solution = response.choices[0].message.content
            # Clear any old technical solution if we re-generate.
            st.session_state.technical_solution = ""
    else:
        st.warning("Please enter a user story first.")

# --- Display Layman's Solution and Approval Button ---
# This section is only shown IF a layman's solution exists in our session_state memory.
if st.session_state.layman_solution:
    st.subheader("2. Business Approval Step")
    st.markdown(st.session_state.layman_solution)

    if st.button("Looks Good! Generate Technical Solution", type="primary"):
        with st.spinner("🛠️ The Technical Architect AI is designing the solution..."):
            technical_prompt = f"""
            You are a Salesforce Technical Architect. Create a detailed technical solution based on a user story and an approved functional description. Recommend best practices like Trigger Handler frameworks.
            User Story:
            ---
            {user_story}
            ---
            Approved Functional Description:
            ---
            {st.session_state.layman_solution}
            ---
            Generate a technical solution direction for a Salesforce developer.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": technical_prompt}]
            )
            st.session_state.technical_solution = response.choices[0].message.content

# --- Display Final Technical Solution ---
# This section is only shown IF a technical solution exists.
if st.session_state.technical_solution:
    st.subheader("3. Technical Solution")
    # st.code displays text in a nice, formatted code block.
    st.code(st.session_state.technical_solution, language="markdown")