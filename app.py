import streamlit as st
import openai
import pandas as pd
import json
import time
import random
import plotly.express as px

###############################################################################
# 1) PAGE CONFIGURATION & OPENAI SETUP
###############################################################################
st.set_page_config(layout="wide", page_title="Contact Center AI Assistant", initial_sidebar_state="collapsed", 
                 menu_items=None)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Add global CSS for better UI
st.markdown("""
<style>
/* Force dark theme */
html, body, [class*="css"] {
    color: white !important;
    background-color: #121212 !important;
}

/* Common styles for detail items */
.agent-detail, .inquiry-detail {
    margin-bottom: 12px;
    padding: 8px 12px;
    color: white;
    background-color: #2C2C2C;
    border-radius: 5px;
}

/* Common styles for labels */
.agent-label, .inquiry-label {
    font-weight: bold;
    margin-bottom: 4px;
    color: #e0e0e0;
}

/* Common styles for section headers */
.agent-section, .inquiry-section {
    margin-top: 20px;
    margin-bottom: 12px;
    font-size: 18px;
    font-weight: bold;
    padding-bottom: 5px;
    border-bottom: 1px solid #757575;
    color: #64B5F6;
}

/* Additional container styling */
.info-container {
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 8px;
    border: 1px solid #424242;
    background-color: #1E1E1E !important;
}

/* Topic tag styling */
.tag-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.topic-tag {
    display: inline-block;
    padding: 6px 12px;
    background-color: #2979FF;
    color: white !important;
    border-radius: 20px;
    font-size: 14px;
    margin: 5px;
    font-weight: 500;
}

/* Override Streamlit's default text color */
.element-container, .stMarkdown, .stText, .stSubheader {
    color: white !important;
}

/* Override header colors */
h1, h2, h3, h4, h5, h6 {
    color: white !important;
}

/* Override text colors */
p, div, span, li, label {
    color: white !important;
}

/* Add styles for charts and expanders */
.stExpander {
    border: 1px solid #424242 !important;
    background-color: #1E1E1E !important;
}

/* Dark theme for buttons */
.stButton>button {
    background-color: #333 !important;
    color: white !important;
    border: 1px solid #555 !important;
}

.stButton>button:hover {
    background-color: #444 !important;
    border: 1px solid #777 !important;
}

/* Set background color to dark */
.main .block-container, .appview-container {
    background-color: #121212 !important;
}

/* Override streamlit radio buttons and checkboxes */
.stRadio > div, .stCheckbox > div {
    color: white !important;
}

/* Make select boxes dark */
.stSelectbox > div > div {
    background-color: #333 !important;
    color: white !important;
}

/* Dark header */
header {
    background-color: #121212 !important;
}

/* Force dark theme for all elements */
div.stApp {
    background-color: #121212 !important;
}
</style>
""", unsafe_allow_html=True)

###############################################################################
# 2) LOAD FAQ / TAXONOMY DATA
###############################################################################
@st.cache_data
def load_faq_csv():
    """
    Loads the CSV file with FAQ/taxonomy data.
    Expected columns: Type, Category, Question.
    """
    try:
        df = pd.read_csv("faq_taxonomy.csv")
    except Exception as e:
        st.error("Error loading faq_taxonomy.csv. Please ensure the file exists and is in plain text CSV format.")
        df = pd.DataFrame(columns=["Type", "Category", "Question"])
    return df

df_faq = load_faq_csv()

###############################################################################
# 3) SET UP SESSION STATE
###############################################################################
@st.cache_data
def load_dummy_inquiries():
    """
    Loads dummy inquiry data from inquiries.json file if it exists.
    """
    try:
        with open("inquiries.json", "r") as f:
            inquiries_data = json.load(f)
        df = pd.DataFrame(inquiries_data)
        return df
    except Exception as e:
        # If file doesn't exist or has issues, return empty DataFrame
        return pd.DataFrame(columns=[
            "timestamp", "inbound_route", "ivr_flow", "ivr_selections", "user_type",
            "phone_email", "membership_id", "scenario_text", "classification",
            "priority", "summary", "account_name", "account_location",
            "account_reviews", "account_jobs", "project_cost", "payment_status"
        ])

if "inquiries" not in st.session_state:
    # Try to load dummy data first
    dummy_data = load_dummy_inquiries()
    if not dummy_data.empty:
        st.session_state["inquiries"] = dummy_data
    else:
        # If no dummy data, initialize with empty DataFrame
        st.session_state["inquiries"] = pd.DataFrame(columns=[
            "timestamp", "inbound_route", "ivr_flow", "ivr_selections", "user_type",
            "phone_email", "membership_id", "scenario_text", "classification",
            "priority", "summary", "account_name", "account_location",
            "account_reviews", "account_jobs", "project_cost", "payment_status"
        ])

if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

###############################################################################
# 4) BUILD FAQ CONTEXT STRING FROM CSV
###############################################################################
def build_faq_context(df):
    """
    Converts each row of the CSV into a bullet point.
    Expected columns: Type, Category, Question.
    """
    if df.empty:
        return "No FAQ/taxonomy data available."
    lines = []
    for _, row in df.iterrows():
        typ = str(row.get("Type", ""))
        cat = str(row.get("Category", ""))
        ques = str(row.get("Question", ""))
        lines.append(f"- Type: {typ} | Category: {cat} | Q: {ques}")
    return "\n".join(lines)

faq_context = build_faq_context(df_faq)

