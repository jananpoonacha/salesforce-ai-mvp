# ui_components/chat_view.py

import streamlit as st
from services import jira_service, openai_service
import re

def handle_user_input(prompt):
    """
    This function processes the user's text prompt, generates a response,
    and adds both to the chat history.
    """
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- Generate and add assistant response ---
    # Check if the prompt is a command to fetch a Jira ticket
    jira_match = re.search(r"([A-Z]+-[0-9]+)", prompt.upper())
    
    if jira_match:
        ticket_id = jira_match.group(1)
        story_text = jira_service.fetch_story(ticket_id)
        if story_text:
            # If fetch is successful, create a new prompt for the AI
            contextual_prompt = f"""Here is the user story from Jira ticket {ticket_id}:\n\n---\n{story_text}\n---\n\nPlease analyze this story and generate a Solution Overview."""
            # We add this to history so the AI has context for the conversation
            st.session_state.messages.append({"role": "user", "content": contextual_prompt})
            response = openai_service.get_chat_response(st.session_state.messages)
        else:
            response = f"Sorry, I couldn't fetch the details for {ticket_id}. Please check the ticket ID and try again."
    else:
        # If it's not a Jira command, get a general chat response
        response = openai_service.get_chat_response(st.session_state.messages)
    
    # Add the assistant's final response to the message history
    st.session_state.messages.append({"role": "assistant", "content": response})

def handle_file_upload(uploaded_file):
    """
    This function processes an uploaded file, generates a response,
    and adds the interaction to the chat history.
    """
    # To prevent reprocessing the same file, use a session state flag.
    if "last_uploaded_file" not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.last_uploaded_file = uploaded_file.name
        
        user_prompt = f"Uploaded file: `{uploaded_file.name}`"
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        try:
            # Read the content of the uploaded file
            story_content = uploaded_file.getvalue().decode("utf-8")
            
            # Create a more detailed prompt for the AI
            contextual_prompt = f"""Here is the user story from the uploaded file '{uploaded_file.name}':\n\n---\n{story_content}\n---\n\nPlease analyze this story and generate a Solution Overview."""
            st.session_state.messages.append({"role": "user", "content": contextual_prompt})

            # Get the AI's response
            response = openai_service.get_chat_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            error_message = f"Sorry, I couldn't read or process the file. Error: {e}"
            st.session_state.messages.append({"role": "assistant", "content": error_message})


def render():
    """
    Renders the chat UI. The logic is now separated: display first, then handle input.
    """
    st.subheader("Conversational Interface")

    # --- 1. Display chat messages from history ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 2. Handle new input (either from file upload or text input) ---
    # We create the uploader first. If a file is uploaded, Streamlit re-runs the script.
    uploaded_file = st.file_uploader(
        "Or upload a user story from a file (.txt, .md)", 
        type=['txt', 'md']
    )
    
    # The text input is created last.
    prompt = st.chat_input("What would you like to do?")

    # The logic to process the input happens *after* the widgets are created.
    if uploaded_file is not None:
        handle_file_upload(uploaded_file)
        # We re-run the script here to display the result of the file upload immediately
        # and clear the uploader widget.
        st.rerun()

    if prompt:
        handle_user_input(prompt)
        # We re-run the script here to display the result of the text input immediately.
        st.rerun()