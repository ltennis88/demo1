import streamlit as st
import openai
import pandas as pd
import json
import time
import random
import plotly.express as px
import os

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

/* Reduce sidebar width to half */
[data-testid="stSidebar"] {
    width: 12rem !important;
    min-width: 12rem !important;
    max-width: 12rem !important;
}

[data-testid="stSidebar"] > div:first-child {
    width: 12rem !important;
    min-width: 12rem !important;
    max-width: 12rem !important;
}

/* Sidebar content styling */
[data-testid="stSidebar"] {
    background-color: #1E1E1E !important;
    border-right: 1px solid #424242 !important;
}

[data-testid="stSidebar"] .element-container {
    padding-right: 1rem;
}

/* More compact sidebar content */
[data-testid="stSidebar"] .block-container {
    padding-top: 2rem !important;
}

/* Improve sidebar headings */
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-size: 1.2rem !important;
    margin-top: 1rem !important;
    margin-bottom: 0.75rem !important;
    color: #64B5F6 !important;
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

.nav-button {
    background-color: #121212;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    margin-right: 10px;
    text-decoration: none;
    display: inline-block;
    border: 2px solid #555;
    font-weight: 500;
}
.nav-button.active {
    background-color: transparent;
    border: 2px solid #0087CC;
    color: #0087CC;
}
.nav-button:hover:not(.active) {
    background-color: #1E1E1E;
    border-color: #0087CC;
    color: #0087CC;
}
.nav-container {
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

# Add a clear title for the main page
st.title("Contact Center AI Assistant")

# Create horizontal navigation with buttons - using Streamlit buttons directly
col1, col2, col3 = st.columns(3)
with col1:
    main_btn = st.button("🏠 Main Dashboard", use_container_width=True, 
                      type="primary" if st.session_state.get("page", "main") == "main" else "secondary")
with col2:
    inquiries_btn = st.button("📋 View Inquiries", use_container_width=True,
                          type="primary" if st.session_state.get("page", "main") == "inquiries" else "secondary")
with col3:
    analytics_btn = st.button("📊 Analytics Dashboard", use_container_width=True,
                          type="primary" if st.session_state.get("page", "main") == "analytics" else "secondary")

# Handle navigation
if "page" not in st.session_state:
    st.session_state["page"] = "main"

if main_btn:
    st.session_state["page"] = "main"
if inquiries_btn:
    st.session_state["page"] = "inquiries"
if analytics_btn:
    st.session_state["page"] = "analytics"

# Show the current page content
if st.session_state["page"] == "main":
    # Remove the duplicate title, just generate the new inquiry section directly
    st.header("Generate New Inquiry")
elif st.session_state["page"] == "inquiries":
    # Import and run view inquiries code
    from pages.view_inquiries import show_inquiries
    show_inquiries()
    st.stop()  # Stop execution of the rest of the script
elif st.session_state["page"] == "analytics":
    # Import and run analytics code
    from pages.analytics_dashboard import show_analytics
    show_analytics()
    st.stop()  # Stop execution of the rest of the script

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
        df = pd.read_csv("faq_taxonomy.csv", sep=';')  # Changed delimiter to semicolon
    except Exception as e:
        st.error("Error loading faq_taxonomy.csv. Please ensure the file exists and is in plain text CSV format.")
        df = pd.DataFrame(columns=["Type", "Category", "Question"])
    return df

@st.cache_data
def load_membership_terms():
    """
    Loads the membership terms and conditions from JSON file.
    Returns a dictionary containing structured T&Cs data.
    """
    try:
        with open("membership_terms.json", "r") as f:
            terms_data = json.load(f)
        return terms_data
    except Exception as e:
        st.error("Error loading membership_terms.json. Please ensure the file exists and is properly formatted.")
        return {
            "last_updated": "",
            "version": "",
            "sections": []
        }

df_faq = load_faq_csv()
membership_terms = load_membership_terms()

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
            "department", "subdepartment", "priority", "summary", "related_faq_category", "account_name", 
            "account_location", "account_reviews", "account_jobs", "project_cost", 
            "payment_status", "estimated_response_time", "agent_notes", "case_status"
        ])

def save_inquiries_to_file():
    """
    Saves the current inquiries DataFrame to inquiries.json
    """
    try:
        # Convert timestamps to strings to make them JSON serializable
        df_copy = st.session_state["inquiries"].copy()
        # Check if timestamp column exists and convert to string format
        if 'timestamp' in df_copy.columns and not df_copy.empty:
            df_copy['timestamp'] = df_copy['timestamp'].astype(str)
        
        # Convert DataFrame to JSON and save with nice formatting
        json_data = df_copy.to_dict(orient="records")
        
        # Save to file locally first - this will always work
        print(f"Saving {len(json_data)} inquiries to file")
        with open("inquiries.json", "w") as f:
            json.dump(json_data, f, indent=2)
        
        # Show a success message in the UI
        st.success(f"Successfully saved {len(json_data)} inquiries to local file.")
        
        # Note: GitHub integration is disabled in this demo
        # In a production app, you would need to use a GitHub API token
        # and proper authentication to push data to GitHub
        
        return True
    except Exception as e:
        print(f"Failed to save inquiries to file: {str(e)}")
        st.error(f"Failed to save inquiries to file: {str(e)}")
        return False

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
            "department", "subdepartment", "priority", "summary", "related_faq_category", "account_name", 
            "account_location", "account_reviews", "account_jobs", "project_cost", 
            "payment_status", "estimated_response_time", "agent_notes", "case_status"
        ])