###############################################################################
# 5) SCENARIO GENERATION PROMPT
###############################################################################
# The prompt instructs the LLM to return only valid JSON, including account details.
scenario_generator_prompt_strict = f"""
You are a scenario generator for Checkatrade's inbound contact system. Your output must be a single, strictly formatted JSON object (with no extra commentary) that follows exactly the structure and rules below.

Below is the reference FAQ/taxonomy data:
{faq_context}

REFER TO THE FOLLOWING DEFINITIONS:

1. User Types & Allowed Actions

   A. Prospective Homeowner:
      - May only ask general questions about finding reliable tradespeople, how the vetting process works, or how to create an account.
      - Must not mention or reference any completed work, reviews, or complaints.
      - Forbidden phrases (any occurrence): 
           "my account", "my review", "poor quality", "not satisfied", "completed job", "past work", "review", "complaint".
      - The scenario_text must not reference any specific job, completed work, or tradesperson performance.
      - Account details must be entirely empty (name, surname, location, latest_reviews, latest_jobs, project_cost, payment_status all empty).

   B. Existing Homeowner:
      - May leave a review, complain about work quality, or refer to specific jobs completed for them.
      - Must only refer to work that has been done for them (e.g., "Had kitchen renovation completed by a plumber" or "Left a 4.5-star review for a roofer who fixed leaking gutters").
      - Forbidden phrases: "membership fees", "business profile", "offering trade services".
      - Account details must include a realistic name, surname, UK location, and non-empty latest_reviews and latest_jobs describing work done FOR them. Project cost and payment_status may be provided.

   C. Prospective Tradesperson:
      - May ask questions about joining Checkatrade, membership fees, application requirements, and the vetting process.
      - Must not reference any reviews, completed work for a homeowner, or any home service requests.
      - Forbidden phrases: any phrases that refer to home services (e.g., "find tradespeople", "reliable tradespeople", "completed job", "leaving a review", "in my home", "I hired").
      - The scenario_text must focus solely on joining the platform.
      - Account details must be entirely empty (name, surname, location, latest_reviews, latest_jobs, project_cost, payment_status all empty).

   D. Existing Tradesperson:
      - May update business details, ask about membership renewal, or respond to customer reviews.
      - Must only reference work they have completed for customers (e.g., "Completed bathroom renovation with custom tiling", "Received a 5-star review for rewiring a period property").
      - Forbidden phrases: any phrases implying they are a customer (e.g., "I hired", "done for me", "in my home", "my property", "complaint about work done").
      - Account details must include a realistic name, surname, UK location, and non-empty latest_reviews (that begin with "Received", "Customer gave", or "Client rated") and latest_jobs (that use active verbs such as "Completed", "Installed", "Repaired"). They must also include a valid membership_id in the format "T-xxxxx". Project cost and payment_status may be provided.

2. JSON Output Structure (ALL fields must be included exactly as below):

{{
    "inbound_route": "<one of: phone, whatsapp, email, web_form>",
    "ivr_flow": "<if inbound_route is phone, provide a realistic IVR flow description; otherwise, empty string>",
    "ivr_selections": "<if inbound_route is phone, provide an array of number selections; otherwise, an empty array>",
    "user_type": "<exactly one of: prospective_homeowner, existing_homeowner, prospective_tradesperson, existing_tradesperson>",
    "phone_email": "<a random phone number if inbound_route is phone or whatsapp; a random email if inbound_route is email; otherwise, empty>",
    "membership_id": "<for existing tradesperson only, e.g., 'T-12345'; for all others, empty string>",
    "account_details": {{
         "name": "<non-empty for existing users; empty for prospective users>",
         "surname": "<non-empty for existing users; empty for prospective users>",
         "location": "<a realistic UK location for existing users; empty for prospective users>",
         "latest_reviews": "<for existing homeowners: reviews they have given (must start with 'Gave', 'Left', or 'Posted'); for existing tradespeople: reviews they have received (must start with 'Received', 'Customer gave', or 'Client rated'); empty for prospective users>",
         "latest_jobs": "<for existing homeowners: job descriptions done for them (passive format, e.g., 'Had ... completed by ...'); for existing tradespeople: job descriptions they completed (active format, e.g., 'Completed ...'); empty for prospective users>",
         "project_cost": "<a realistic cost if a job is mentioned (e.g., '£2,500') for existing users; empty otherwise>",
         "payment_status": "<one of 'Paid', 'Pending', 'Partial Payment' if a job is mentioned for existing users; empty otherwise>"
    }},
    "scenario_text": "<a concise, realistic reason for contacting Checkatrade that strictly adheres to the allowed actions for the given user type>"
}}

3. IMPORTANT CROSSOVER CONSISTENCY RULES:

   - The scenario_text must be completely consistent with the user_type. For example:
         • If user_type is prospective_tradesperson, the text must ONLY ask about joining/membership and must not mention any work done in a home or reviews.
         • If user_type is prospective_homeowner, the text must only ask general questions about how Checkatrade vets tradespeople, and must not reference completed jobs or reviews.
         • If user_type is existing_homeowner, the text must reference work that was done for them (passively) and any review they left.
         • If user_type is existing_tradesperson, the text must reference work they have completed (actively) or a customer review they received.
   - The ivr_flow and any IVR selections must match the context implied by the user_type. For example, if the ivr_flow is "Homeowner Inquiry," the user_type must be either prospective_homeowner or existing_homeowner.
   - There must be no mention of a job, review, or complaint in the scenario_text if the user is prospective.
   - Only existing tradespeople may have a membership_id; all other user types must have an empty membership_id.
   - Account details must be empty for any prospective user (both homeowner and tradesperson).

4. FINAL OUTPUT REQUIREMENTS:

   - Your output MUST be valid JSON with exactly the keys and structure above.
   - Do not output any additional text, commentary, or formatting outside the JSON object.
   - All values must logically match the rules for the specified user_type. Any mention of reviews, completed work, or complaints must be exclusive to existing users, and any mention of joining, membership, or application details must be exclusive to prospective tradespeople.

Generate one inbound scenario that strictly adheres to all the rules above.
"""

###############################################################################
# 6) CLASSIFICATION PROMPT
###############################################################################
classification_prompt_template = """
You are an AI classification assistant for Checkatrade.

Given the scenario text below, please analyze the inquiry and return a JSON object with:
1. The most appropriate classification
2. The priority level
3. A brief summary
4. Whether this is related to a specific FAQ

Here's how to classify:
- Classification: Choose the most specific category (e.g., "Billing Dispute", "Job Quality Complaint", "Membership Query", "Technical Support", etc.)
- Priority: 
  * "High" for urgent issues affecting customers immediately (complaints, work issues, payment disputes)
  * "Medium" for important but not critical matters (account questions, general inquiries)
  * "Low" for informational requests or future-dated concerns
- Summary: A concise 1-2 sentence summary that captures the key issue
- FAQ Relation: If the inquiry directly relates to common questions about job issues, payment disputes, finding tradespeople, etc.

Return only valid JSON in this format:
{
  "classification": "...",
  "priority": "High|Medium|Low",
  "summary": "...",
  "related_faq_category": "..."  // E.g. "job_issue", "billing", "technical", "membership", or "" if none applies
}

Scenario text:
"{SCENARIO}"
"""

###############################################################################
# 7) HELPER: GENERATE SCENARIO VIA OPENAI
###############################################################################
def validate_scenario_rules(scenario_data):
    """
    Validates that the generated scenario follows all rules for its user type.
    Returns (is_valid, error_message) tuple.
    """
    user_type = scenario_data.get("user_type", "")
    scenario_text = scenario_data.get("scenario_text", "").lower()
    account_details = scenario_data.get("account_details", {})
    
    # Check for empty account details for prospective users
    if "prospective" in user_type:
        for key, value in account_details.items():
            if value and key not in ["name", "surname", "location"]:  # These can be empty strings
                return False, f"Prospective user has non-empty {key} in account details"
    
    # Check membership ID rules
    membership_id = scenario_data.get("membership_id", "")
    if "existing_tradesperson" in user_type and not membership_id.startswith("T-"):
        return False, "Existing tradesperson missing valid membership ID"
    elif "existing_tradesperson" not in user_type and membership_id:
        return False, "Non-tradesperson has membership ID"
    
    # Define forbidden phrases for each user type
    forbidden_phrases = {
        "prospective_homeowner": [
            "my account", "my review", "poor quality", "not satisfied", 
            "completed job", "past work", "my business", "insurance details",
            "trade license", "my customers"
        ],
        "existing_homeowner": [
            "my business", "insurance details", "trade license", "my customers",
            "membership fees", "business profiles", "trade services"
        ],
        "prospective_tradesperson": [
            "my review", "poor quality", "not satisfied", "in my home", 
            "I hired", "buy a home", "verify tradespeople", "find tradespeople",
            "reliable tradespeople", "home improvement", "renovation", "repair"
        ],
        "existing_tradesperson": [
            "I hired", "done for me", "my home", "my property", 
            "not satisfied with", "poor quality", "buy a home",
            "verify tradespeople", "find tradespeople", "reliable tradespeople"
        ]
    }
    
    # Check for forbidden phrases
    if user_type in forbidden_phrases:
        for phrase in forbidden_phrases[user_type]:
            if phrase in scenario_text:
                return False, f"Scenario contains forbidden phrase for {user_type}: '{phrase}'"
    
    # Check review format rules
    latest_reviews = account_details.get("latest_reviews", "")
    if latest_reviews:
        if "homeowner" in user_type:
            if not any(latest_reviews.lower().startswith(word) for word in ["gave", "left", "posted"]):
                return False, "Homeowner review must start with 'Gave', 'Left', or 'Posted'"
        elif "tradesperson" in user_type:
            if not any(latest_reviews.lower().startswith(word) for word in ["received", "customer gave", "client rated"]):
                return False, "Tradesperson review must start with 'Received', 'Customer gave', or 'Client rated'"
    
    # Check job description format with improved validation
    latest_jobs = account_details.get("latest_jobs", "")
    if latest_jobs:
        # Define active and passive verbs
        active_verbs = ["completed", "installed", "fixed", "repaired", "built", "constructed", "fitted", "mounted", "assembled"]
        passive_verbs = ["had", "got", "received", "was", "were", "been"]
        
        # For homeowners, check for active verbs (should be passive)
        if "homeowner" in user_type:
            active_verb_count = sum(1 for verb in active_verbs if verb in latest_jobs.lower())
            if active_verb_count > 0:
                return False, "Homeowner job description should be passive (e.g., 'Had kitchen renovated' not 'Completed kitchen renovation')"
            
            # Check if it starts with a passive verb
            if not any(latest_jobs.lower().startswith(verb) for verb in passive_verbs):
                return False, "Homeowner job description should start with a passive verb (e.g., 'Had', 'Got', 'Received')"
        
        # For tradespeople, check for passive verbs (should be active)
        elif "tradesperson" in user_type:
            passive_verb_count = sum(1 for verb in passive_verbs if verb in latest_jobs.lower())
            if passive_verb_count > 0:
                return False, "Tradesperson job description should be active (e.g., 'Completed kitchen renovation' not 'Had kitchen renovated')"
            
            # Check if it starts with an active verb
            if not any(latest_jobs.lower().startswith(verb) for verb in active_verbs):
                return False, "Tradesperson job description should start with an active verb (e.g., 'Completed', 'Installed', 'Fixed')"
    
    return True, ""

