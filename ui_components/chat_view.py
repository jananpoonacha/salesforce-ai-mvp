# ui_components/chat_view.py

import streamlit as st
import re

# We dynamically import the correct AI service in the main app.py file
# and pass it to this render function.

def render(ai_service):
    """
    Renders the chat UI and handles the conversational logic.
    """
    st.subheader(f"Conversational Interface (Powered by {st.session_state.ai_provider})")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you design a Salesforce solution today?"}]

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # We need to import the jira_service here, as it's used in the chat logic
    from services import jira_service

    # Handle file upload
    uploaded_file = st.file_uploader("Or upload a user story from a file (.txt, .md)", type=['txt', 'md'], key="chat_uploader")
    
    if uploaded_file is not None:
        if "last_uploaded_file" not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.last_uploaded_file = uploaded_file.name
            user_prompt = f"Uploaded file: `{uploaded_file.name}`"
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            try:
                story_content = uploaded_file.getvalue().decode("utf-8")
                contextual_prompt = f"Here is the user story from the uploaded file '{uploaded_file.name}':\n\n---\n{story_content}\n---\n\nPlease analyze this story and generate a Solution Overview."
                st.session_state.messages.append({"role": "user", "content": contextual_prompt})
                response = ai_service.get_chat_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I couldn't read the file. Error: {e}"})
            st.rerun()

    # Handle text input
    if prompt := st.chat_input("What would you like to do?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                jira_match = re.search(r"([A-Z]+-[0-9]+)", prompt.upper())
                
                if jira_match:
                    ticket_id = jira_match.group(1)
                    story_text = jira_service.fetch_story(ticket_id)
                    if story_text:
                        contextual_prompt = f"Here is the user story from Jira ticket {ticket_id}:\n\n---\n{story_text}\n---\n\nPlease analyze this story and generate a Solution Overview."
                        st.session_state.messages.append({"role": "user", "content": contextual_prompt})
                        response = ai_service.get_chat_response(st.session_state.messages)
                    else:
                        response = f"Sorry, I couldn't fetch the details for {ticket_id}."
                else:
                    response = ai_service.get_chat_response(st.session_state.messages)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "last_uploaded_file" in st.session_state:
                    del st.session_state.last_uploaded_file
                st.rerun()