if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

if "current_case_id" not in st.session_state:
    st.session_state["current_case_id"] = None

# Add these constants at the top of the file after the imports
TOKEN_COSTS = {
    "input": 0.15,      # $0.15 per 1M tokens
    "cached_input": 0.075,  # $0.075 per 1M tokens
    "output": 0.60      # $0.60 per 1M tokens
}

# Add this to the session state initialization section
if "token_usage" not in st.session_state:
    st.session_state["token_usage"] = {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0,
        "response_times": [],
        "generations": []
    }

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
# 5) SCENARIO GENERATION PROMPTS
###############################################################################
# Base prompt with common structure
base_prompt = """
You are a scenario generator for Checkatrade's inbound contact system. Your output must be a single, strictly formatted JSON object (with no extra commentary) that follows exactly the structure and rules below.

Below is the reference FAQ/taxonomy data:
{faq_context}

REFER TO THE FOLLOWING DEFINITIONS:

1. JSON Output Structure (ALL fields must be included exactly as below):
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
"""

###############################################################################
# 5) USER TYPE PROMPTS
###############################################################################

# Convert to cached variables similar to how FAQ_context is cached
@st.cache_data
def load_existing_homeowner_prompt():
    return """
Generate a realistic customer service scenario for Checkatrade's contact center involving an existing homeowner.

For existing homeowners, consider scenarios like:
- Complaints about tradesperson quality, behavior, or work
- Questions about a project they've arranged through Checkatrade
- Billing or payment disputes
- Problems with a tradesperson not showing up
- Questions about the guarantee
- How to leave a review
- How to find another tradesperson
- Account management issues

Include:
1. A randomized inbound_route (phone, email, whatsapp, or web_form)
2. Random phone number or email based on the route
3. Appropriate membership_id for an existing homeowner
4. Realistic account details including name, location, and a recent review or job
5. A detailed scenario_text from the customer's perspective

The response should be in valid JSON format like this:
{
    "inbound_route": "phone",
    "ivr_flow": "homeowner_support",
    "ivr_selections": ["existing_customer", "complaint"],
    "user_type": "existing_homeowner",
    "phone_email": "+44 7911 123456",
    "membership_id": "H-12345678",
    "account_details": {
        "name": "Sarah",
        "surname": "Johnson",
        "location": "Manchester",
        "latest_reviews": "Left a 4-star review for PlumbPerfect Ltd 3 weeks ago",
        "latest_jobs": "Bathroom renovation completed on 15 May 2023",
        "project_cost": "£4,500",
        "payment_status": "Paid in full"
    },
    "scenario_text": "I'm calling about the bathroom renovation that was completed last month. The sink has started leaking and the tradesperson isn't responding to my calls. I need someone to come fix it urgently as water is damaging my cabinet."
}
"""

@st.cache_data
def load_prospective_homeowner_prompt():
    return """
Generate a realistic customer service scenario for Checkatrade's contact center involving a prospective homeowner (not yet a customer).

For prospective homeowners, consider scenarios like:
- Questions about how Checkatrade works
- How to find a tradesperson for a specific job
- Questions about vetting or qualification checking
- Inquiries about the Checkatrade guarantee
- Questions about becoming a member
- How reviews work and if they can be trusted
- Comparing quotes from multiple tradespeople

Include:
1. A randomized inbound_route (phone, email, whatsapp, or web_form)
2. Random phone number or email based on the route
3. Empty account details (as they are not yet a customer)
4. No membership_id
5. A detailed scenario_text from the prospective customer's perspective

The response should be in valid JSON format like this:
{
    "inbound_route": "email",
    "ivr_flow": "",
    "ivr_selections": [],
    "user_type": "prospective_homeowner",
    "phone_email": "jane.smith@example.com",
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
    "scenario_text": "I'm planning a kitchen renovation and I'm not sure how to get started with Checkatrade. Do you just show me a list of companies, or do you help match me with the right tradesperson? And how do I know if they're reliable?"
}
"""