def generate_scenario(selected_route=None, selected_user_type=None):
    """
    Generates a scenario using OpenAI's ChatCompletion.
    If selected_route is provided (phone, whatsapp, email, web_form), force that route.
    If selected_user_type is provided, force that user type.
    """
    # For random user type, we'll randomize it ourselves to ensure true randomness
    should_randomize_user_type = selected_user_type is None
    
    # Add strict validation rules for scenario generation
    validation_rules = """
    STRICT JSON FORMAT REQUIREMENTS:
    
    You MUST return a single JSON object with EXACTLY this structure:
    {
        "inbound_route": "phone" | "whatsapp" | "email" | "web_form",
        "ivr_flow": "string if phone, empty string otherwise",
        "ivr_selections": [numbers if phone, empty array otherwise],
        "user_type": "existing_tradesperson" | "existing_homeowner" | "prospective_tradesperson" | "prospective_homeowner",
        "phone_email": "string based on route type",
        "membership_id": "T-xxxxx for existing tradesperson only, empty string otherwise",
        "account_details": {
            "name": "string for existing users, empty string for prospective",
            "surname": "string for existing users, empty string for prospective",
            "location": "string for existing users, empty string for prospective",
            "latest_reviews": "string for existing users, empty string for prospective",
            "latest_jobs": "string for existing users, empty string for prospective",
            "project_cost": "string for existing users with jobs, empty string otherwise",
            "payment_status": "string for existing users with jobs, empty string otherwise"
        },
        "scenario_text": "string describing the contact reason"
    }

    IMPORTANT JOB DESCRIPTION RULES:
    - For homeowners: Use passive voice (e.g., "Had kitchen renovated by a plumber")
    - For tradespeople: Use active voice (e.g., "Completed kitchen renovation with custom tiling")
    - Homeowner jobs must start with passive verbs like "Had", "Got", "Received"
    - Tradesperson jobs must start with active verbs like "Completed", "Installed", "Fixed"

    DO NOT include any additional fields or commentary.
    ALL fields must be present exactly as shown above.
    """
    
    # Start with base prompt
    user_content = scenario_generator_prompt_strict + validation_rules
    
    # Add route and user type instructions
    if selected_route and selected_user_type:
        user_content += f"\n\nForce inbound_route to '{selected_route}' and user_type to '{selected_user_type}'."
    elif selected_route:
        user_content += f"\n\nForce inbound_route to '{selected_route}'."
    elif selected_user_type:
        user_content += f"\n\nForce user_type to '{selected_user_type}'."
    else:
        user_content += "\n\nYou may pick any inbound_route and user_type."

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a JSON generator that creates strictly formatted scenario data for Checkatrade's contact system."},
                    {"role": "user", "content": user_content}
                ],
                temperature=1.0,
                max_tokens=500
            )
            raw_reply = response["choices"][0]["message"]["content"].strip()
            
            try:
                scenario_data = json.loads(raw_reply)
                
                # Validate required fields
                required_fields = ["inbound_route", "ivr_flow", "ivr_selections", "user_type", 
                                 "phone_email", "membership_id", "account_details", "scenario_text"]
                required_account_fields = ["name", "surname", "location", "latest_reviews", 
                                         "latest_jobs", "project_cost", "payment_status"]
                
                # Check all required fields exist
                for field in required_fields:
                    if field not in scenario_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Check account_details structure
                if not isinstance(scenario_data["account_details"], dict):
                    raise ValueError("account_details must be an object")
                
                for field in required_account_fields:
                    if field not in scenario_data["account_details"]:
                        raise ValueError(f"Missing required account field: {field}")
                
                # If we're supposed to randomize the user type, do it manually
                if should_randomize_user_type:
                    user_types = ["existing_homeowner", "existing_tradesperson", 
                                "prospective_homeowner", "prospective_tradesperson"]
                    random_user_type = random.choice(user_types)
                    scenario_data["user_type"] = random_user_type
                    
                    # Update account details based on user type
                    if "prospective" in random_user_type:
                        scenario_data["account_details"] = {
                            "name": "",
                            "surname": "",
                            "location": "",
                            "latest_reviews": "",
                            "latest_jobs": "",
                            "project_cost": "",
                            "payment_status": ""
                        }
                        scenario_data["membership_id"] = ""
                
                # Validate the scenario against all rules
                is_valid, error_message = validate_scenario_rules(scenario_data)
                if not is_valid:
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        continue
                    else:
                        # If we've hit max retries, return an error scenario with more specific error message
                        return {
                            "inbound_route": "error",
                            "ivr_flow": "",
                            "ivr_selections": [],
                            "user_type": selected_user_type if selected_user_type else "error",
                            "phone_email": "",
                            "membership_id": "",
                            "account_details": {
                                "name": "",
                                "surname": "",
                                "location": "",
                                "latest_reviews": "",
                                "latest_jobs": "",
                                "project_cost": "",
                                "payment_status": ""
                            },
                            "scenario_text": f"Failed to generate valid scenario after {max_retries} attempts. Last error: {error_message}"
                        }
                
                return scenario_data
                
            except Exception as e:
                if retry_count < max_retries - 1:
                    retry_count += 1
                    continue
                else:
                    # Return a properly structured error scenario
                    return {
                        "inbound_route": "error",
                        "ivr_flow": "",
                        "ivr_selections": [],
                        "user_type": selected_user_type if selected_user_type else "error",
                        "phone_email": "",
                        "membership_id": "",
                        "account_details": {
                            "name": "",
                            "surname": "",
                            "location": "",
                            "latest_reviews": "",
                            "latest_jobs": "",
                            "project_cost": "",
                            "payment_status": ""
                        },
                        "scenario_text": f"Error parsing scenario JSON: {str(e)}"
                    }
            
        except Exception as e:
            if retry_count < max_retries - 1:
                retry_count += 1
                continue
            else:
                # Return a properly structured error scenario for API errors
                return {
                    "inbound_route": "error",
                    "ivr_flow": "",
                    "ivr_selections": [],
                    "user_type": selected_user_type if selected_user_type else "error",
                    "phone_email": "",
                    "membership_id": "",
                    "account_details": {
                        "name": "",
                        "surname": "",
                        "location": "",
                        "latest_reviews": "",
                        "latest_jobs": "",
                        "project_cost": "",
                        "payment_status": ""
                    },
                    "scenario_text": f"API Error: {str(e)}"
                }
    
    # If we've exhausted all retries, return an error scenario
    return {
        "inbound_route": "error",
        "ivr_flow": "",
        "ivr_selections": [],
        "user_type": selected_user_type if selected_user_type else "error",
        "phone_email": "",
        "membership_id": "",
        "account_details": {
            "name": "",
            "surname": "",
            "location": "",
            "latest_reviews": "",
            "latest_jobs": "",
            "project_cost": "",
            "payment_status": ""
        },
        "scenario_text": f"Failed to generate valid scenario after {max_retries} attempts."
    }

