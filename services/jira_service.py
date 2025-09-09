# services/jira_service.py

import streamlit as st
from jira import JIRA, JIRAError

def _get_jira_client():
    """Initializes and returns a Jira client using secrets. Returns None on failure."""
    try:
        jira_server = st.secrets["JIRA_SERVER"]
        jira_username = st.secrets["JIRA_USERNAME"]
        jira_token = st.secrets["JIRA_API_TOKEN"]
        return JIRA(server=jira_server, basic_auth=(jira_username, jira_token))
    except KeyError as e:
        st.error(f"Jira credential '{e.args[0]}' not found in secrets.")
        return None
    except Exception as e:
        st.error(f"Failed to connect to Jira: {e}")
        return None

def fetch_story(ticket_id):
    """Fetches a story from Jira and returns the formatted text."""
    jira_client = _get_jira_client()
    if not jira_client:
        return None

    try:
        issue = jira_client.issue(ticket_id)
        return f"**{issue.fields.summary}**\n\n{issue.fields.description}"
    except JIRAError as e:
        st.error(f"Jira Error: {e.text}. Check the ticket ID and your permissions.")
        return None

def update_story_description(ticket_id, text_to_append):
    """Appends text to a Jira story's description."""
    jira_client = _get_jira_client()
    if not jira_client:
        return False

    try:
        issue = jira_client.issue(ticket_id)
        current_description = issue.fields.description if issue.fields.description else ""
        new_description = current_description + text_to_append
        issue.update(description=new_description)
        st.success(f"Successfully appended solutions to Jira ticket {ticket_id}!")
        return True
    except JIRAError as e:
        st.error(f"Jira Error during update: {e.text}")
        return False