@st.cache_data
def load_existing_tradesperson_prompt():
    return """
Generate a realistic customer service scenario for Checkatrade's contact center involving an existing tradesperson member.

For existing tradespeople, consider scenarios like:
- Questions about membership fees or renewal
- How to respond to customer reviews (especially negative ones)
- Technical issues with their profile or the app
- Billing or payment queries
- Questions about upgrading membership
- Lead generation concerns
- Insurance or qualification verification updates
- Competition concerns with other tradespeople

Include:
1. A randomized inbound_route (phone, email, whatsapp, or web_form)
2. Random phone number or email based on the route
3. Appropriate membership_id for a tradesperson (T- prefix)
4. Realistic account details including business name, location, and recent activity
5. A detailed scenario_text from the tradesperson's perspective

The response should be in valid JSON format like this:
{
    "inbound_route": "phone",
    "ivr_flow": "tradesperson_support",
    "ivr_selections": ["existing_member", "billing"],
    "user_type": "existing_tradesperson",
    "phone_email": "+44 7700 900123",
    "membership_id": "T-87654321",
    "account_details": {
        "name": "Johnson Plumbing",
        "surname": "Ltd",
        "location": "Liverpool",
        "latest_reviews": "Received a 3-star review 2 days ago that seems unfair",
        "latest_jobs": "3 new leads in the past week, 1 converted to quote",
        "project_cost": "Monthly Premium membership: £74.99",
        "payment_status": "Next payment due: 05/08/2023"
    },
    "scenario_text": "I'm calling about a negative review I received last week. The customer complained about delays, but they kept changing the requirements which caused the delays. I think the review is unfair and damaging to my business. Can you help me get it removed or respond to it appropriately?"
}
"""

@st.cache_data
def load_prospective_tradesperson_prompt():
    return """
Generate a realistic customer service scenario for Checkatrade's contact center involving a prospective tradesperson (interested in joining).

For prospective tradespeople, consider scenarios like:
- Questions about how to join Checkatrade
- Inquiries about membership costs and benefits
- Questions about the vetting process
- How lead generation works
- What documentation they need to provide
- How the review system works
- Comparing different membership levels
- Questions about competitors like MyBuilder or RatedPeople

Include:
1. A randomized inbound_route (phone, email, whatsapp, or web_form)
2. Random phone number or email based on the route
3. No membership_id (as they are not yet a member)
4. Empty account details (as they don't have an account yet)
5. A detailed scenario_text from the prospective tradesperson's perspective

The response should be in valid JSON format like this:
{
    "inbound_route": "web_form",
    "ivr_flow": "",
    "ivr_selections": [],
    "user_type": "prospective_tradesperson",
    "phone_email": "mike.builders@example.com",
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
    "scenario_text": "I'm interested in joining Checkatrade as a plumber. What are the membership fees and requirements?"
}
"""

# Load the cached prompts once
existing_homeowner_prompt = load_existing_homeowner_prompt()
prospective_homeowner_prompt = load_prospective_homeowner_prompt()
existing_tradesperson_prompt = load_existing_tradesperson_prompt()
prospective_tradesperson_prompt = load_prospective_tradesperson_prompt()

@st.cache_data
def get_user_type_prompt(user_type):
    """Returns the appropriate prompt based on user type."""
    prompts = {
        "existing_homeowner": existing_homeowner_prompt,
        "prospective_homeowner": prospective_homeowner_prompt,
        "existing_tradesperson": existing_tradesperson_prompt,
        "prospective_tradesperson": prospective_tradesperson_prompt
    }
    return prompts.get(user_type, "")

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
def calculate_token_cost(tokens, token_type):
    """Calculate cost for a given number of tokens and type."""
    cost_per_million = TOKEN_COSTS.get(token_type, 0)
    return (tokens / 1_000_000) * cost_per_million

