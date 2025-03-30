import streamlit as st
import openai
import pandas as pd
import json
import time
import random

###############################################################################
# 1) PAGE CONFIGURATION & OPENAI SETUP
###############################################################################
st.set_page_config(layout="wide", page_title="Checkatrade AI Demo", initial_sidebar_state="collapsed", 
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
if "inquiries" not in st.session_state:
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
You are a scenario generator for Checkatrade's inbound contact system.

Below is FAQ/taxonomy data for reference:
{faq_context}

Produce a single inbound scenario in STRICT JSON FORMAT ONLY (no extra text).
The JSON object must have exactly these keys:
- "inbound_route": one of "phone", "whatsapp", "email", "web_form".
- "ivr_flow": a string (if inbound_route is "phone", else an empty string).
- "ivr_selections": an array of pressed options if phone, else an empty array.
- "user_type": one of "existing_tradesperson", "existing_homeowner", "prospective_tradesperson", "prospective_homeowner".
- "phone_email": a random phone number (if route is phone or whatsapp) or a random email (if email) or empty.
- "membership_id": for an existing tradesperson (e.g., "T-12345") or empty otherwise.
- "account_details": an object with:
    - "name": if existing, a random first name; otherwise empty.
    - "surname": if existing, a random surname; otherwise empty.
    - "location": if existing, a UK location; otherwise empty.
    - "latest_reviews": 
        * For homeowners: reviews they've given to tradespeople (e.g., "Has given 5-star reviews to recent plumber and electrician"); 
        * For tradespeople: reviews they've received (e.g., "Received a 5-star review for a recent kitchen renovation"); 
        * Otherwise empty.
    - "latest_jobs": 
        * For homeowners: jobs completed for them (e.g., "Had a bathroom refurbishment completed last month"); 
        * For tradespeople: jobs they've completed (e.g., "Completed a kitchen renovation last week"); 
        * Otherwise empty.
    - "project_cost": if existing user with recent jobs, a random cost (e.g. "£2,500"); otherwise empty.
    - "payment_status": if existing user with recent jobs, one of "Paid", "Pending", "Partial Payment"; otherwise empty.
- "scenario_text": a short, realistic reason for contacting Checkatrade (for example, a billing issue, a complaint, membership renewal, or looking for a tradesperson).

Rules:
1. Return ONLY valid JSON with no extra commentary or code fences.
2. If inbound_route is "phone", include realistic ivr_flow and ivr_selections.
3. For "existing" user types, fill out account_details with plausible data.
4. The scenario_text must be specific to Checkatrade.
5. Remember: homeowners GIVE reviews and have jobs completed FOR them; tradespeople RECEIVE reviews and complete jobs FOR homeowners.
"""

###############################################################################
# 6) CLASSIFICATION PROMPT
###############################################################################
classification_prompt_template = """
You are an AI classification assistant for Checkatrade.
Given the scenario text below, return a JSON object with keys:
{
  "classification": "...",  // e.g., "Billing", "Membership", "Tech Support", "Complaints", etc.
  "priority": "...",        // "High", "Medium", or "Low"
  "summary": "..."          // a short 1-2 sentence summary
}

Scenario text:
"{SCENARIO}"
"""

###############################################################################
# 7) HELPER: GENERATE SCENARIO VIA OPENAI
###############################################################################
def generate_scenario(selected_route=None):
    """
    Generates a scenario using OpenAI's ChatCompletion.
    If selected_route is provided (phone, whatsapp, email, web_form), force that route.
    """
    # Build a more diverse prompt by specifying diversity requirements
    diversity_instructions = """
    IMPORTANT: Ensure true randomness and diversity in scenario generation:
    1. Randomize user_type among all four options (don't always use existing_homeowner)
    2. Base the scenario_text on different topics from the FAQ/taxonomy data provided
    3. Don't repeatedly use the Home Health Check report issue
    4. Create a wide variety of realistic customer inquiries that reflect different service needs
    """
    
    if selected_route is None:
        user_content = scenario_generator_prompt_strict + diversity_instructions + "\n\nYou may pick any inbound_route."
    else:
        user_content = scenario_generator_prompt_strict + diversity_instructions + f"\n\nForce inbound_route to '{selected_route}'."

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Replace with a valid model if needed (e.g., "gpt-3.5-turbo")
        messages=[
            {"role": "system", "content": "You generate diverse and random inbound scenarios for Checkatrade using FAQ topics as inspiration."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.8,  # Increased temperature for more diversity
        max_tokens=500
    )
    raw_reply = response["choices"][0]["message"]["content"].strip()
    try:
        scenario_data = json.loads(raw_reply)
        return scenario_data
    except Exception as e:
        return {
            "inbound_route": "error",
            "ivr_flow": "",
            "ivr_selections": [],
            "user_type": "unknown",
            "phone_email": "",
            "membership_id": "",
            "account_details": {
                "name": "",
                "surname": "",
                "location": "",
                "latest_reviews": "",
                "latest_jobs": ""
            },
            "scenario_text": "Error parsing scenario JSON."
        }

###############################################################################
# 8) HELPER: CLASSIFY SCENARIO VIA OPENAI
###############################################################################
def classify_scenario(text):
    prompt = classification_prompt_template.replace("{SCENARIO}", text)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You classify inbound queries for Checkatrade."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=200
    )
    raw_reply = response["choices"][0]["message"]["content"].strip()
    try:
        classification_data = json.loads(raw_reply)
        return classification_data
    except Exception as e:
        return {
            "classification": "General",
            "priority": "Medium",
            "summary": "Could not parse classification JSON."
        }

###############################################################################
# RESPONSE SUGGESTION HELPER FUNCTIONS
###############################################################################
def find_relevant_faq(scenario_text, faq_dataframe):
    """
    Find the most relevant FAQ based on the scenario text.
    Returns the question string if found, or None if no good match
    """
    if faq_dataframe.empty:
        return None
    
    # In a real implementation, this would use semantic search or embedding comparison
    # For demo purposes, we'll use simple keyword matching
    scenario_lower = scenario_text.lower()
    best_match = None
    
    # Common keywords to look for
    keywords = {
        "bill": ["bill", "payment", "invoice", "charge"],
        "account": ["account", "login", "password", "credentials", "sign in"],
        "complaint": ["complaint", "unhappy", "dissatisfied", "poor service"],
        "tradesperson": ["tradesperson", "trade", "contractor", "professional"],
        "membership": ["membership", "subscription", "renewal", "join"],
        "review": ["review", "rating", "feedback", "star"],
        "refund": ["refund", "money back", "cancel"],
        "quote": ["quote", "estimate", "price", "cost"],
        "contact": ["contact", "reach", "phone", "email"]
    }
    
    # Try to find a matching FAQ by category keywords
    for category, terms in keywords.items():
        if any(term in scenario_lower for term in terms):
            matched_rows = faq_dataframe[faq_dataframe["Category"].str.lower() == category.lower()]
            if not matched_rows.empty:
                return matched_rows.iloc[0]["Question"]
    
    # Fallback to keyword matching in questions
    for _, row in faq_dataframe.iterrows():
        question = str(row.get("Question", "")).lower()
        # Check if any significant words from the scenario appear in the question
        if any(word in question for word in scenario_lower.split() if len(word) > 4):
            return row["Question"]
    
    return None

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
    
    # Generate appropriate greeting based on route type and available information
    greeting = ""
    if inbound_route in ["email", "whatsapp"]:
        if name:
            greeting = f"Hi {name.split()[0]},"
        else:
            greeting = "Hi there,"
    
    # Generate response body based on classification
    body = ""
    if "billing" in classification.lower():
        body = "Thank you for contacting Checkatrade about your billing query. We'll look into this for you right away."
    elif "complaint" in classification.lower():
        body = "We're sorry to hear about your experience. Your feedback is important to us, and we'll investigate this matter."
    elif "membership" in classification.lower():
        if "existing" in user_type:
            body = "Thank you for your query about your Checkatrade membership."
        else:
            body = "Thank you for your interest in becoming a Checkatrade member."
    elif "technical" in classification.lower():
        body = "I understand you're experiencing technical difficulties. Let me help resolve this for you."
    else:
        body = "Thank you for contacting Checkatrade. We're happy to help with your inquiry."
    
    # Add scenario-specific details if appropriate
    if "review" in scenario_text.lower():
        body += " Reviews are an important part of the Checkatrade experience."
    elif "payment" in scenario_text.lower() or "project" in scenario_text.lower():
        body += " We'll check your payment details and get back to you shortly."
    
    # Different closing based on channel
    closing = ""
    if inbound_route == "email":
        closing = "\n\nPlease let us know if you need any additional information.\n\nBest regards,\nThe Checkatrade Team"
    elif inbound_route == "whatsapp":
        closing = "\n\nIs there anything else I can help you with today?"
    
    return f"{greeting}\n\n{body}{closing}"

###############################################################################
# 9) STREAMLIT APP UI
###############################################################################
st.title("Checkatrade AI Demo (Enhanced Agent View)")

# -----------------------------------------------------------------------------
# SCENARIO GENERATION
# -----------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    route_mode = st.radio("Route Selection Mode", ["Random", "Specific"])
    if route_mode == "Specific":
        forced_route = st.selectbox("Select inbound route", ["phone", "whatsapp", "email", "web_form"])
    else:
        forced_route = None
        st.write("Inbound route will be chosen by the AI.")

    # Move button below route selection
    if st.button("Generate Scenario", use_container_width=True):
        with st.spinner("Generating scenario..."):
            scenario_data = generate_scenario(forced_route)
            st.session_state["generated_scenario"] = scenario_data
            st.success("Scenario generated!")

with col2:
    # Empty space for visual balance
    st.write("")
    
    # Instead of raw JSON, display a formatted agent view for the generated scenario.
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
            
            ivr_selections = ', '.join(scenario.get("ivr_selections", [])) if scenario.get("ivr_selections") else ""
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
st.header("Classify & Store Inquiry")
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
                    "ivr_selections": ", ".join(st.session_state["generated_scenario"].get("ivr_selections", [])),
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
                
                # Get relevant FAQ if available
                relevant_faq = find_relevant_faq(scenario_text, df_faq)
                if relevant_faq:
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
st.header("Dashboard & Logged Inquiries")
df = st.session_state["inquiries"]
if len(df) > 0:
    # Show Detailed Inquiry Cards first
    st.subheader("Detailed Inquiry Cards")
    for idx, row in df.iterrows():
        with st.expander(f"Inquiry #{idx+1} - {row['classification']} (Priority: {row['priority']})"):
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
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
    
    # Then show summary charts with expanded information
    st.subheader("Summary Analytics")
    
    # Row 1: Classification and Priority distribution
    colA, colB = st.columns(2)
    with colA:
        st.write("**Inquiries by Classification:**")
        classification_counts = df["classification"].value_counts()
        st.bar_chart(classification_counts)
        
        # Show classification breakdown as text too
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        for classification, count in classification_counts.items():
            percentage = (count / len(df)) * 100
            st.markdown(f"<div class='inquiry-label'>{classification}: {count} ({percentage:.1f}%)</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with colB:
        st.write("**Inquiries by Priority:**")
        priority_counts = df["priority"].value_counts()
        st.bar_chart(priority_counts)
        
        # Show priority breakdown as text too
        st.markdown("<div class='info-container'>", unsafe_allow_html=True)
        for priority, count in priority_counts.items():
            percentage = (count / len(df)) * 100
            st.markdown(f"<div class='inquiry-label'>{priority}: {count} ({percentage:.1f}%)</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Row 2: User type and Route distribution 
    colC, colD = st.columns(2)
    with colC:
        st.write("**Inquiries by User Type:**")
        user_type_counts = df["user_type"].value_counts()
        st.bar_chart(user_type_counts)
        
    with colD:
        st.write("**Inquiries by Route:**")
        route_counts = df["inbound_route"].value_counts()
        st.bar_chart(route_counts)
        
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
        
        st.markdown("<div class='info-container tag-container'>", unsafe_allow_html=True)
        for word in common_words:
            if word.lower() in all_summaries.lower():
                # Generate a random count for demo purposes - in real app, count actual occurrences
                count = random.randint(1, len(df))
                if count > 0:
                    opacity = min(0.5 + (count / len(df)), 1.0)
                    st.markdown(f"""
                        <span class="topic-tag" style="opacity: {opacity}">
                            {word.title()} ({count})
                        </span>
                    """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
else:
    st.write("No inquiries logged yet. Generate and classify a scenario.")

# -----------------------------------------------------------------------------
# EXPORT LOGGED DATA
# -----------------------------------------------------------------------------
st.header("Export Logged Data")
if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")
