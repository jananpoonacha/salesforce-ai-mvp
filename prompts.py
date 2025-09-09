# prompts.py

def get_triage_prompt(user_story):
    """
    Creates the initial prompt to analyze a user story and decide whether to 
    ask clarifying questions or provide a direct solution.
    """
    return f"""
    You are a Senior Salesforce Business Analyst AI. Your first task is to analyze the following user story for ambiguities.
    User Story:
    ---
    {user_story}
    ---
    Analyze the user story and respond ONLY with a JSON object. The JSON object must have a "status" field.
    - If the story is perfectly clear, set "status" to "clear" and include a "solution" field with the generated Solution Overview.
    - If the story is ambiguous, set "status" to "ambiguous" and provide a "clarification_questions" field, an array of objects.
    - For each question object, include a "question", an array of "options", and a "type" field set to either 'single' for single-choice questions or 'multiple' for multi-choice questions.
    """

def get_final_solution_prompt(user_story, context_from_answers):
    """
    Creates the prompt to generate a final Solution Overview after the user has
    provided answers to clarifying questions.
    """
    return f"""
    The user provided the following story:
    ---
    {user_story}
    ---
    The user provided the following clarifications to your questions:
    ---
    {context_from_answers}
    ---
    Based on the original story AND the new clarifications, please generate a final, comprehensive Solution Overview.
    """

def get_technical_solution_prompt(user_story, solution_overview):
    """
    Creates the prompt for the Technical Architect AI to generate a technical solution.
    """
    return f"""
    You are a Salesforce Technical Architect. Your primary goal is to leverage standard Salesforce features wherever possible.
    **Guiding Principle:** Before recommending custom code (like Apex or LWC), first consider if the requirement can be met using standard Salesforce declarative features such as Flows, Validation Rules, Page Layouts, or Formula Fields. If you must recommend custom code, you must briefly justify why standard features are insufficient.
    Create a detailed technical solution based on the following user story and functional description.
    User Story:
    ---
    {user_story}
    ---
    Approved Functional Description:
    ---
    {solution_overview}
    ---
    Generate a technical solution direction for a Salesforce developer.
    """

def get_code_generation_prompt(user_story, solution_overview, technical_solution):
    """
    NEW: Creates the prompt for the Code Generation AI.
    """
    return f"""
    You are an expert Salesforce Developer AI specializing in Apex and Lightning Web Components. Your task is to generate production-quality Salesforce code based on the provided context.

    **Context:**
    1.  **Original User Story:** ```{user_story}```
    2.  **Functional Solution Overview:** ```{solution_overview}```
    3.  **Approved Technical Solution:** ```{technical_solution}```

    **Instructions:**
    1.  Strictly adhere to the Approved Technical Solution.
    2.  Follow Salesforce best practices: bulkification, error handling, and security (CRUD/FLS checks).
    3.  Generate a corresponding Apex Test Class for any Apex code. The test class must have high code coverage (aim for 90%+) and include tests for positive, negative, and bulk scenarios.
    4.  The output MUST be a single, valid JSON object.
    5.  The JSON object must contain a single key, "files", which is an array of objects.
    6.  Each object in the "files" array must have two keys: "file_name" (e.g., "MyClass.cls") and "code_content" (the full source code as a string).

    **Example JSON Output Structure:**
    ```json
    {{
      "files": [
        {{
          "file_name": "AccountTriggerHandler.cls",
          "code_content": "public class AccountTriggerHandler {{\\n  // Apex code here...\\n}}"
        }},
        {{
          "file_name": "AccountTriggerHandler_Test.cls",
          "code_content": "@isTest\\nprivate class AccountTriggerHandler_Test {{\\n  // Test code here...\\n}}"
        }}
      ]
    }}
    ```
    
    Now, generate the code based on the provided context.
    """