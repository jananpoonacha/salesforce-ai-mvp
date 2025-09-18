# services/jira_service.py

import streamlit as st
from jira import JIRA, JIRAError

def get_jira_client():
    """
    Initializes and returns a JIRA client using credentials from secrets.
    """
    try:
        jira_options = {'server': st.secrets["JIRA_SERVER"]}
        jira_client = JIRA(
            options=jira_options,
            basic_auth=(
                st.secrets["JIRA_USERNAME"],
                st.secrets["JIRA_API_TOKEN"]
            )
        )
        return jira_client
    except (KeyError, AttributeError) as e:
        st.error(f"Jira credentials not found in secrets.toml. Please check your configuration. Missing key: {e}")
        return None
    except JIRAError as e:
        st.error(f"Jira authentication failed: {e.status_code} - {e.text}")
        return None

def fetch_story(ticket_id):
    """
    Fetches the summary and description of a Jira ticket.
    """
    jira = get_jira_client()
    if not jira:
        return None
        
    try:
        issue = jira.issue(ticket_id)
        # Combine summary and description for the full context
        story_text = f"Summary: {issue.fields.summary}\n\nDescription:\n{issue.fields.description}"
        return story_text
    except JIRAError as e:
        if e.status_code == 404:
            st.error(f"Jira ticket '{ticket_id}' not found.")
        else:
            st.error(f"An error occurred while fetching from Jira: {e.text}")
        return None

def append_to_story(ticket_id, content, content_type="Solution Overview"):
    """
    Appends content to a Jira ticket's description.
    """
    jira = get_jira_client()
    if not jira:
        return False

    try:
        issue = jira.issue(ticket_id)
        new_comment = f"\n\n---\n*AI Generated {content_type}:*\n{content}"
        
        # Append the new content to the existing description
        current_description = issue.fields.description or ""
        issue.update(description=current_description + new_comment)
        
        st.success(f"Successfully appended {content_type} to Jira ticket {ticket_id}.")
        return True
    except JIRAError as e:
        st.error(f"Failed to update Jira ticket {ticket_id}: {e.text}")
        return False