###############################################################################
# 8) HELPER: CLASSIFY SCENARIO VIA OPENAI
###############################################################################
def classify_scenario(text):
    prompt = classification_prompt_template.replace("{SCENARIO}", text)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Updated to use gpt-4o-mini
        messages=[
            {"role": "system", "content": "You classify inbound queries for Checkatrade."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=300
    )
    raw_reply = response["choices"][0]["message"]["content"].strip()
    try:
        classification_data = json.loads(raw_reply)
        return classification_data
    except Exception as e:
        return {
            "classification": "General",
            "priority": "Medium",
            "summary": "Could not parse classification JSON.",
            "related_faq_category": ""
        }

###############################################################################
# RESPONSE SUGGESTION HELPER FUNCTIONS
###############################################################################
def self_process_ivr_selections(ivr_selections):
    """
    Safely process ivr_selections to handle any type that might be received.
    Returns a string representation suitable for storing in the DataFrame.
    """
    if isinstance(ivr_selections, list):
        return ", ".join(map(str, ivr_selections))
    elif ivr_selections:
        return str(ivr_selections)
    else:
        return ""

def find_relevant_faq(scenario_text, faq_dataframe):
    """
    Find the most relevant FAQ based on the scenario text.
    Returns a tuple (question, relevance_score) if found, or (None, 0) if no good match
    """
    if faq_dataframe.empty:
        return None, 0
    
    # In a real implementation, this would use embedding similarity
    # For demo purposes, we'll use improved keyword matching
    scenario_lower = scenario_text.lower()
    
    # First, look for direct issue mentions in the scenario text
    issue_keywords = {
        "job not completed": ["not completed", "unfinished", "incomplete", "left halfway", "abandoned", "not finished"],
        "quality issues": ["poor quality", "bad workmanship", "not satisfied", "poor standard", "substandard", "quality issue", "poor work", "faulty"],
        "delayed work": ["delayed", "late", "behind schedule", "taking too long", "missed deadline", "overdue"],
        "billing dispute": ["overcharged", "invoice", "billing", "payment dispute", "charge", "refund", "overpriced", "cost dispute"],
        "tradesperson communication": ["not responding", "ghosted", "won't return calls", "can't reach", "no communication", "stopped responding", "no reply"],
        "complaint": ["unhappy", "disappointed", "complaint", "not happy", "issue", "problem", "dissatisfied"],
        "account access": ["can't login", "password", "reset", "access", "account", "sign in", "login failed"],
        "app technical": ["app", "website", "technical", "error", "not working", "glitch", "broken"],
        "find tradesperson": ["looking for", "need to find", "searching for", "recommend", "suggestion", "need a", "looking to hire"],
        "membership": ["membership", "subscribe", "join", "renewal", "cancel subscription", "subscription fee"],
        "warranty issues": ["warranty", "guarantee", "promised warranty", "no warranty", "warranty claim", "coverage", "warranty period"],
        "tradesperson qualifications": ["qualifications", "certified", "licensed", "accredited", "training", "skills", "experience"],
        "repair issues": ["repair failed", "still broken", "not fixed", "same issue", "recurring problem", "issue persists"]
    }
    
    # Special case for warranty issues which are particularly sensitive
    if "warranty" in scenario_lower or "guarantee" in scenario_lower:
        # Look for FAQs specifically about warranties
        warranty_matches = []
        for _, row in faq_dataframe.iterrows():
            question = str(row.get("Question", "")).lower()
            if "warranty" in question or "guarantee" in question:
                # Count how many words overlap between scenario and question
                scenario_words = set(scenario_lower.split())
                question_words = set(question.split())
                overlap_count = len(scenario_words.intersection(question_words))
                warranty_matches.append((row["Question"], overlap_count + 5))  # Bonus for warranty match
        
        if warranty_matches:
            # Return the one with highest score
            warranty_matches.sort(key=lambda x: x[1], reverse=True)
            if warranty_matches[0][1] >= 6:  # Higher threshold for relevance
                return warranty_matches[0]
    
    # Try direct issue matching first - this has the highest relevance score
    for issue, keywords in issue_keywords.items():
        # Count how many keywords from this issue are in the scenario
        matches = sum(1 for keyword in keywords if keyword in scenario_lower)
        if matches >= 2:  # If we have at least 2 matching keywords for an issue type
            # Find FAQs related to this issue
            for _, row in faq_dataframe.iterrows():
                question = str(row.get("Question", "")).lower()
                # If the issue matches keywords in the question, return it with high relevance
                keyword_matches = sum(1 for keyword in keywords if keyword in question)
                if keyword_matches >= 2:
                    return row["Question"], 8  # High relevance for direct issue match
    
    # If no direct issue match, try matching by category with improved categories
    category_keywords = {
        "complaint": ["complaint", "dissatisfied", "poor service", "issue", "problem", "unhappy", "disappointed"],
        "tradesperson": ["tradesperson", "trade", "contractor", "professional", "worker", "electrician", "plumber", "roofer", "builder"],
        "job quality": ["job", "work", "quality", "standard", "workmanship", "completed", "finished", "done", "performed"],
        "warranty": ["warranty", "guarantee", "coverage", "protection", "promised", "assured", "certified"],
        "billing": ["bill", "payment", "invoice", "charge", "cost", "price", "fee", "refund"],
        "account": ["account", "login", "password", "credentials", "sign in", "profile", "dashboard"],
        "membership": ["membership", "subscription", "renewal", "join", "register", "member"],
        "reviews": ["review", "rating", "feedback", "star", "comment", "testimonial", "reputation"],
        "technical": ["technical", "app", "website", "online", "digital", "error", "malfunction"]
    }
    
    # Find matching category with improved scoring
    matching_categories = []
    for category, terms in category_keywords.items():
        # Use weighted matching - exact matches worth more than partial matches
        exact_matches = sum(1 for term in terms if f" {term} " in f" {scenario_lower} ")
        contains_matches = sum(1 for term in terms if term in scenario_lower) - exact_matches
        total_score = (exact_matches * 2) + contains_matches
        
        if total_score > 0:
            # Give extra weight to certain important categories
            if category in ["warranty", "job quality", "complaint"] and total_score > 1:
                total_score += 2
            
            matching_categories.append((category, total_score))
    
    # Sort categories by number of matches
    matching_categories.sort(key=lambda x: x[1], reverse=True)
    
    # If we have matching categories, find FAQs in those categories
    if matching_categories:
        for category, category_match_count in matching_categories:
            matched_rows = faq_dataframe[faq_dataframe["Category"].str.lower().str.contains(category.lower())]
            if not matched_rows.empty:
                # Find the FAQ that best matches specific words in the scenario
                best_match = None
                best_match_score = 0
                
                for _, row in matched_rows.iterrows():
                    question = str(row.get("Question", "")).lower()
                    
                    # Enhanced scoring system:
                    # 1. More weight for matching significant words
                    # 2. Bonus for multiple word matches
                    # 3. Penalty for questions with irrelevant topics
                    
                    # Get significant words (longer words carry more meaning)
                    scenario_words = [word for word in scenario_lower.split() if len(word) > 4]
                    
                    # Count matches
                    word_matches = sum(1 for word in scenario_words if word in question)
                    
                    # Bonus for consecutive words matching (phrases)
                    phrase_bonus = 0
                    for i in range(len(scenario_words) - 1):
                        phrase = f"{scenario_words[i]} {scenario_words[i+1]}"
                        if phrase in question:
                            phrase_bonus += 2
                    
                    # Check for irrelevant topics that would make the FAQ inappropriate
                    irrelevant_terms = ["drone", "survey", "partnership", "newsletter", "marketing"]
                    irrelevance_penalty = sum(3 for term in irrelevant_terms if term in question)
                    
                    # Final score
                    score = word_matches + phrase_bonus + (category_match_count/2) - irrelevance_penalty
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = row["Question"]
                
                if best_match and best_match_score >= 3:  # Higher threshold for relevance
                    # Relevance is based on both category match and word match
                    relevance = best_match_score
                    return best_match, relevance
    
    # Last resort: look for any significant word matches with improved scoring
    best_match = None
    best_score = 0
    
    # Important topic words that should be given more weight
    important_topics = ["warranty", "guarantee", "electrician", "complaint", "quality", "problem", "issue"]
    
    for _, row in faq_dataframe.iterrows():
        question = str(row.get("Question", "")).lower()
        
        # Check if any significant words from the scenario appear in the question
        scenario_words = [word for word in scenario_lower.split() if len(word) > 4]
        
        # Basic matching score
        matches = sum(1 for word in scenario_words if word in question)
        
        # Bonus for important topics
        topic_bonus = sum(2 for word in important_topics if word in scenario_lower and word in question)
        
        # Penalty for likely irrelevant topics
        irrelevant_terms = ["drone", "survey", "partnership", "newsletter", "marketing"]
        irrelevance_penalty = sum(3 for term in irrelevant_terms if term in question)
        
        # Final score
        total_score = matches + topic_bonus - irrelevance_penalty
        
        if total_score > best_score:
            best_score = total_score
            best_match = row["Question"]
    
    if best_match and best_score >= 3:  # Higher threshold for relevance
        return best_match, best_score
    
    return None, 0

def generate_response_suggestion(scenario, classification_result):
    """
    Generate a suggested response based on scenario type (email/whatsapp)
    """
    inbound_route = scenario.get("inbound_route", "")
    scenario_text = scenario.get("scenario_text", "")
    user_type = scenario.get("user_type", "")
    classification = classification_result.get("classification", "")
    
    # Get account details if available
    account_details = scenario.get("account_details", {})
    name = f"{account_details.get('name', '')} {account_details.get('surname', '')}".strip()
    first_name = name.split()[0] if name else ""
    latest_jobs = account_details.get("latest_jobs", "")
    latest_reviews = account_details.get("latest_reviews", "")
    project_cost = account_details.get("project_cost", "")
    
    # Generate appropriate greeting based on route type and available information
    greeting = ""
    if inbound_route in ["email", "whatsapp"]:
        if first_name:
            greeting = f"Hi {first_name},"
    else:
            greeting = "Hi there,"
    
    # Generate response body based on classification and scenario context
    body = ""
    
    # Reference job details if relevant to the issue
    job_reference = ""
    if "complaint" in classification.lower() or "job" in scenario_text.lower() or "issue" in scenario_text.lower():
        # Extract job type from latest_jobs if available
        job_type = ""
        if latest_jobs:
            # Try to extract job type (e.g., "roof repair", "kitchen renovation")
            job_words = ["renovation", "repair", "installation", "fitting", "refurbishment", "plumbing", "electrical", "roofing", "bathroom", "kitchen"]
            for word in job_words:
                if word in latest_jobs.lower():
                    job_type = word
                    break
            
            # If we have a job type, reference it specifically
            if job_type:
                job_reference = f"I can see this relates to your recent {job_type} work. "
            else:
                job_reference = f"I can see from your account that you've recently had work completed. "
                
            job_reference += "Could you confirm which specific aspects of the job you're experiencing issues with? "
    
    # Extract specific details from scenario for context
    specific_details = extract_specific_details(scenario_text)
    
    # Main response body based on classification
    if "complaint" in classification.lower():
        body = f"Thank you for contacting Checkatrade about your concerns. {job_reference}We're sorry to hear you're experiencing problems and want to help resolve this for you as quickly as possible."
        
        # Add follow-up questions specific to complaints
        body += "\n\nTo help us address your concerns effectively, could you please provide:"
        body += "\n- Details of what specifically hasn't met your expectations"
        body += "\n- Any communication you've had with the tradesperson about these issues"
        if project_cost:
            body += f"\n- Whether you've made any payments toward the {project_cost} project cost"
        
    elif "billing" in classification.lower():
        body = f"Thank you for contacting Checkatrade about your billing query. {specific_details}We'll look into this for you right away."
        
        # Add follow-up questions for billing
        if project_cost:
            body += f"\n\nI can see the project cost is {project_cost}. Could you please confirm which aspect of the payment you'd like assistance with?"
        else:
            body += "\n\nTo help resolve this quickly, could you provide details of the specific payment or charge you're inquiring about?"
            
    elif "membership" in classification.lower() or "insurance" in scenario_text.lower() or "account" in scenario_text.lower():
        if "insurance" in scenario_text.lower() or "public liability" in scenario_text.lower():
            body = f"Thank you for contacting Checkatrade about updating your Public Liability Insurance details. I'd be happy to help you with this important account update."
            body += "\n\nTo update your insurance information, I'll need the following details:"
            body += "\n- Your new insurance provider name"
            body += "\n- Policy number"
            body += "\n- Coverage amount"
            body += "\n- Effective dates of the policy"
            body += "\n\nOnce you provide these details, I can update your account immediately. Alternatively, you can update this information directly through your account dashboard by going to the 'Insurance Details' section."
        elif "existing" in user_type:
            body = f"Thank you for your query about your Checkatrade membership. {specific_details}"
            body += "\n\nI'll take a look at your account and make sure everything is updated correctly. If you have any specific details or documents you need to upload, please let me know and I can guide you through the process."
        else:
            body = f"Thank you for your interest in becoming a Checkatrade member. {specific_details}"
            body += "\n\nTo proceed with your membership application, we'll need to gather some information about your business and services. Would you like me to outline the steps involved, or do you have specific questions about the membership process?"
            
    elif "technical" in classification.lower():
        body = f"I understand you're experiencing technical difficulties with {specific_details}. Let me help resolve this for you."
        body += "\n\nCould you please share what specific error messages you're seeing or what functionality isn't working as expected? Screenshots can be helpful if available."
        body += "\n\nIn the meantime, you might try clearing your browser cache or using our mobile app as an alternative."
        
    else:
        if job_reference:
            body = f"Thank you for contacting Checkatrade. {job_reference}We're happy to help with your inquiry."
        else:
            body = f"Thank you for contacting Checkatrade. {specific_details}We're happy to help with your inquiry."
    
    # Add review reference if relevant
    if "review" in scenario_text.lower() and latest_reviews:
        body += f"\n\nI can see you've recently provided feedback on our service. Your reviews are important to us and help maintain our high standards."
    
    # Add FAQ link section with more prominent and friendly message
    faq_link = ""
    
    if "membership" in classification.lower():
        faq_link = "\n\n📚 **For your convenience:** Many of our members find our Membership FAQ helpful for quick answers. Please check our comprehensive guide at [Checkatrade.com/MembershipFAQ] which covers common questions about account management, benefits, and renewal processes."
    elif "insurance" in scenario_text.lower():
        faq_link = "\n\n📚 **For your convenience:** We've put together detailed information about insurance requirements and coverage at [Checkatrade.com/InsuranceInfo]. This resource explains all our insurance policies and answers common questions you might have."
    elif "billing" in classification.lower():
        faq_link = "\n\n📚 **For your convenience:** Our billing FAQ section at [Checkatrade.com/BillingFAQ] provides detailed guidance on payment processes, invoice questions, and subscription details that may help answer your questions immediately."
    elif "complaint" in classification.lower() or "job" in classification.lower():
        faq_link = "\n\n📚 **For your convenience:** We have a dedicated help section about resolving job quality issues at [Checkatrade.com/JobResolutionHelp] which offers step-by-step guidance on our resolution process."
    elif "technical" in classification.lower():
        faq_link = "\n\n📚 **For your convenience:** Our technical support hub at [Checkatrade.com/TechSupport] contains troubleshooting guides, video tutorials, and solutions to common technical issues you may encounter."
    else:
        faq_link = "\n\n📚 **For your convenience:** You may find immediate answers to your questions in our FAQ section at [Checkatrade.com/FAQ]. Our help center is available 24/7 with searchable solutions to common questions."
    
    # Add the FAQ link to the body
    body += faq_link
    
    # Different closing based on channel
    closing = ""
    if inbound_route == "email":
        closing = "\n\nWe're committed to ensuring your issue is resolved satisfactorily. I'll personally look into this and get back to you within 24 hours.\n\nBest regards,\nThe Checkatrade Team"
    elif inbound_route == "whatsapp":
        closing = "\n\nWe're here to help resolve this for you. Is there anything else you can tell me about the situation that would help us address your concerns more effectively?"
    
    return f"{greeting}\n\n{body}{closing}"

def extract_specific_details(scenario_text):
    """
    Extract specific details from the scenario text to include in the response
    """
    # This is a simple version - in a real system this could use NER or other techniques
    specific_details = ""
    
    if "insurance" in scenario_text.lower() or "public liability" in scenario_text.lower():
        specific_details = "I understand you need assistance with updating your Public Liability Insurance details. "
    elif "password" in scenario_text.lower() or "login" in scenario_text.lower():
        specific_details = "I understand you're having trouble accessing your account. "
    elif "payment" in scenario_text.lower() or "bill" in scenario_text.lower():
        specific_details = "I understand you have a query about your payment or billing. "
    elif "membership" in scenario_text.lower():
        specific_details = "I understand you have a question about your membership. "
    elif "tradesperson" in scenario_text.lower() or "contractor" in scenario_text.lower():
        specific_details = "I understand you have a concern regarding a tradesperson. "
    
    return specific_details

###############################################################################
# 9) STREAMLIT APP UI
###############################################################################
st.title("Contact Center AI Assistant")

# -----------------------------------------------------------------------------
# SCENARIO GENERATION
# -----------------------------------------------------------------------------
st.header("Generate New Inquiry")

# Create columns for the route selection mode
col1, col2, col3, col4, col5 = st.columns([1, 0.75, 0.75, 0.75, 0.75])

with col1:
    st.markdown("<div class='inquiry-label'>Route Selection:</div>", unsafe_allow_html=True)
    route_selection = st.radio(
        label="Route",
        options=["Random", "Phone", "Email", "WhatsApp", "Web Form"],
        label_visibility="collapsed",
        horizontal=True,
        key="route_selection"
    )

# Map route selection to variables
route_random = route_selection == "Random"
route_phone = route_selection == "Phone"
route_email = route_selection == "Email"
route_whatsapp = route_selection == "WhatsApp"
route_webform = route_selection == "Web Form"

# User Type Selection
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 0.75, 0.75, 0.75])

