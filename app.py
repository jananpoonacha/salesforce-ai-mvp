# app.py (Main file with Wizard and Chat tabs)

import streamlit as st
from services import jira_service, openai_service
from ui_components import chat_view

# --- Page Configuration ---
st.set_page_config(page_title="Design Orchestrator", layout="wide", initial_sidebar_state="collapsed")
st.title("Design Orchestrator 🚀 (by Rocket AI)")

# --- Session State Initialization ---
# Initialize ALL session state variables here, in the main app file.
if 'user_story' not in st.session_state: st.session_state.user_story = ""
if 'solution_overview' not in st.session_state: st.session_state.solution_overview = ""
if 'technical_solution' not in st.session_state: st.session_state.technical_solution = ""
if 'jira_ticket_id' not in st.session_state: st.session_state.jira_ticket_id = None
if 'url_processed' not in st.session_state: st.session_state.url_processed = False
if 'questions_to_ask' not in st.session_state: st.session_state.questions_to_ask = []
if 'generated_code' not in st.session_state: st.session_state.generated_code = None
# Initialize chat history for the chat tab
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you design a Salesforce solution today? You can provide a Jira ticket ID or paste a user story."}]


wizard_tab, chat_tab = st.tabs(["Step-by-Step Wizard", "Chat Assistant"])

