# app.py

import streamlit as st
import re
import os
from services import jira_service, claude_service as ai_service, salesforce_service
from ui_components import chat_view

st.set_page_config(page_title="Design Orchestrator", layout="wide", initial_sidebar_state="auto")
st.title("Design Orchestrator 🚀 (by Rocket AI)")

# --- Session State Initialization ---
if 'user_story' not in st.session_state: st.session_state.user_story = ""
if 'solution_overview' not in st.session_state: st.session_state.solution_overview = ""
if 'technical_solution' not in st.session_state: st.session_state.technical_solution = ""
if 'jira_ticket_id' not in st.session_state: st.session_state.jira_ticket_id = None
if 'url_processed' not in st.session_state: st.session_state.url_processed = False
if 'questions_to_ask' not in st.session_state: st.session_state.questions_to_ask = []
if 'files_to_generate' not in st.session_state: st.session_state.files_to_generate = []
if 'generated_code_files' not in st.session_state: st.session_state.generated_code_files = {}
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you design a Salesforce solution today?"}]
if "schema_context" not in st.session_state: st.session_state.schema_context = "No schema context available."
if "debug_info" not in st.session_state: st.session_state.debug_info = {}
if 'ai_provider' not in st.session_state: st.session_state.ai_provider = "Claude"

# --- Sidebar for Model Selection ---
with st.sidebar:
    st.header("Settings ⚙️")
    st.session_state.ai_provider = st.selectbox(
        "Choose your AI Provider",
        ("Claude", "OpenAI"),
        index=0 if st.session_state.ai_provider == "Claude" else 1
    )
    st.caption("The app will use this model for all generations.")

    if st.session_state.ai_provider == "Claude" and not st.secrets.get("ANTHROPIC_API_KEY"):
        st.error("Anthropic API key is not set in your secrets!")
    elif st.session_state.ai_provider == "OpenAI" and not st.secrets.get("OPENAI_API_KEY"):
        st.error("OpenAI API key is not set in your secrets!")

# --- Dynamic AI Service Loading ---
if st.session_state.ai_provider == "Claude":
    from services import claude_service as ai_service
else:
    from services import openai_service as ai_service

# --- Main App Tabs ---
wizard_tab, chat_tab = st.tabs(["Step-by-Step Wizard", "Chat Assistant"])