with col1:
    st.markdown("<div class='inquiry-label'>Customer Type:</div>", unsafe_allow_html=True)
    user_selection = st.radio(
        label="User Type",
        options=["Random", "Existing Homeowner", "Existing Tradesperson", "Unknown/New Contact"],
        label_visibility="collapsed",
        horizontal=True,
        key="user_selection"
    )

# Map user type selection to variables
user_random = user_selection == "Random"
user_homeowner = user_selection == "Existing Homeowner"
user_tradesperson = user_selection == "Existing Tradesperson"
user_unknown = user_selection == "Unknown/New Contact"

# Map the selection to the correct user_type value
selected_user_type = None
if not user_random:
    if user_homeowner:
        selected_user_type = "existing_homeowner"
    elif user_tradesperson:
        selected_user_type = "existing_tradesperson"
    elif user_unknown:
        # For unknown/new, randomly choose between prospective homeowner or tradesperson
        selected_user_type = random.choice(["prospective_homeowner", "prospective_tradesperson"])

# Determine selected route
selected_route = None
if not route_random:
    if route_phone:
        selected_route = "phone"
    elif route_email:
        selected_route = "email"
    elif route_whatsapp:
        selected_route = "whatsapp"
    elif route_webform:
        selected_route = "web_form"

# Generate button in a new row
if st.button("Generate New Inquiry", use_container_width=True):
    with st.spinner("Generating scenario..."):
        scenario_data = generate_scenario(selected_route, selected_user_type)
        st.session_state["generated_scenario"] = scenario_data
        st.success("Scenario generated!")