with wizard_tab:
    st.header("Wizard Mode")
    st.markdown("Follow a structured, step-by-step process to generate your solution.")
    
    def handle_jira_fetch(ticket_id):
        with st.spinner(f"Fetching {ticket_id} from Jira..."):
            story_text = jira_service.fetch_story(ticket_id)
            if story_text:
                st.session_state.user_story = story_text
                st.session_state.jira_ticket_id = ticket_id
                st.session_state.solution_overview, st.session_state.technical_solution, st.session_state.questions_to_ask, st.session_state.generated_code = "", "", [], None
                st.success(f"Successfully fetched story for {ticket_id}!")

    issue_key_from_url = st.query_params.get("issueKey")
    if issue_key_from_url and not st.session_state.url_processed:
        st.session_state.url_processed = True
        handle_jira_fetch(issue_key_from_url)

    if issue_key_from_url:
        tab_names = ["Fetch from Jira", "Paste Manually"]
    else:
        tab_names = ["Paste Manually", "Fetch from Jira"]

    created_tabs = st.tabs(tab_names)
    manual_tab, jira_tab = created_tabs[tab_names.index("Paste Manually")], created_tabs[tab_names.index("Fetch from Jira")]

    with manual_tab:
        st.text_area("**1. Paste Your User Story Here:**", key="user_story_manual", value=st.session_state.user_story, height=200, on_change=lambda: st.session_state.update(user_story=st.session_state.user_story_manual, jira_ticket_id=None, url_processed=True, solution_overview="", technical_solution="", questions_to_ask=[], generated_code=None))
    
    with jira_tab:
        st.subheader("Fetch User Story from Jira")
        jira_ticket_id_input = st.text_input("Enter Jira Ticket ID (e.g., PROJ-123)", value=issue_key_from_url or "")
        if st.button("Fetch from Jira"):
            if jira_ticket_id_input: handle_jira_fetch(jira_ticket_id_input)
            else: st.warning("Please enter a Jira Ticket ID.")

    if st.session_state.user_story:
        story_header = f"Current User Story ({st.session_state.jira_ticket_id})" if st.session_state.jira_ticket_id else "Current User Story"
        with st.expander(story_header, expanded=True): st.markdown(st.session_state.user_story)
        st.divider()

    if st.button("Analyze Story & Generate Solution Overview", type="primary", disabled=not st.session_state.user_story):
        with st.spinner("🧠 The AI Business Analyst is analyzing the story..."):
            response_data = openai_service.analyze_story(st.session_state.user_story)
            if response_data:
                st.session_state.solution_overview, st.session_state.technical_solution, st.session_state.questions_to_ask, st.session_state.generated_code = "", "", [], None
                if response_data.get("status") == "clear": st.session_state.solution_overview = response_data.get("solution", "")
                elif response_data.get("status") == "ambiguous": st.session_state.questions_to_ask = response_data.get("clarification_questions", [])

    if st.session_state.questions_to_ask:
        with st.expander("❓ The AI needs more information. Please clarify:", expanded=True):
            with st.form("qa_form"):
                user_answers = {}
                for i, q in enumerate(st.session_state.questions_to_ask):
                    if q.get("type", "single") == "multiple": user_answers[q['question']] = st.multiselect(q['question'], options=q['options'], key=f"q_{i}")
                    else: user_answers[q['question']] = st.radio(q['question'], options=q['options'], key=f"q_{i}")
                if st.form_submit_button("Submit Answers & Generate Solution"):
                    with st.spinner("🧠 Thanks! Regenerating solution..."):
                        context_lines = []
                        for question, answer in user_answers.items():
                            formatted_answer = ", ".join(answer) if isinstance(answer, list) and answer else "None selected" if isinstance(answer, list) else answer
                            context_lines.append(f"- Regarding '{question}', the user specified: '{formatted_answer}'")
                        st.session_state.solution_overview = openai_service.generate_solution_with_answers(st.session_state.user_story, "\n".join(context_lines))
                        st.session_state.questions_to_ask = []

    if st.session_state.solution_overview:
        with st.expander("Business Approval Step (Solution Overview)", expanded=True):
            st.markdown(st.session_state.solution_overview)
            st.divider()
            if st.button("Generate Technical Solution", type="primary"):
                with st.spinner("🛠️ The Technical Architect AI is designing..."):
                    st.session_state.technical_solution = openai_service.generate_technical_solution(st.session_state.user_story, st.session_state.solution_overview)
                    st.session_state.generated_code = None
                    st.rerun()

    if st.session_state.technical_solution:
        with st.expander("Technical Solution (Editable)", expanded=True):
            st.text_area(label="You can edit the technical solution below:", value=st.session_state.technical_solution, height=400, key="technical_solution")
            if st.button("Generate Code", type="primary"):
                with st.spinner("💻 The AI Developer is generating code..."):
                    response_data = openai_service.generate_salesforce_code(st.session_state.user_story, st.session_state.solution_overview, st.session_state.technical_solution)
                    if response_data and "files" in response_data: st.session_state.generated_code = response_data["files"]
                    else: st.error("Code generation failed or returned an invalid format."); st.session_state.generated_code = None
        
        if st.session_state.generated_code:
            st.subheader("Generated Code")
            file_tabs = st.tabs([file["file_name"] for file in st.session_state.generated_code])
            for tab, file_data in zip(file_tabs, st.session_state.generated_code):
                with tab:
                    st.code(file_data["code_content"], language='apex' if '.cls' in file_data["file_name"] else 'xml')
                    st.download_button(label=f"Download {file_data['file_name']}", data=file_data["code_content"], file_name=file_data["file_name"], mime='text/plain')
        st.divider()
        st.subheader("Final Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Restart & Regenerate"):
                st.session_state.update(solution_overview="", technical_solution="", questions_to_ask=[], generated_code=None)
                st.rerun()
        with col2:
            if st.button("Confirm to Jira", disabled=not st.session_state.get("jira_ticket_id"), help="This option is only available for stories fetched directly from Jira."):
                with st.spinner("Appending solutions to Jira ticket..."):
                    text_to_append = f"""\n\nh2. Generated by Rocket AI 🚀\n{{panel:title=Solution Direction|borderColor=#82B5F8}}\n{st.session_state.solution_overview}\n{{panel}}\n{{panel:title=Technical Solution|borderColor=#4285F4}}\n{{code:language=markdown}}\n{st.session_state.technical_solution}\n{{code}}\n{{panel}}"""
                    jira_service.update_story_description(st.session_state.jira_ticket_id, text_to_append)

with chat_tab:
    chat_view.render()