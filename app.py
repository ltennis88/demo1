import streamlit as st
import openai
import pandas as pd
import json
import time
import random

###############################################################################
# 1) PAGE CONFIGURATION & OPENAI SETUP
###############################################################################
st.set_page_config(layout="wide", page_title="Checkatrade AI Demo")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Add global CSS for better UI
st.markdown("""
<style>
/* Common styles for detail items */
.agent-detail, .inquiry-detail {
    margin-bottom: 12px;
    padding: 8px 12px;
    background-color: #f8f9fa;
    border-radius: 5px;
}

/* Common styles for labels */
.agent-label, .inquiry-label {
    font-weight: bold;
    margin-bottom: 4px;
    color: #333;
}

/* Common styles for section headers */
.agent-section, .inquiry-section {
    margin-top: 20px;
    margin-bottom: 12px;
    font-size: 18px;
    font-weight: bold;
    padding-bottom: 5px;
    border-bottom: 1px solid #ddd;
    color: #1E88E5;
}

/* Additional container styling */
.info-container {
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
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
        "account_reviews", "account_jobs"
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
    - "latest_reviews": short text describing recent reviews if existing; otherwise empty.
    - "latest_jobs": short text describing recent jobs if existing; otherwise empty.
- "scenario_text": a short, realistic reason for contacting Checkatrade (for example, a billing issue, a complaint, membership renewal, or looking for a tradesperson).

Rules:
1. Return ONLY valid JSON with no extra commentary or code fences.
2. If inbound_route is "phone", include realistic ivr_flow and ivr_selections.
3. For "existing" user types, fill out account_details with plausible data.
4. The scenario_text must be specific to Checkatrade.
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
    if selected_route is None:
        user_content = scenario_generator_prompt_strict + "\n\nYou may pick any inbound_route."
    else:
        user_content = scenario_generator_prompt_strict + f"\n\nForce inbound_route to '{selected_route}'."

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Replace with a valid model if needed (e.g., "gpt-3.5-turbo")
        messages=[
            {"role": "system", "content": "You generate random inbound scenarios for Checkatrade."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.4,
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
# 9) STREAMLIT APP UI
###############################################################################
st.title("Checkatrade AI Demo (Enhanced Agent View)")

# -----------------------------------------------------------------------------
# SECTION 1: SCENARIO GENERATION
# -----------------------------------------------------------------------------
st.header("1. Generate Scenario")

col1, col2 = st.columns(2)
with col1:
    route_mode = st.radio("Route Selection Mode", ["Random", "Specific"])
with col2:
    forced_route = None
    if route_mode == "Specific":
        forced_route = st.selectbox("Select inbound route", ["phone", "whatsapp", "email", "web_form"])
    else:
        st.write("Inbound route will be chosen by the AI.")

if st.button("Generate Scenario"):
    with st.spinner("Generating scenario..."):
        scenario_data = generate_scenario(forced_route)
        st.session_state["generated_scenario"] = scenario_data
        st.success("Scenario generated!")

# Instead of raw JSON, display a formatted agent view for the generated scenario.
if st.session_state["generated_scenario"]:
    scenario = st.session_state["generated_scenario"]
    st.subheader("Scenario Details (Agent View)")
    
    # Use the info-container class for better styling
    st.markdown("<div class='info-container'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    with col2:
        if scenario.get('phone_email'):
            st.markdown("<div class='agent-label'>Phone/Email:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('phone_email', 'N/A')}</div>", unsafe_allow_html=True)
        
        if scenario.get('membership_id'):
            st.markdown("<div class='agent-label'>Membership ID:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{scenario.get('membership_id', 'N/A')}</div>", unsafe_allow_html=True)

    # Account details in a separate section
    account_details = scenario.get("account_details", {})
    name = f"{account_details.get('name', '')} {account_details.get('surname', '')}".strip()
    
    if name or account_details.get('location') or account_details.get('latest_reviews') or account_details.get('latest_jobs'):
        st.markdown("<div class='agent-section'>Account Details</div>", unsafe_allow_html=True)
    
        if name:
            st.markdown("<div class='agent-label'>Name:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{name}</div>", unsafe_allow_html=True)
        
        if account_details.get('location'):
            st.markdown("<div class='agent-label'>Location:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('location')}</div>", unsafe_allow_html=True)
        
        if account_details.get('latest_reviews'):
            st.markdown("<div class='agent-label'>Latest Reviews:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('latest_reviews')}</div>", unsafe_allow_html=True)
        
        if account_details.get('latest_jobs'):
            st.markdown("<div class='agent-label'>Latest Jobs:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='agent-detail'>{account_details.get('latest_jobs')}</div>", unsafe_allow_html=True)
    
    # Reason for contact in a separate section
    if scenario.get('scenario_text'):
        st.markdown("<div class='agent-section'>Reason for Contact</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='agent-detail'>{scenario.get('scenario_text')}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div

# -----------------------------------------------------------------------------
# SECTION 2: CLASSIFY & STORE INQUIRY
# -----------------------------------------------------------------------------
st.header("2. Classify & Store Inquiry")
if st.session_state["generated_scenario"]:
    scenario_text = st.session_state["generated_scenario"].get("scenario_text", "")
    account_details = st.session_state["generated_scenario"].get("account_details", {})
    if st.button("Classify Scenario"):
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
                    "account_jobs": account_details.get("latest_jobs", "")
                }

                st.session_state["inquiries"] = pd.concat(
                    [st.session_state["inquiries"], pd.DataFrame([new_row])],
                    ignore_index=True
                )
                st.success(f"Scenario classified as {new_row['classification']} (Priority: {new_row['priority']}).")
        else:
            st.warning("No scenario text found. Generate a scenario first.")
else:
    st.info("Generate a scenario above before classification.")

# -----------------------------------------------------------------------------
# SECTION 3: DASHBOARD & LOGGED INQUIRIES (Enhanced View)
# -----------------------------------------------------------------------------
st.header("3. Dashboard & Logged Inquiries")
df = st.session_state["inquiries"]
if len(df) > 0:
    st.subheader("Summary Charts")
    colA, colB = st.columns(2)
    with colA:
        st.write("**Inquiries by Classification:**")
        st.bar_chart(df["classification"].value_counts())
    with colB:
        st.write("**Inquiries by Priority:**")
        st.bar_chart(df["priority"].value_counts())
    
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
else:
    st.write("No inquiries logged yet. Generate and classify a scenario.")

# -----------------------------------------------------------------------------
# SECTION 4: EXPORT LOGGED DATA
# -----------------------------------------------------------------------------
st.header("4. Export Logged Data")
if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")