def generate_scenario(selected_route=None, selected_user_type=None):
    """
    Generates a scenario using OpenAI's ChatCompletion.
    If selected_route is provided (phone, whatsapp, email, web_form), force that route.
    If selected_user_type is provided, force that user type.
    """
    # Start timing
    start_time = time.time()
    
    # For random user type, we'll randomize it ourselves to ensure true randomness
    should_randomize_user_type = selected_user_type is None
    
    # If we're randomizing, do it now so we can get the correct prompt
    if should_randomize_user_type:
        user_types = ["existing_homeowner", "existing_tradesperson", 
                    "prospective_homeowner", "prospective_tradesperson"]
        selected_user_type = random.choice(user_types)
    
    # Get the appropriate user type prompt - this is now guaranteed to have a user type
    user_type_prompt = get_user_type_prompt(selected_user_type)
    
    # Start with base prompt
    user_content = base_prompt + "\n\n" + user_type_prompt
    
    # Add route and user type instructions
    if selected_route:
        user_content += f"\n\nForce inbound_route to '{selected_route}'."
    
    # Always specify the user type now, since we either have it from input or randomly selected it
    user_content += f"\n\nForce user_type to '{selected_user_type}'."

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
        
        # Calculate token usage and costs
        input_tokens = response["usage"]["prompt_tokens"]
        output_tokens = response["usage"]["completion_tokens"]
        total_tokens = response["usage"]["total_tokens"]
        
        # Calculate costs - since we're using cached prompts, use the cached_input rate
        input_cost = calculate_token_cost(input_tokens, "cached_input")
        output_cost = calculate_token_cost(output_tokens, "output")
        total_cost = input_cost + output_cost
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Store usage data
        usage_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "response_time": response_time,
            "operation": "generation"
        }
        
        st.session_state["token_usage"]["generations"].append(usage_data)
        st.session_state["token_usage"]["total_input_tokens"] += input_tokens
        st.session_state["token_usage"]["total_output_tokens"] += output_tokens
        st.session_state["token_usage"]["total_cost"] += total_cost
        st.session_state["token_usage"]["response_times"].append(response_time)
        
        raw_reply = response["choices"][0]["message"]["content"].strip()
        
        try:
            scenario_data = json.loads(raw_reply)
            
            # Ensure account details match the user type
            if "prospective" in selected_user_type:
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
            
            # Force the user type to match what was selected/randomized
            scenario_data["user_type"] = selected_user_type
            
            return scenario_data
            
        except Exception as e:
            return {
                "inbound_route": "error",
                "ivr_flow": "",
                "ivr_selections": [],
                "user_type": selected_user_type,
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
            return {
                "inbound_route": "error",
                "ivr_flow": "",
                "ivr_selections": [],
                "user_type": selected_user_type,
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

###############################################################################
# 8) HELPER: CLASSIFY SCENARIO VIA OPENAI
###############################################################################
def classify_scenario(text):
    # Start timing
    start_time = time.time()
    
    # Enhanced classification prompt with departments and subdepartments
    enhanced_classification_prompt = classification_prompt_template.replace("{SCENARIO}", text)
    enhanced_classification_prompt += """
    
    Please also identify:
    1. Department: The main department that should handle this inquiry
       Options: "Consumer Support", "Technical Support", "Quality Assurance", "Tradesperson Support", "Finance", "Legal"
    
    2. Subdepartment: The specific team within the department
       For Consumer Support: "Account Issues", "Job Issues", "Payments", "Resolving Issues"
       For Technical Support: "App Issues", "Website Issues", "Integration Issues"
       For Quality Assurance: "Tradesperson Vetting", "Review Verification", "Complaint Investigation"
       For Tradesperson Support: "Account Management", "Jobs", "Payments", "Technical Issues"
       For Finance: "Billing", "Refunds", "Financial Disputes"
       For Legal: "Contract Issues", "Guarantee Claims", "Compliance"
    
    Return the enhanced JSON with these additional fields:
    {
      "classification": "...",
      "department": "...",
      "subdepartment": "...",
      "priority": "High|Medium|Low",
      "summary": "...",
      "related_faq_category": "...",
      "estimated_response_time": "..." // E.g. "24 hours", "48 hours", "1 week" based on priority
    }
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Updated to use gpt-4o-mini
        messages=[
            {"role": "system", "content": "You classify inbound queries for Checkatrade."},
            {"role": "user", "content": enhanced_classification_prompt}
        ],
        temperature=0.5,
        max_tokens=400
    )
    
    # Calculate token usage and costs
    input_tokens = response["usage"]["prompt_tokens"]
    output_tokens = response["usage"]["completion_tokens"]
    total_tokens = response["usage"]["total_tokens"]
    
    # Calculate costs - since we're using cached prompts, use the cached_input rate
    input_cost = calculate_token_cost(input_tokens, "cached_input")
    output_cost = calculate_token_cost(output_tokens, "output")
    total_cost = input_cost + output_cost
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Store usage data
    usage_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "response_time": response_time,
        "operation": "classification"  # Add operation type to distinguish from scenario generation
    }
    
    st.session_state["token_usage"]["generations"].append(usage_data)
    st.session_state["token_usage"]["total_input_tokens"] += input_tokens
    st.session_state["token_usage"]["total_output_tokens"] += output_tokens
    st.session_state["token_usage"]["total_cost"] += total_cost
    st.session_state["token_usage"]["response_times"].append(response_time)
    
    raw_reply = response["choices"][0]["message"]["content"].strip()
    try:
        classification_data = json.loads(raw_reply)
        return classification_data
    except Exception as e:
        return {
            "classification": "General",
            "department": "Consumer Support",
            "subdepartment": "General Inquiries",
            "priority": "Medium",
            "summary": "Could not parse classification JSON.",
            "related_faq_category": "",
            "estimated_response_time": "48 hours"
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
    
    # Check if required columns exist
    required_columns = ["Type", "Category", "Question"]
    if not all(col in faq_dataframe.columns for col in required_columns):
        st.warning("FAQ data is missing required columns. Expected: Type, Category, Question")
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
                warranty_matches.append((row.get("Question", ""), overlap_count + 5))  # Bonus for warranty match
        
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
                    return row.get("Question", ""), 8  # High relevance for direct issue match
    
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
            try:
                # Look for matches in both the main category and subcategory columns
                matched_rows = faq_dataframe[
                    faq_dataframe["Type"].str.lower().str.contains(category.lower(), na=False) |  # Main category
                    faq_dataframe["Category"].str.lower().str.contains(category.lower(), na=False)    # Subcategory
                ]
                
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
                            best_match = row.get("Question", "")
                    
                    if best_match and best_match_score >= 3:  # Higher threshold for relevance
                        # Relevance is based on both category match and word match
                        relevance = best_match_score
                        return best_match, relevance
            except Exception as e:
                st.warning(f"Error processing category {category}: {str(e)}")
                continue
    
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
            best_match = row.get("Question", "")
    
    if best_match and best_score >= 3:  # Higher threshold for relevance
        return best_match, best_score
    
    return None, 0

def generate_response_suggestion(scenario, classification_result):
    """
    Generate a suggested response based on scenario type (email/whatsapp)
    """
    inbound_route = scenario.get("inbound_route", "")
    scenario_text = scenario.get("scenario_text", "").lower()
    user_type = scenario.get("user_type", "")
    classification = classification_result.get("classification", "")
    
    # Get account details if available
    account_details = scenario.get("account_details", {})
    name = f"{account_details.get('name', '')} {account_details.get('surname', '')}".strip()
    first_name = name.split()[0] if name else ""
    latest_jobs = account_details.get("latest_jobs", "")
    latest_reviews = account_details.get("latest_reviews", "")
    project_cost = account_details.get("project_cost", "")
    
    # Check if this is a membership-related query
    is_membership_query = any(word in scenario_text for word in ["membership", "join", "sign up", "register", "become a member"])
    
    # If it's a membership query, get relevant terms
    membership_info = ""
    if is_membership_query and "tradesperson" in user_type:
        # Find relevant membership terms based on the query
        relevant_terms = []
        for section in membership_terms.get("sections", []):
            # Safely get content from section
            section_content = section.get("content", "")
            if section_content and any(word in scenario_text for word in section.get("title", "").lower().split()):
                relevant_terms.append(section_content)
            
            # Safely handle subsections
            for subsection in section.get("subsections", []):
                subsection_content = subsection.get("content", "")
                if subsection_content and any(word in scenario_text for word in subsection.get("title", "").lower().split()):
                    relevant_terms.append(subsection_content)
        
        if relevant_terms:
            membership_info = " ".join(relevant_terms)

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
    if "complaint" in classification.lower() or "job" in scenario_text or "issue" in scenario_text:
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
# Dashboard Main Page - REMOVE SECOND TITLE AND NAVIGATION
# The main title and navigation are already at the top of the file (lines ~168-188)
# Remove duplicate title and navigation here

# Generate New Inquiry Section
# Removed duplicate header here, already defined at line 234

# Route Selection
st.markdown("<div class='inquiry-label'>Route Selection:</div>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([1, 0.75, 0.75, 0.75, 0.75])

with col1:
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
        
        # Get the most recent generation data - check if the list is not empty first
        if st.session_state["token_usage"]["generations"]:
            latest_generation = st.session_state["token_usage"]["generations"][-1]
            
            # Create columns for metrics display
            st.markdown("### Generation Metrics")
            st.markdown("<div class='info-container'>", unsafe_allow_html=True)
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "Response Time",
                    f"{latest_generation['response_time']:.2f}s"
                )
            
            with metric_col2:
                st.metric(
                    "Input Tokens",
                    f"{latest_generation['input_tokens']:,}",
                    f"${latest_generation['input_cost']:.4f}"
                )
            
            with metric_col3:
                st.metric(
                    "Output Tokens",
                    f"{latest_generation['output_tokens']:,}",
                    f"${latest_generation['output_cost']:.4f}"
                )
            
            with metric_col4:
                st.metric(
                    "Total Cost",
                    f"${latest_generation['total_cost']:.4f}"
                )
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.success("Scenario generated successfully!")

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
        
        if scenario.get('membership_id'):
            st.markdown("<div class='agent-label'>Membership ID:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('membership_id', 'N/A')}</div>", unsafe_allow_html=True)
        
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
                    "department": classification_result.get("department", "Consumer Support"),
                    "subdepartment": classification_result.get("subdepartment", "General Inquiries"),
                    "priority": classification_result.get("priority", "Medium"),
                    "summary": classification_result.get("summary", ""),
                    "related_faq_category": classification_result.get("related_faq_category", ""),
                    "account_name": f"{account_details.get('name', '')} {account_details.get('surname', '')}".strip(),
                    "account_location": account_details.get("location", ""),
                    "account_reviews": account_details.get("latest_reviews", ""),
                    "account_jobs": account_details.get("latest_jobs", ""),
                    "project_cost": account_details.get("project_cost", ""),
                    "payment_status": account_details.get("payment_status", ""),
                    "estimated_response_time": classification_result.get("estimated_response_time", "48 hours"),
                    "agent_notes": "",  # Initialize with empty agent notes
                    "case_status": "New"  # Initial case status
                }

                st.session_state["inquiries"] = pd.concat(
                    [st.session_state["inquiries"], pd.DataFrame([new_row])],
                    ignore_index=True
                )
                
                # Store the case index for reference
                st.session_state["current_case_id"] = len(st.session_state["inquiries"]) - 1
                
                # Save to file
                save_inquiries_to_file()
                
                # Get the most recent classification data
                if st.session_state["token_usage"]["generations"]:
                    # Find the most recent classification operation
                    classification_data = None
                    for data in reversed(st.session_state["token_usage"]["generations"]):
                        if data.get("operation") == "classification":
                            classification_data = data
                            break
                    
                    if classification_data:
                        # Display classification metrics
                        st.markdown("### Classification Metrics")
                        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        with metric_col1:
                            st.metric(
                                "Response Time",
                                f"{classification_data['response_time']:.2f}s"
                            )
                        
                        with metric_col2:
                            st.metric(
                                "Input Tokens",
                                f"{classification_data['input_tokens']:,}",
                                f"${classification_data['input_cost']:.4f}"
                            )
                        
                        with metric_col3:
                            st.metric(
                                "Output Tokens",
                                f"{classification_data['output_tokens']:,}",
                                f"${classification_data['output_cost']:.4f}"
                            )
                        
                        with metric_col4:
                            st.metric(
                                "Total Cost",
                                f"${classification_data['total_cost']:.4f}"
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Determine priority class
                priority_class = "priority-medium"
                if new_row["priority"] == "High":
                    priority_class = "priority-high"
                elif new_row["priority"] == "Low":
                    priority_class = "priority-low"
                
                # Create classification section with Streamlit components instead of raw HTML
                st.markdown("<h3>Classification Results</h3>", unsafe_allow_html=True)
                
                # Create a styled container for the classification results
                st.markdown("""
                <style>
                .styled-container {
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    border: 1px solid #424242;
                }
                .result-row {
                    display: flex;
                    margin-bottom: 12px;
                }
                .result-label {
                    width: 220px;
                    font-weight: bold;
                    color: #64B5F6;
                }
                .result-value {
                    flex-grow: 1;
                    background-color: #2C2C2C;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Start the styled container
                st.markdown("<div class='styled-container'>", unsafe_allow_html=True)
                
                # Create each classification field with proper formatting
                st.markdown(f"""
                <div class='result-row'>
                    <div class='result-label'>Classification:</div>
                    <div class='result-value'>{classification_result.get("classification", "Unknown")}</div>
                </div>
                
                <div class='result-row'>
                    <div class='result-label'>Department:</div>
                    <div class='result-value'>{classification_result.get("department", "Unknown")}</div>
                </div>
                
                <div class='result-row'>
                    <div class='result-label'>Subdepartment:</div>
                    <div class='result-value'>{classification_result.get("subdepartment", "Unknown")}</div>
                </div>
                
                <div class='result-row'>
                    <div class='result-label'>Priority:</div>
                    <div class='result-value'>
                        <span class='priority-{classification_result.get("priority", "medium").lower()}'>
                            {classification_result.get("priority", "Medium")}
                        </span>
                    </div>
                </div>
                
                <div class='result-row'>
                    <div class='result-label'>Estimated Response Time:</div>
                    <div class='result-value'>{classification_result.get("estimated_response_time", "Unknown")}</div>
                </div>
                
                <div class='result-row'>
                    <div class='result-label'>Summary:</div>
                    <div class='result-value'>{classification_result.get("summary", "No summary available")}</div>
                </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Get relevant FAQ based on the classification result and scenario text
                faq_category = classification_result.get("related_faq_category", "")
                relevant_faq = None
                faq_relevance_score = 0

                # First try to use the model's suggested FAQ category
                if faq_category and faq_category.lower() not in ["", "none", "n/a"]:
                    # First check if Category column exists
                    if "Category" in df_faq.columns:
                    # Filter FAQ dataframe by the suggested category
                        category_matches = df_faq[df_faq["Category"].str.lower().str.contains(faq_category.lower(), na=False)]
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
                    else:
                        # If Category column doesn't exist, try searching in Type column instead
                        if "Type" in df_faq.columns:
                            category_matches = df_faq[df_faq["Type"].str.lower().str.contains(faq_category.lower(), na=False)]
                            if not category_matches.empty:
                                # Same matching logic as above
                                best_match = None
                                best_score = 0
                                
                                for _, row in category_matches.iterrows():
                                    question = str(row.get("Question", "")).lower()
                                    scenario_lower = scenario_text.lower()
                                    score = sum(1 for word in scenario_lower.split() if len(word) > 4 and word in question)
                                    if score > best_score:
                                        best_score = score
                                        best_match = row["Question"]
                                
                                if best_match and best_score >= 2:
                                    relevant_faq = best_match
                                    faq_relevance_score = best_score + 2

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
                    st.markdown("""
                    <div class="classification-card">
                        <div class="classification-header">Relevant FAQ</div>
                        <div class="field-value">""" + relevant_faq + """</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Generate response suggestion for email or whatsapp
                inbound_route = st.session_state["generated_scenario"].get("inbound_route", "")
                if inbound_route in ["email", "whatsapp"]:
                    response_suggestion = generate_response_suggestion(
                        st.session_state["generated_scenario"], 
                        classification_result
                    )
                    st.markdown("""
                    <div class="classification-card">
                        <div class="classification-header">Suggested """ + inbound_route.capitalize() + """ Response</div>
                        <div class="field-value" style="white-space: pre-wrap;">""" + response_suggestion + """</div>
                    </div>
                    """, unsafe_allow_html=True)

                # After displaying the classification card, add the agent action area
                st.markdown("""
                <div class="classification-card">
                    <div class="classification-header">Agent Actions</div>
                """, unsafe_allow_html=True)

                # Case status selection
                case_status_options = ["New", "In Progress", "Awaiting Customer", "Awaiting Tradesperson", "Resolved", "Closed"]
                selected_status = st.selectbox(
                    "Update Case Status:",
                    options=case_status_options,
                    index=case_status_options.index("New") if st.session_state["inquiries"].iloc[st.session_state["current_case_id"]]["case_status"] == "New" 
                    else case_status_options.index(st.session_state["inquiries"].iloc[st.session_state["current_case_id"]]["case_status"])
                )

                # Agent notes text area
                agent_notes = st.text_area(
                    "Agent Notes:",
                    value=st.session_state["inquiries"].iloc[st.session_state["current_case_id"]]["agent_notes"],
                    height=150,
                    placeholder="Enter your notes about the case here..."
                )

                # Save button for agent updates
                if st.button("Save Agent Updates", use_container_width=True):
                    # Update the DataFrame with the new status and notes
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "case_status"] = selected_status
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "agent_notes"] = agent_notes
                    
                    # Save to file
                    save_inquiries_to_file()
                    
                    st.success(f"Case {st.session_state['current_case_id']} updated - Status: {selected_status}")

                st.markdown("</div>", unsafe_allow_html=True)

                # Add metrics for the classification tokens and cost
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    last_usage = st.session_state["token_usage"]["generations"][-1]
                    response_time = last_usage["response_time"]
                    st.metric("Response Time", f"{response_time:.2f}s")
                
                with col2:
                    input_tokens = last_usage["input_tokens"] 
                    input_cost = last_usage["input_cost"]
                    st.metric("Input Tokens", f"{input_tokens} (${input_cost:.4f})")
                
                with col3:
                    output_tokens = last_usage["output_tokens"]
                    output_cost = last_usage["output_cost"]
                    st.metric("Output Tokens", f"{output_tokens} (${output_cost:.4f})")
                    
                with col4:
                    total_cost = last_usage["total_cost"]
                    st.metric("Total Cost", f"${total_cost:.4f}")
                
                # Store all classification fields in the inquiries DataFrame
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "classification"] = classification_result.get("classification", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "department"] = classification_result.get("department", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "subdepartment"] = classification_result.get("subdepartment", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "priority"] = classification_result.get("priority", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "estimated_response_time"] = classification_result.get("estimated_response_time", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "summary"] = classification_result.get("summary", "")
                st.session_state["inquiries"].at[st.session_state["current_case_id"], "related_faq_category"] = classification_result.get("related_faq_category", "")
                
                # Also save the generated response suggestion if applicable
                if inbound_route in ["email", "whatsapp"] and 'response_suggestion' in locals():
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "response_suggestion"] = response_suggestion
                
                # Save any relevant FAQ that was found
                if relevant_faq and faq_relevance_score >= 3:
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "relevant_faq"] = relevant_faq
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "faq_relevance_score"] = faq_relevance_score
                    
                # Save to file again to ensure all classification fields are stored
                save_inquiries_to_file()
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
                           recent_row['account_reviews'] or recent_row['account_jobs'] or
                           recent_row['membership_id'])
        
        if has_account_info:
            st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
            
            if recent_row['account_name']:
                st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['account_name']}</div>", unsafe_allow_html=True)
            
            if recent_row['membership_id']:
                st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['membership_id']}</div>", unsafe_allow_html=True)
            
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
                                   row['account_reviews'] or row['account_jobs'] or
                                   row['membership_id'])
                
                if has_account_info:
                    st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
                    
                    if row['account_name']:
                        st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['account_name']}</div>", unsafe_allow_html=True)
                    
                    if row['membership_id']:
                        st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['membership_id']}</div>", unsafe_allow_html=True)
                    
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
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv", key="main_csv_download")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json", key="main_json_download")
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
        
        # Convert value_counts to DataFrame for plotly
        user_type_df = pd.DataFrame({
            'User Type': user_type_counts.index,
            'Count': user_type_counts.values
        })
        
        # Create horizontal bar chart using plotly express
        fig3 = px.bar(
            user_type_df,
            x='Count',
            y='User Type',
            orientation='h',
            title="User Type Distribution",
            text='Count',
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

    # Add new Token Usage Analytics section
    st.subheader("Token Usage Analytics")
    
    if st.session_state["token_usage"]["generations"]:
        # Create DataFrame from token usage data
        df_tokens = pd.DataFrame(st.session_state["token_usage"]["generations"])
        df_tokens['timestamp'] = pd.to_datetime(df_tokens['timestamp'])
        
        # Split data by operation, handling case where operation field might not exist
        if 'operation' in df_tokens.columns:
            scenario_data = df_tokens[df_tokens['operation'].isna()]  # Scenario generation doesn't have operation field
            classification_data = df_tokens[df_tokens['operation'] == 'classification']
        else:
            # If operation field doesn't exist, treat all data as scenario generation
            scenario_data = df_tokens
            classification_data = pd.DataFrame()
        
        # Calculate averages for scenario generation
        if not scenario_data.empty:
            st.markdown("### Scenario Generation Metrics")
            avg_response_time_scenario = scenario_data['response_time'].mean()
            avg_input_tokens_scenario = scenario_data['input_tokens'].mean()
            avg_output_tokens_scenario = scenario_data['output_tokens'].mean()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Average Response Time",
                    f"{avg_response_time_scenario:.2f}s",
                    f"Total: {scenario_data['response_time'].sum():.2f}s"
                )
            
            with col2:
                st.metric(
                    "Average Input Tokens",
                    f"{avg_input_tokens_scenario:,.0f}",
                    f"Total: {scenario_data['input_tokens'].sum():,}"
                )
            
            with col3:
                st.metric(
                    "Average Output Tokens",
                    f"{avg_output_tokens_scenario:,.0f}",
                    f"Total: {scenario_data['output_tokens'].sum():,}"
                )
        
        # Calculate averages for classification
        if not classification_data.empty:
            st.markdown("### Classification Metrics")
            avg_response_time_class = classification_data['response_time'].mean()
            avg_input_tokens_class = classification_data['input_tokens'].mean()
            avg_output_tokens_class = classification_data['output_tokens'].mean()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Average Response Time",
                    f"{avg_response_time_class:.2f}s",
                    f"Total: {classification_data['response_time'].sum():.2f}s"
                )
            
            with col2:
                st.metric(
                    "Average Input Tokens",
                    f"{avg_input_tokens_class:,.0f}",
                    f"Total: {classification_data['input_tokens'].sum():,}"
                )
            
            with col3:
                st.metric(
                    "Average Output Tokens",
                    f"{avg_output_tokens_class:,.0f}",
                    f"Total: {classification_data['output_tokens'].sum():,}"
                )
        
        # Create line charts for token usage over time
        st.markdown("### Token Usage Over Time")
        
        # Scenario Generation Chart
        if not scenario_data.empty:
            fig_scenario = px.line(
                scenario_data,
                x='timestamp',
                y=['input_tokens', 'output_tokens'],
                title='Scenario Generation Token Usage',
                labels={'value': 'Tokens', 'timestamp': 'Time'}
            )
            
            fig_scenario.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="#444"),
                yaxis=dict(gridcolor="#444")
            )
            
            st.plotly_chart(fig_scenario, use_container_width=True)
        
        # Classification Chart
        if not classification_data.empty:
            fig_class = px.line(
                classification_data,
                x='timestamp',
                y=['input_tokens', 'output_tokens'],
                title='Classification Token Usage',
                labels={'value': 'Tokens', 'timestamp': 'Time'}
            )
            
            fig_class.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                xaxis=dict(gridcolor="#444"),
                yaxis=dict(gridcolor="#444")
            )
            
            st.plotly_chart(fig_class, use_container_width=True)
        
        # Display cost breakdown
        st.markdown("### Cost Breakdown")
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        
        # Scenario Generation Costs
        if not scenario_data.empty:
            st.markdown("<div class='inquiry-section'>Scenario Generation</div>", unsafe_allow_html=True)
            scenario_input_cost = scenario_data['input_cost'].sum()
            scenario_output_cost = scenario_data['output_cost'].sum()
            scenario_total_cost = scenario_data['total_cost'].sum()
            
            st.markdown(f"<div class='inquiry-label'>Input Cost: ${scenario_input_cost:.4f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-label'>Output Cost: ${scenario_output_cost:.4f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-label'>Total Cost: ${scenario_total_cost:.4f}</div>", unsafe_allow_html=True)
        
        # Classification Costs
        if not classification_data.empty:
            st.markdown("<div class='inquiry-section'>Classification</div>", unsafe_allow_html=True)
            class_input_cost = classification_data['input_cost'].sum()
            class_output_cost = classification_data['output_cost'].sum()
            class_total_cost = classification_data['total_cost'].sum()
            
            st.markdown(f"<div class='inquiry-label'>Input Cost: ${class_input_cost:.4f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-label'>Output Cost: ${class_output_cost:.4f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-label'>Total Cost: ${class_total_cost:.4f}</div>", unsafe_allow_html=True)
        
        # Overall Totals
        st.markdown("<div class='inquiry-section'>Overall Totals</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='inquiry-label'>Total Input Cost: ${df_tokens['input_cost'].sum():.4f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='inquiry-label'>Total Output Cost: ${df_tokens['output_cost'].sum():.4f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='inquiry-label'>Total Cost: ${st.session_state['token_usage']['total_cost']:.4f}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No token usage data available yet. Generate some scenarios to see analytics.")
