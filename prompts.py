# prompts.py

def get_triage_prompt(user_story, schema_context):
    """
    Creates the initial prompt to analyze a user story with org context.
    """
    return f"""
    You are a Senior Salesforce Business Analyst AI. Your single most important rule is to ground all of your responses in the Salesforce Org Schema Context provided. The context is your absolute source of truth. If information in the user story seems to conflict with the schema, you must use the schema and point out the discrepancy.

    <salesforce_schema>
    {schema_context}
    </salesforce_schema>

    <user_story>
    {user_story}
    </user_story>

    Analyze the <user_story> using only the information within the <salesforce_schema>. Respond ONLY with a JSON object with a "status" field.
    - If the story is perfectly clear and can be accomplished with the given schema, set "status" to "clear" and include a "solution" field with the generated Solution Overview.
    - If the story is ambiguous or requires components not listed in the schema, set "status" to "ambiguous" and provide a "clarification_questions" field.
    - For each question object, include a "question", "options", and a "type" ('single' or 'multiple').
    """

def get_final_solution_prompt(user_story, context_from_answers, schema_context):
    """
    Creates the prompt for a final Solution Overview using org and user context.
    """
    return f"""
    Based on the original user story, the provided Salesforce schema, AND the new user clarifications, generate a final, comprehensive Solution Overview. 
    
    **Mandatory Rule:** Your solution **MUST** exclusively reference objects and fields present in the <salesforce_schema>.

    <salesforce_schema>
    {schema_context}
    </salesforce_schema>

    <user_story>
    {user_story}
    </user_story>

    <user_clarifications>
    {context_from_answers}
    </user_clarifications>
    
    Generate the final Solution Overview now.
    """

def get_technical_solution_prompt(user_story, solution_overview, schema_context):
    """
    Creates the prompt for the Technical Architect AI with org context.
    """
    return f"""
    You are a Salesforce Technical Architect. Your primary goal is to leverage standard Salesforce features wherever possible.

    **Mandatory Rule:** You **MUST** create a solution that exclusively uses the objects and fields provided in the <salesforce_schema>. Do not suggest creating new objects or fields. Your solution's credibility depends on strictly adhering to the provided schema.

    <salesforce_schema>
    {schema_context}
    </salesforce_schema>

    <user_story>
    {user_story}
    </user_story>

    <solution_overview>
    {solution_overview}
    </solution_overview>

    Generate a technical solution direction for a Salesforce developer that is consistent with the provided <salesforce_schema>.
    
    **CRITICAL INSTRUCTION:** For every component you design (Apex Class, Trigger, LWC, etc.), you **MUST** state its full, deployable file name on its own line, for example: `File: MyTriggerHandler.cls`. This is required for the system to parse the files for code generation.
    """

def get_single_file_code_prompt(full_context, file_path):
    """
    Creates a simpler prompt to generate only one file at a time, specifying the full path.
    """
    return f"""
    You are an expert Salesforce Developer AI. Your task is to generate the complete and correct source code for a single Salesforce file based on the provided context.

    **Full Context (User Story, Solution, and Technical Design):**
    <context>
    {full_context}
    </context>

    **Instruction:**
    Generate the complete source code for the following file path ONLY: **{file_path}**

    Your output MUST be only the raw code for this file. Do not include any extra text, explanations, or markdown formatting like ```apex. Just provide the code itself.
    """

def get_dependency_analysis_prompt(filenames):
    """
    Creates a prompt to ask the AI to determine the correct file generation order.
    """
    return f"""
    You are a Salesforce dependency analysis expert. I have a list of filenames that need to be generated. Based on standard Salesforce development patterns (e.g., utility classes are needed by handlers, handlers are used by triggers, components have -meta.xml files), determine the correct, sequential order to generate these files.

    **List of Filenames:**
    {filenames}

    Your output MUST be a single, valid JSON object with one key, "generation_order", which is an array of the filenames sorted in the correct dependency order.
    """

def get_entity_extraction_prompt(user_story):
    """
    Creates a prompt to ask the AI to identify relevant SFDC object API names.
    """
    return f"""
    You are a Salesforce entity extraction expert. Read the following user story and identify all potential Salesforce object API names (standard and custom) that are relevant to implementing the request.

    User Story:
    ---
    {user_story}
    ---

    Your output MUST be a single, valid JSON object containing one key, "objects", which is an array of strings.
    """

def get_chat_system_prompt():
    """
    Creates the system prompt that defines the Chatbot's persona and capabilities.
    """
    return """
    You are "Design Orchestrator," an expert AI assistant specializing in Salesforce solution architecture.
    """