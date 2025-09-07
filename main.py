# main.py (Updated Version)

# Step 1: Import the necessary libraries
import os ### NEW ###
from openai import OpenAI
from dotenv import load_dotenv ### NEW ###

# Step 2: Load environment variables from the .env file ### NEW ###
load_dotenv()

# Step 3: Initialize the AI client securely ### MODIFIED ###
# The script now reads the key from the environment, not from the code.
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Error: OPENAI_API_KEY not found.")
    print("Please make sure you have created a .env file with your API key.")
    exit()

try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    exit()

# Step 4: Define the User Story (This part is unchanged)
user_story = """
As a Sales Manager, I want the primary contact to be automatically set on an Account 
when the account's annual revenue exceeds $1,000,000, so our team knows who 
the key person is for our most valuable clients.
"""

print("✅ User Story Loaded.")
print("----------------------------------------")

# --- The rest of the script remains exactly the same ---

# Step 5: Define the prompt for the "Layman's Solution"
layman_prompt = f"""
You are a Salesforce Business Analyst...
User Story:
---
{user_story}
---
...
"""

# Step 6: Call the AI to get the Layman's Solution
print("⏳ Generating Layman's Solution...")
try:
    layman_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful Salesforce Business Analyst."},
            {"role": "user", "content": layman_prompt}
        ]
    )
    layman_solution = layman_response.choices[0].message.content
    print("✅ Layman's Solution Generated!")
    print(layman_solution)
    print("----------------------------------------")
except Exception as e:
    print(f"An error occurred while calling the OpenAI API: {e}")
    exit()

# Step 7: Define the prompt for the "Technical Solution"
technical_prompt = f"""
You are a Salesforce Technical Architect...
User Story:
---
{user_story}
---
Approved Functional Description:
---
{layman_solution}
---
...
"""

# Step 8: Call the AI to get the Technical Solution
print("⏳ Generating Technical Solution...")
try:
    technical_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful Salesforce Technical Architect."},
            {"role": "user", "content": technical_prompt}
        ]
    )
    technical_solution = technical_response.choices[0].message.content
    print("✅ Technical Solution Generated!")
    print(technical_solution)
    print("----------------------------------------")
except Exception as e:
    print(f"An error occurred while calling the OpenAI API: {e}")