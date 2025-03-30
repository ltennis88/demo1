import streamlit as st
import openai
import pandas as pd
import json
import time
import random

###############################################################################
# 1) CONFIGURE OPENAI
###############################################################################
# Pull your API key from Streamlit secrets. 
# Make sure your Streamlit Cloud "Secrets" has:
# OPENAI_API_KEY="sk-..." at the top level (no brackets).
openai.api_key = st.secrets["OPENAI_API_KEY"]

###############################################################################
# 2) LOAD FAQ / TAXONOMY DATA
###############################################################################
# We'll assume your CSV is named "faq_taxonomy.csv" in the same folder.
# Adapt the code below if your file/columns differ.

@st.cache_data
def load_faq_csv():
    try:
        df_faq = pd.read_csv("faq_taxonomy.csv")  # e.g., columns might be ["Category", "Question", "Answer"]
    except:
        # If file doesn't exist or columns differ, we handle it gracefully
        df_faq = pd.DataFrame({"Category": [], "Question": [], "Answer": []})
    return df_faq

df_faq = load_faq_csv()

###############################################################################
# 3) SET UP STREAMLIT SESSION STATE
###############################################################################
if "inquiries" not in st.session_state:
    st.session_state["inquiries"] = pd.DataFrame(columns=[
        "timestamp",
        "inbound_route",
        "ivr_flow",
        "ivr_selections",
        "user_type",
        "phone_email",
        "membership_id",
        "scenario_text",
        "classification",
        "priority",
        "summary",
        "account_name",
        "account_location",
        "account_reviews",
        "account_jobs"
    ])

if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

###############################################################################
# 4) BUILD A STRING FROM THE FAQ DATA (TO PASS INTO THE PROMPT)
###############################################################################
# We convert the CSV data into a textual form for context.

def build_faq_context(df):
    if df.empty:
        return "No FAQ data available."
    # You might want to summarize or slice the data if it's large.
    # Example: create a bullet list of category+question+answer.
    lines = []
    for _, row in df.iterrows():
        cat = str(row.get("Category", ""))
        q = str(row.get("Question", ""))
        a = str(row.get("Answer", ""))
        lines.append(f"- Category: {cat}\n  Q: {q}\n  A: {a}")
    return "\n".join(lines)

faq_context = build_faq_context(df_faq)

###############################################################################
# 5) SCENARIO GENERATION PROMPT
###############################################################################
# We incorporate the FAQ context + instructions to produce 
# a scenario with potential account details.

scenario_generator_prompt_strict = f"""
You are a scenario generator for Checkatrade’s inbound contact system.

We have an FAQ/taxonomy data for reference (below). 
You can use it to inspire or shape the scenario's reason/issue.

FAQ Data:
{faq_context}

Produce a single inbound scenario in STRICT JSON FORMAT ONLY (no extra text):
{{
  "inbound_route": "phone | whatsapp | email | web_form",
  "ivr_flow": "...",       // string if phone, else ""
  "ivr_selections": [],    // array of pressed options if phone, else []
  "user_type": "existing_tradesperson | existing_homeowner | prospective_tradesperson | prospective_homeowner",
  "phone_email": "random phone/email if relevant, else empty",
  "membership_id": "T-xxxxx if user_type=existing_tradesperson, else empty",
  "account_details": {{
    "name": "If existing, random name",
    "surname": "If existing, random surname",
    "location": "If existing, location in UK, else empty",
    "latest_reviews": "An array or short text describing latest reviews if existing",
    "latest_jobs": "Short text describing recent jobs if existing"
  }},
  "scenario_text": "Short reason for contacting Checkatrade"
}}

Rules:
1. Return ONLY valid JSON. DO NOT add disclaimers or code fences.
2. If inbound_route='phone', you can specify ivr_flow + ivr_selections. Otherwise keep them "" and [].
3. If user_type starts with 'existing', fill out 'account_details' with random name, surname, location, reviews, etc.
4. If user_type is prospective, 'account_details' can be empty or minimal.
5. scenario_text must reflect a realistic issue or question related to Checkatrade (billing, complaint, membership, searching for tradesperson, etc.).
6. Use or reference the FAQ data for relevant terms or categories, but you don't have to list the entire FAQ. Just keep it realistic.

Remember: We only want the JSON object, no extra commentary.
"""

###############################################################################
# 6) CLASSIFICATION PROMPT
###############################################################################
classification_prompt_template = """
You are an AI classification assistant for Checkatrade.
Given the scenario text below, return a JSON:
{
  "classification": "...",  
  "priority": "...",        
  "summary": "..."
}

Scenario text:
"{SCENARIO}"
"""