with wizard_tab:
    st.header("Wizard Mode")
    
    def get_schema_context_from_cache():
        st.session_state.debug_info = {}
        with st.spinner("Step 1/3: Asking AI to identify relevant Salesforce objects..."):
            sfdc_objects_from_ai = ai_service.extract_entities_from_story(st.session_state.user_story)
        st.session_state.debug_info["1a_AI_Suggested_Entities"] = sfdc_objects_from_ai
        sfdc_objects_from_keyword = salesforce_service.extract_sfdc_objects_by_keyword(st.session_state.user_story)
        st.session_state.debug_info["1b_Keyword_Suggested_Entities"] = sfdc_objects_from_keyword
        combined_objects = sorted(list(set(sfdc_objects_from_ai + sfdc_objects_from_keyword)))
        st.session_state.debug_info["1c_Combined_Entities_List"] = combined_objects

        if not combined_objects:
            st.warning("Could not identify any potential Salesforce objects. Proceeding without org context.")
            st.session_state.schema_context = "No schema context available."
            return
        
        with st.spinner(f"Step 2/3: Searching cache for schemas related to: {', '.join(combined_objects)}..."):
            schema_context_str, debug_data = salesforce_service.get_org_schema_for_objects(combined_objects)
            st.session_state.schema_context = schema_context_str
            st.session_state.debug_info.update(debug_data)

    def handle_jira_fetch(ticket_id):
        with st.spinner(f"Fetching {ticket_id} from Jira..."):
            story_text = jira_service.fetch_story(ticket_id)
            if story_text:
                st.session_state.update(user_story=story_text, jira_ticket_id=ticket_id, solution_overview="", technical_solution="", questions_to_ask=[], files_to_generate=[], generated_code_files={})
                st.success(f"Successfully fetched story for {ticket_id}!")

    issue_key_from_url = st.query_params.get("issueKey")
    if issue_key_from_url and not st.session_state.url_processed:
        st.session_state.url_processed = True
        handle_jira_fetch(issue_key_from_url)

    # --- INPUT SECTION ---
    with st.expander("Step 1: Provide a User Story", expanded=True):
        tab_names = ["Fetch from Jira", "Paste Manually"] if issue_key_from_url else ["Paste Manually", "Fetch from Jira"]
        created_tabs = st.tabs(tab_names)
        manual_tab, jira_tab = created_tabs[tab_names.index("Paste Manually")], created_tabs[tab_names.index("Fetch from Jira")]

        with manual_tab:
            st.text_area("**Paste Your User Story Here:**", key="user_story_manual", value=st.session_state.user_story, height=200, 
                          on_change=lambda: st.session_state.update(user_story=st.session_state.user_story_manual, jira_ticket_id=None, url_processed=True, solution_overview="", technical_solution="", questions_to_ask=[], files_to_generate=[], generated_code_files={}, debug_info={}))
        
        with jira_tab:
            st.subheader("Fetch User Story from Jira")
            jira_ticket_id_input = st.text_input("Enter Jira Ticket ID (e.g., PROJ-123)", value=issue_key_from_url or "")
            if st.button("Fetch from Jira"):
                if jira_ticket_id_input: handle_jira_fetch(jira_ticket_id_input)
                else: st.warning("Please enter a Jira Ticket ID.")

    if st.session_state.user_story:
        if st.button("Step 2: Analyze Story & Generate Solution Overview", type="primary", use_container_width=True):
            get_schema_context_from_cache() 
            with st.spinner(f"Step 3/3: AI Business Analyst ({st.session_state.ai_provider}) is analyzing..."):
                response_data = ai_service.analyze_story(st.session_state.user_story, st.session_state.schema_context)
                if response_data:
                    st.session_state.update(solution_overview="", technical_solution="", questions_to_ask=[], files_to_generate=[], generated_code_files={})
                    if response_data.get("status") == "clear": st.session_state.solution_overview = response_data.get("solution", "")
                    elif response_data.get("status") == "ambiguous": st.session_state.questions_to_ask = response_data.get("clarification_questions", [])

    # --- Q&A SECTION ---
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
                        st.session_state.solution_overview = ai_service.generate_solution_with_answers(st.session_state.user_story, "\n".join(context_lines), st.session_state.schema_context)
                        st.session_state.questions_to_ask = []
                        st.rerun()

    # --- OUTPUT SECTION ---
    if st.session_state.solution_overview:
        st.divider()
        st.header("Step 3: Review, Refine, and Generate Code")
        
        overview_tab, tech_tab, code_tab = st.tabs(["Solution Overview", "Technical Solution", "Generated Code"])

        with overview_tab:
            st.markdown(st.session_state.solution_overview)
            st.divider()
            if st.button("Generate Technical Solution", type="primary", use_container_width=True):
                get_schema_context_from_cache()
                with st.spinner("🛠️ The Technical Architect AI is designing..."):
                    st.session_state.technical_solution = ai_service.generate_technical_solution(st.session_state.user_story, st.session_state.solution_overview, st.session_state.schema_context)
                    st.session_state.files_to_generate, st.session_state.generated_code_files = [], {}
                    # MODIFIED: Add a success message to guide the user
                    st.success("Technical Solution generated! Click the 'Technical Solution' tab to view and edit it. 👉")
                    st.rerun()

        with tech_tab:
            if st.session_state.technical_solution:
                st.text_area(label="You can edit the technical solution below:", value=st.session_state.technical_solution, height=400, key="technical_solution")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Prepare Code Generation"):
                        with st.spinner("Parsing technical solution and analyzing dependencies..."):
                            st.session_state.debug_info["4_Text_For_Filename_Parsing"] = st.session_state.technical_solution
                            filenames = re.findall(r'(\w+\.(?:cls|trigger|xml|js|html|css))', st.session_state.technical_solution)
                            st.session_state.debug_info["5_Regex_Found_Filenames"] = filenames
                            if filenames:
                                sorted_filenames = ai_service.get_generation_order(filenames)
                                st.session_state.files_to_generate = sorted_filenames
                                st.session_state.debug_info["6_AI_Sorted_Filenames"] = sorted_filenames
                            else:
                                st.session_state.files_to_generate = []
                            st.session_state.generated_code_files = {}
                        st.rerun()
                
                with col2:
                    if st.button("Generate All Files", type="primary", disabled=not st.session_state.files_to_generate):
                        st.session_state.generated_code_files = {}
                        full_context = f"USER STORY:\n{st.session_state.user_story}\n\nSOLUTION OVERVIEW:\n{st.session_state.solution_overview}\n\nTECHNICAL SOLUTION:\n{st.session_state.technical_solution}"
                        progress_bar = st.progress(0, text="Starting code generation...")
                        
                        for i, filename in enumerate(st.session_state.files_to_generate):
                            progress_text = f"Generating file {i+1}/{len(st.session_state.files_to_generate)}: `{filename}`"
                            st.info(progress_text)
                            generated_code = ai_service.generate_single_file_code(full_context, filename)
                            st.session_state.generated_code_files[filename] = generated_code
                            progress_bar.progress((i + 1) / len(st.session_state.files_to_generate), text=progress_text)
                        
                        st.success("✅ Code generation complete!")
                
                if st.session_state.files_to_generate:
                    st.write("**Generation Plan (in order):**")
                    st.write(" ➡️ ".join(f"`{name}`" for name in st.session_state.files_to_generate))
            else:
                st.info("A technical solution must be generated before you can prepare or generate code.")

        with code_tab:
            if st.session_state.generated_code_files:
                filenames_with_code = list(st.session_state.generated_code_files.keys())
                code_display_tabs = st.tabs(filenames_with_code)
                
                for i, tab in enumerate(code_display_tabs):
                    filename = filenames_with_code[i]
                    code_content = st.session_state.generated_code_files[filename]
                    with tab:
                        st.code(code_content, language='apex', line_numbers=True)
                        st.download_button(label=f"Download {filename}", data=code_content, file_name=filename, mime='text/plain')
            else:
                st.info("No code has been generated yet.")

    # --- FINAL ACTIONS and DEBUG PANEL ---
    if st.session_state.technical_solution:
        st.divider()
        st.subheader("Final Actions")
        col3, col4 = st.columns(2)
        with col3:
            if st.button("🔄 Restart Process", use_container_width=True):
                st.session_state.update(user_story="", jira_ticket_id=None, url_processed=False, solution_overview="", technical_solution="", questions_to_ask=[], files_to_generate=[], generated_code_files={}, debug_info={})
                st.rerun()
        with col4:
            if st.button("Confirm to Jira", use_container_width=True, disabled=not st.session_state.get("jira_ticket_id"), help="This option is only available for stories fetched directly from Jira."):
                with st.spinner("Appending solutions to Jira ticket..."):
                    text_to_append = f"""\n\nh2. Generated by Rocket AI 🚀\n{{panel:title=Solution Direction|borderColor=#82B5F8}}\n{st.session_state.solution_overview}\n{{panel}}\n{{panel:title=Technical Solution|borderColor=#4285F4}}\n{{code:language=markdown}}\n{st.session_state.technical_solution}\n{{code}}\n{{panel}}"""
                    jira_service.update_story_description(st.session_state.jira_ticket_id, text_to_append)

    if st.session_state.debug_info:
        with st.expander("🔍 Show Debug Panel", expanded=False):
            st.json(st.session_state.debug_info)

with chat_tab:
    chat_view.render(ai_service)