# Create a visual separation before the scenario display
st.markdown("<hr style='margin: 30px 0px; border-color: #424242;'/>", unsafe_allow_html=True)

# Move scenario display outside the columns to be full width below the Generate Scenario button
if st.session_state["generated_scenario"]:
    scenario = st.session_state["generated_scenario"]
    
    # Create columns for the titles
    title_col1, title_col2 = st.columns(2)
    with title_col1:
        st.subheader("Scenario Details")
    with title_col2:
        st.subheader("Account Details")
    
    # Create columns for the content
    left_col, right_col = st.columns(2)
    
    # Left column for general scenario details
    with left_col:
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        
        # Basic scenario information
        if scenario.get('inbound_route'):
            st.markdown("<div class='agent-label'>Inbound Route:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('inbound_route', 'N/A')}</div>", unsafe_allow_html=True)
        
        if scenario.get('ivr_flow'):
            st.markdown("<div class='agent-label'>IVR Flow:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('ivr_flow', 'N/A')}</div>", unsafe_allow_html=True)
        
        # Add type checking for ivr_selections
        ivr_selections_list = scenario.get("ivr_selections", [])
        if isinstance(ivr_selections_list, list):
            ivr_selections = ', '.join(map(str, ivr_selections_list))
        else:
            ivr_selections = str(ivr_selections_list) if ivr_selections_list else ""
            
        if ivr_selections:
            st.markdown("<div class='agent-label'>IVR Selections:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{ivr_selections}</div>", unsafe_allow_html=True)
        
        if scenario.get('user_type'):
            st.markdown("<div class='agent-label'>User Type:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('user_type', 'N/A')}</div>", unsafe_allow_html=True)
            
        if scenario.get('phone_email'):
            st.markdown("<div class='agent-label'>Phone/Email:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('phone_email', 'N/A')}</div>", unsafe_allow_html=True)
        
        if scenario.get('membership_id'):
            st.markdown("<div class='agent-label'>Membership ID:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('membership_id', 'N/A')}</div>", unsafe_allow_html=True)
            
        # Reason for contact
        if scenario.get('scenario_text'):
            st.markdown("<div class='agent-section'>Reason for Contact</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('scenario_text')}</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
    
    # Right column for account details
    with right_col:
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        
        account_details = scenario.get("account_details", {})
        name = f"{account_details.get('name', '')} {account_details.get('surname', '')}".strip()
        
        if name:
            st.markdown("<div class='agent-label'>Name:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{name}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='agent-label'>Name:</div>", unsafe_allow_html=True)
            st.markdown("<div class='agent-detail'>No account information available</div>", unsafe_allow_html=True)
        
        if account_details.get('location'):
            st.markdown("<div class='agent-label'>Location:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('location')}</div>", unsafe_allow_html=True)
        
        if account_details.get('latest_reviews'):
            st.markdown("<div class='agent-label'>Latest Reviews:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('latest_reviews')}</div>", unsafe_allow_html=True)
        
        if account_details.get('latest_jobs'):
            st.markdown("<div class='agent-label'>Latest Jobs:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('latest_jobs')}</div>", unsafe_allow_html=True)
        
        # Show project cost and payment status side by side if available
        if account_details.get('project_cost') or account_details.get('payment_status'):
            project_cost = account_details.get('project_cost', 'N/A')
            payment_status = account_details.get('payment_status', 'N/A')
            
            st.markdown("<div class='agent-label'>Project Details:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>Project Cost: {project_cost} &nbsp;&nbsp;&nbsp; Status: {payment_status}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div

# -----------------------------------------------------------------------------
# CLASSIFY & STORE INQUIRY
# -----------------------------------------------------------------------------
st.header("Inquiry Classification")
if st.session_state["generated_scenario"]:
    scenario_text = st.session_state["generated_scenario"].get("scenario_text", "")
    account_details = st.session_state["generated_scenario"].get("account_details", {})
    if st.button("Classify Scenario", use_container_width=True):
        if scenario_text.strip():
            with st.spinner("Classifying scenario..."):
                classification_result = classify_scenario(scenario_text)
                now = time.strftime("%Y-%m-%d %H:%M:%S")

                new_row = {
                    "timestamp": now,
                    "inbound_route": st.session_state["generated_scenario"].get("inbound_route", ""),
                    "ivr_flow": st.session_state["generated_scenario"].get("ivr_flow", ""),
                    "ivr_selections": self_process_ivr_selections(st.session_state["generated_scenario"].get("ivr_selections", [])),
                    "user_type": st.session_state["generated_scenario"].get("user_type", ""),
                    "phone_email": st.session_state["generated_scenario"].get("phone_email", ""),
                    "membership_id": st.session_state["generated_scenario"].get("membership_id", ""),
                    "scenario_text": scenario_text,
                    "classification": classification_result.get("classification", "General"),
                    "priority": classification_result.get("priority", "Medium"),
                    "summary": classification_result.get("summary", ""),
                    "account_name": account_details.get("name", ""),
                    "account_location": account_details.get("location", ""),
                    "account_reviews": account_details.get("latest_reviews", ""),
                    "account_jobs": account_details.get("latest_jobs", ""),
                    "project_cost": account_details.get("project_cost", ""),
                    "payment_status": account_details.get("payment_status", "")
                }

                st.session_state["inquiries"] = pd.concat(
                    [st.session_state["inquiries"], pd.DataFrame([new_row])],
                    ignore_index=True
                )
                st.success(f"Scenario classified as {new_row['classification']} (Priority: {new_row['priority']}).")
                
                # Get relevant FAQ based on the classification result and scenario text
                faq_category = classification_result.get("related_faq_category", "")
                relevant_faq = None
                faq_relevance_score = 0  # Track how relevant the match is

                # First try to use the model's suggested FAQ category
                if faq_category and faq_category.lower() not in ["", "none", "n/a"]:
                    # Filter FAQ dataframe by the suggested category
                    category_matches = df_faq[df_faq["Category"].str.lower().str.contains(faq_category.lower())]
                    if not category_matches.empty:
                        # Look for the best match within this category
                        best_match = None
                        best_score = 0
                        
                        for _, row in category_matches.iterrows():
                            question = str(row.get("Question", "")).lower()
                            scenario_lower = scenario_text.lower()
                            # Count significant word matches
                            score = sum(1 for word in scenario_lower.split() if len(word) > 4 and word in question)
                            if score > best_score:
                                best_score = score
                                best_match = row["Question"]
                        
                        if best_match and best_score >= 2:  # Require at least 2 significant matches
                            relevant_faq = best_match
                            faq_relevance_score = best_score + 2  # Bonus for model-suggested category

                # If no FAQ found via category or low relevance, use our keyword matching function
                if not relevant_faq or faq_relevance_score < 3:
                    keyword_faq, keyword_score = find_relevant_faq(scenario_text, df_faq)
                    if keyword_faq and keyword_score >= 3:  # Higher threshold for keyword matching
                        # If we already have a FAQ but this one is more relevant, replace it
                        if keyword_score > faq_relevance_score:
                            relevant_faq = keyword_faq
                            faq_relevance_score = keyword_score

                # Only display FAQ if we have a sufficiently relevant match
                if relevant_faq and faq_relevance_score >= 3:
                    st.info(f"**Suggested FAQ:** {relevant_faq}")
                
                # Generate response suggestion for email or whatsapp
                inbound_route = st.session_state["generated_scenario"].get("inbound_route", "")
                if inbound_route in ["email", "whatsapp"]:
                    response_suggestion = generate_response_suggestion(
                        st.session_state["generated_scenario"], 
                        classification_result
                    )
                    st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='agent-section'>Suggested {inbound_route.capitalize()} Response</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='agent-detail' style='white-space: pre-wrap;'>{response_suggestion}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No scenario text found. Generate a scenario first.")
else:
    st.info("Generate a scenario above before classification.")

# -----------------------------------------------------------------------------
# DASHBOARD & LOGGED INQUIRIES (Enhanced View)
# -----------------------------------------------------------------------------
st.header("Dashboard")
df = st.session_state["inquiries"]
if len(df) > 0:
    # Sort inquiries by timestamp in descending order (most recent first)
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
    except:
        # If timestamp conversion fails, just use the existing order
        pass
    
    # Display the most recent inquiry card first with full details
    st.subheader("Most Recent Inquiry")
    
    # Get the most recent inquiry
    recent_row = df.iloc[0]
    
    # Create a collapsible container for the most recent inquiry instead of showing it expanded by default
    with st.expander("View Most Recent Inquiry", expanded=False):
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        
        # Display header with classification and priority
        st.markdown(f"<div style='font-size: 18px; font-weight: bold; margin-bottom: 10px;'>{recent_row['classification']} (Priority: {recent_row['priority']})</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{recent_row['timestamp']}</div>", unsafe_allow_html=True)
            
            if recent_row['inbound_route']:
                st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['inbound_route']}</div>", unsafe_allow_html=True)
            
            if recent_row['ivr_flow']:
                st.markdown("<div class='inquiry-label'>IVR Flow:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['ivr_flow']}</div>", unsafe_allow_html=True)
            
            if recent_row['ivr_selections']:
                st.markdown("<div class='inquiry-label'>IVR Selections:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['ivr_selections']}</div>", unsafe_allow_html=True)
        
        with col2:
            if recent_row['user_type']:
                st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['user_type']}</div>", unsafe_allow_html=True)
            
            if recent_row['phone_email']:
                st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['phone_email']}</div>", unsafe_allow_html=True)
            
            if recent_row['membership_id']:
                st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['membership_id']}</div>", unsafe_allow_html=True)
        
        # Account details section - only show if there's actual account info
        has_account_info = (recent_row['account_name'] or recent_row['account_location'] or 
                           recent_row['account_reviews'] or recent_row['account_jobs'])
        
        if has_account_info:
            st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
            
            if recent_row['account_name']:
                st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['account_name']}</div>", unsafe_allow_html=True)
            
            if recent_row['account_location']:
                st.markdown("<div class='inquiry-label'>Location:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['account_location']}</div>", unsafe_allow_html=True)
            
            if recent_row['account_reviews']:
                st.markdown("<div class='inquiry-label'>Latest Reviews:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['account_reviews']}</div>", unsafe_allow_html=True)
            
            if recent_row['account_jobs']:
                st.markdown("<div class='inquiry-label'>Latest Jobs:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['account_jobs']}</div>", unsafe_allow_html=True)
            
            # Show project cost and payment status side by side if available
            if recent_row['project_cost'] or recent_row['payment_status']:
                st.markdown("<div class='inquiry-label'>Project Details:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>Project Cost: {recent_row['project_cost']} &nbsp;&nbsp;&nbsp; Status: {recent_row['payment_status']}</div>", unsafe_allow_html=True)
        
        # Scenario text section
        if recent_row['scenario_text']:
            st.markdown("<div class='inquiry-section'>Scenario Text</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{recent_row['scenario_text']}</div>", unsafe_allow_html=True)
        
        # Classification summary section
        st.markdown("<div class='inquiry-section'>Classification Summary</div>", unsafe_allow_html=True)
        
        if recent_row['classification']:
            st.markdown("<div class='inquiry-label'>Classification:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{recent_row['classification']}</div>", unsafe_allow_html=True)
        
        if recent_row['priority']:
            st.markdown("<div class='inquiry-label'>Priority:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{recent_row['priority']}</div>", unsafe_allow_html=True)
        
        if recent_row['summary']:
            st.markdown("<div class='inquiry-label'>Summary:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{recent_row['summary']}</div>", unsafe_allow_html=True)
        
        # Add FAQ suggestion and response suggestion
        st.markdown("<div class='inquiry-section'>Assistance Information</div>", unsafe_allow_html=True)
        
        # First search for relevant FAQ
        faq_category = ""
        # Try to parse the classification result to get related_faq_category
        try:
            # Check if we can find something related to faq_category in the summary
            if "faq" in recent_row['summary'].lower():
                faq_category = recent_row['summary'].lower().split("faq")[1].strip().strip(".:,")
        except:
            pass
            
        relevant_faq, faq_score = find_relevant_faq(recent_row['scenario_text'], df_faq)
        
        # Only display FAQ if it meets the relevance threshold
        if relevant_faq and faq_score >= 3:
            st.markdown("<div class='inquiry-label'>Suggested FAQ:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail'>{relevant_faq}</div>", unsafe_allow_html=True)
        
        # Generate response suggestion for email or whatsapp
        inbound_route = recent_row['inbound_route']
        if inbound_route in ["email", "whatsapp"]:
            # Recreate scenario structure from row data
            scenario_dict = {
                "inbound_route": recent_row['inbound_route'],
                "scenario_text": recent_row['scenario_text'],
                "user_type": recent_row['user_type'],
                "account_details": {
                    "name": recent_row['account_name'],
                    "location": recent_row['account_location'],
                    "latest_reviews": recent_row['account_reviews'],
                    "latest_jobs": recent_row['account_jobs'],
                    "project_cost": recent_row['project_cost'],
                    "payment_status": recent_row['payment_status']
                }
            }
            
            # Recreate classification structure
            classification_dict = {
                "classification": recent_row['classification'],
                "priority": recent_row['priority'],
                "summary": recent_row['summary']
            }
            
            response_suggestion = generate_response_suggestion(scenario_dict, classification_dict)
            
            st.markdown(f"<div class='inquiry-label'>Suggested {inbound_route.capitalize()} Response:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail' style='white-space: pre-wrap;'>{response_suggestion}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
    
    # Show previous inquiries in a collapsible expander
    if len(df) > 1:
        with st.expander("See More Inquiries"):
            # Show the rest of the inquiries (excluding the most recent one)
            for idx, row in df.iloc[1:].iterrows():
                # Use a header for each inquiry instead of a nested expander
                st.markdown(f"<div style='font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;'>Inquiry #{idx} - {row['classification']} (Priority: {row['priority']})</div>", unsafe_allow_html=True)
                st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['timestamp']}</div>", unsafe_allow_html=True)
                    
                    if row['inbound_route']:
                        st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['inbound_route']}</div>", unsafe_allow_html=True)
                    
                    if row['ivr_flow']:
                        st.markdown("<div class='inquiry-label'>IVR Flow:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['ivr_flow']}</div>", unsafe_allow_html=True)
                    
                    if row['ivr_selections']:
                        st.markdown("<div class='inquiry-label'>IVR Selections:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['ivr_selections']}</div>", unsafe_allow_html=True)
                
                with col2:
                    if row['user_type']:
                        st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['user_type']}</div>", unsafe_allow_html=True)
                    
                    if row['phone_email']:
                        st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['phone_email']}</div>", unsafe_allow_html=True)
                    
                    if row['membership_id']:
                        st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['membership_id']}</div>", unsafe_allow_html=True)
                
                # Account details section - only show if there's actual account info
                has_account_info = (row['account_name'] or row['account_location'] or 
                                   row['account_reviews'] or row['account_jobs'])
                
                if has_account_info:
                    st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
                    
                    if row['account_name']:
                        st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['account_name']}</div>", unsafe_allow_html=True)
                    
                    if row['account_location']:
                        st.markdown("<div class='inquiry-label'>Location:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['account_location']}</div>", unsafe_allow_html=True)
                    
                    if row['account_reviews']:
                        st.markdown("<div class='inquiry-label'>Latest Reviews:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['account_reviews']}</div>", unsafe_allow_html=True)
                    
                    if row['account_jobs']:
                        st.markdown("<div class='inquiry-label'>Latest Jobs:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['account_jobs']}</div>", unsafe_allow_html=True)
                    
                    # Show project cost and payment status side by side if available
                    if row['project_cost'] or row['payment_status']:
                        st.markdown("<div class='inquiry-label'>Project Details:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>Project Cost: {row['project_cost']} &nbsp;&nbsp;&nbsp; Status: {row['payment_status']}</div>", unsafe_allow_html=True)
                
                # Scenario text section
                if row['scenario_text']:
                    st.markdown("<div class='inquiry-section'>Scenario Text</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['scenario_text']}</div>", unsafe_allow_html=True)
                
                # Classification summary section
                st.markdown("<div class='inquiry-section'>Classification Summary</div>", unsafe_allow_html=True)
                
                if row['classification']:
                    st.markdown("<div class='inquiry-label'>Classification:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['classification']}</div>", unsafe_allow_html=True)
                
                if row['priority']:
                    st.markdown("<div class='inquiry-label'>Priority:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['priority']}</div>", unsafe_allow_html=True)
                
                if row['summary']:
                    st.markdown("<div class='inquiry-label'>Summary:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['summary']}</div>", unsafe_allow_html=True)
                
                # Add FAQ suggestion
                relevant_faq, faq_score = find_relevant_faq(row['scenario_text'], df_faq)
                
                # Only display FAQ if it meets the relevance threshold
                if relevant_faq and faq_score >= 3:
                    st.markdown("<div class='inquiry-section'>Assistance Information</div>", unsafe_allow_html=True)
                    st.markdown("<div class='inquiry-label'>Suggested FAQ:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{relevant_faq}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
else:
    st.write("No inquiries logged yet. Generate and classify a scenario.")

# -----------------------------------------------------------------------------
# EXPORT LOGGED DATA
# -----------------------------------------------------------------------------
st.subheader("Data Exports")
if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")

# -----------------------------------------------------------------------------
# ANALYTICS
# -----------------------------------------------------------------------------
st.subheader("Analytics")

# Then show summary charts with expanded information
with st.expander("View Analytics Dashboard"):
    st.subheader("Summary Analytics")
    
    # Row 1: Classification and Priority distribution
    colA, colB = st.columns(2)
    with colA:
        classification_counts = df["classification"].value_counts()
        
        # Create pie chart with plotly express
        fig1 = px.pie(
            values=classification_counts.values,
            names=classification_counts.index,
            title="Classification Distribution",
            hole=0.4,  # Makes it a donut chart
            color_discrete_sequence=["#4285F4", "#DB4437", "#F4B400", "#0F9D58", "#9C27B0", "#3F51B5", "#03A9F4", "#8BC34A"]
        )
        
        # Customize
        fig1.update_traces(textinfo='percent+label', pull=[0.05 if i == classification_counts.values.argmax() else 0 for i in range(len(classification_counts))])
        fig1.update_layout(
            legend=dict(orientation="h", y=-0.1),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Show classification breakdown as text too
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        for classification, count in classification_counts.items():
            percentage = (count / len(df)) * 100
            st.markdown(f"<div class='inquiry-label'>{classification}: {count} ({percentage:.1f}%)</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with colB:
        priority_counts = df["priority"].value_counts()
        
        # Create color mapping for priorities
        priority_colors = {
            "High": "#DB4437",    # Red for high
            "Medium": "#F4B400",  # Yellow for medium
            "Low": "#0F9D58"      # Green for low
        }
        
        # Create a pie chart using plotly express
        fig2 = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Priority Distribution",
            hole=0.4,  # Makes it a donut chart
            color_discrete_map=priority_colors
        )
        
        # Customize
        fig2.update_traces(textinfo='percent+label')
        fig2.update_layout(
            legend=dict(orientation="h", y=-0.1),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Show priority breakdown as text too
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        for priority, count in priority_counts.items():
            percentage = (count / len(df)) * 100
            st.markdown(f"<div class='inquiry-label'>{priority}: {count} ({percentage:.1f}%)</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Row 2: User type and Route distribution 
    colC, colD = st.columns(2)
    with colC:
        user_type_counts = df["user_type"].value_counts()
        
        # Create horizontal bar chart using plotly express
        fig3 = px.bar(
            x=user_type_counts.values,
            y=user_type_counts.index,
            orientation='h',
            title="User Type Distribution",
            text=user_type_counts.values,
            color_discrete_sequence=["#4285F4"]
        )
        
        # Customize
        fig3.update_layout(
            xaxis_title="Count",
            yaxis_title="",
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            xaxis=dict(gridcolor="#444"),
            yaxis=dict(gridcolor="#444")
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        with colD:
            route_counts = df["inbound_route"].value_counts()
            
            # Create color mapping for routes
            route_colors = {
                "phone": "#4285F4",     # Blue for phone
                "email": "#DB4437",     # Red for email
                "whatsapp": "#0F9D58",  # Green for whatsapp
                "web_form": "#F4B400"   # Yellow for web form
            }
            
            # Create a pie chart using plotly express
            fig4 = px.pie(
                values=route_counts.values,
                names=route_counts.index,
                title="Inbound Route Distribution",
                hole=0.4,  # Makes it a donut chart
                color_discrete_map=route_colors
            )
            
            # Customize
            fig4.update_traces(textinfo='percent+label')
            fig4.update_layout(
                legend=dict(orientation="h", y=-0.1),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )
            
            st.plotly_chart(fig4, use_container_width=True)

        # Common topics/themes from summaries
        st.subheader("Common Topics & Themes")
        topics_container = st.container()
        with topics_container:
            # Extract keywords from summaries to create topic tags
            all_summaries = " ".join(df["summary"].dropna())
            
            # Display a word cloud-like representation with the most common words
            common_words = ["account", "issue", "problem", "help", "request", "billing", "membership", 
                           "technical", "login", "access", "website", "app", "mobile", "payment",
                           "renewal", "subscription", "complaint", "feedback", "review", "rating",
                           "tradesperson", "homeowner", "service", "quality", "delay"]
            
            # Create a container with improved styling for a horizontal tag layout
            st.markdown("""
            <div class='info-container'>
                <div style="display: flex; flex-wrap: wrap; gap: 12px; justify-content: flex-start;">
            """, unsafe_allow_html=True)
            
            # Filter to only show words that appear in the summaries
            matching_words = [word for word in common_words if word.lower() in all_summaries.lower()]
            
            # Generate random counts for demo purposes
            for word in matching_words:
                count = random.randint(1, len(df))
                if count > 0:
                    # Calculate opacity based on count (more frequent = more opaque)
                    opacity = min(0.5 + (count / len(df)), 1.0)
                    # Create the tag with improved styling
                    st.markdown(f"""
                        <div style="display: inline-block; padding: 8px 16px; background-color: #2979FF; 
                             color: white; border-radius: 20px; font-size: 14px; font-weight: 500;
                             opacity: {opacity}; margin-bottom: 10px;">
                            {word.title()} ({count})
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