###############################################################################
# HELPER: GENERATE SCENARIO
###############################################################################
def generate_scenario(selected_route=None):
    """
    Calls OpenAI ChatCompletion to produce a scenario in JSON.
    If selected_route is None, let the LLM pick any route.
    If selected_route is "phone","whatsapp","email","web_form", we instruct the LLM to use that route.
    """
    # Build user content with or without forced route
    if selected_route is None:
        user_content = scenario_generator_prompt_strict + "\n\nYou may pick any inbound_route."
    else:
        user_content = scenario_generator_prompt_strict + f"\n\nForce inbound_route to '{selected_route}'."

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # your custom model name, or e.g. "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You generate random inbound scenarios for Checkatrade."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.4,  # lower for more compliance
        max_tokens=500
    )
    raw_reply = response["choices"][0]["message"]["content"].strip()

    # Try to parse the JSON
    try:
        scenario_data = json.loads(raw_reply)
        return scenario_data
    except:
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
# HELPER: CLASSIFY SCENARIO
###############################################################################
def classify_scenario(text):
    """
    Classify scenario text using classification_prompt_template.
    Return { "classification": "...", "priority": "...", "summary": "..." }
    """
    prompt = classification_prompt_template.replace("{SCENARIO}", text)

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # custom model name or "gpt-3.5-turbo"
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
    except:
        return {
            "classification": "General",
            "priority": "Medium",
            "summary": "Could not parse classification JSON."
        }

###############################################################################
# STREAMLIT APP
###############################################################################
st.title("Checkatrade AI Demo (With FAQ + Account Details)")

# Show the loaded FAQ (optional)
with st.expander("View Loaded FAQ / Taxonomy Data"):
    if df_faq.empty:
        st.warning("No FAQ data found. Make sure faq_taxonomy.csv is present.")
    else:
        st.dataframe(df_faq, use_container_width=True)

st.write("""
This app:
1. Loads a CSV with FAQ/Taxonomy data for context.
2. Generates inbound scenarios using that data + random account details (if existing).
3. Classifies the scenario.
4. Displays and exports a small dashboard.
""")

# -----------------------------------------------------------------------------
# SECTION 1: SCENARIO GENERATION
# -----------------------------------------------------------------------------
st.header("1. Generate Scenario")

col1, col2 = st.columns(2)

with col1:
    route_choice_mode = st.radio("Route Selection", ["Random", "Specific"])
with col2:
    forced_route = None
    if route_choice_mode == "Specific":
        forced_route = st.selectbox("Select inbound route", ["phone", "whatsapp", "email", "web_form"])
    else:
        st.write("The route will be picked by the AI.")

if st.button("Generate Scenario"):
    with st.spinner("Generating scenario..."):
        scenario_data = generate_scenario(forced_route)
        st.session_state["generated_scenario"] = scenario_data
        st.success("Scenario generated!")

if st.session_state["generated_scenario"]:
    st.subheader("Generated Scenario (Raw JSON)")
    st.json(st.session_state["generated_scenario"])

# -----------------------------------------------------------------------------
# SECTION 2: CLASSIFY & STORE
# -----------------------------------------------------------------------------
st.header("2. Classify & Store Inquiry")
if st.session_state["generated_scenario"]:
    scenario_text = st.session_state["generated_scenario"].get("scenario_text", "")
    account_details = st.session_state["generated_scenario"].get("account_details", {})
    if st.button("Classify Scenario"):
        if scenario_text.strip():
            with st.spinner("Classifying..."):
                result = classify_scenario(scenario_text)
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
                    "classification": result.get("classification", "General"),
                    "priority": result.get("priority", "Medium"),
                    "summary": result.get("summary", ""),
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
            st.warning("No scenario_text found. Generate a scenario first.")
else:
    st.info("No scenario to classify. Generate one above.")

# -----------------------------------------------------------------------------
# SECTION 3: DASHBOARD & DATA
# -----------------------------------------------------------------------------
st.header("3. Dashboard & Data")

df = st.session_state["inquiries"]
if len(df) > 0:
    st.subheader("Current Logged Inquiries")
    st.dataframe(df, use_container_width=True)

    st.subheader("Inquiries by Classification")
    class_counts = df["classification"].value_counts()
    st.bar_chart(class_counts)

    st.subheader("Inquiries by Priority")
    prio_counts = df["priority"].value_counts()
    st.bar_chart(prio_counts)
else:
    st.write("No inquiries stored yet. Please generate + classify a scenario.")

# -----------------------------------------------------------------------------
# SECTION 4: EXPORT
# -----------------------------------------------------------------------------
st.header("4. Export Logged Data")

if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")
