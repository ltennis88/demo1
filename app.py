import streamlit as st
import openai
import pandas as pd
import json
import time
import random

###############################################################################
# 1) CONFIGURE OPENAI
###############################################################################
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Must be in your Streamlit secrets

###############################################################################
# 2) SET UP STREAMLIT SESSION STATE
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
        "summary"
    ])

if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

###############################################################################
# 3) SCENARIO GENERATION PROMPTS
###############################################################################
scenario_generator_prompt_strict = """
You are a scenario generator for Checkatrade’s inbound contact system.
Produce a single inbound scenario in STRICT JSON FORMAT ONLY (no extra text),
with these keys exactly:
- "inbound_route" (one of: phone, whatsapp, email, web_form)
- "ivr_flow" (string, often "" if not phone)
- "ivr_selections" (array of pressed options, or [])
- "user_type" ("existing_tradesperson", "existing_homeowner", 
   "prospective_tradesperson", or "prospective_homeowner")
- "phone_email" (random phone # or email if relevant, or empty)
- "membership_id" ("T-12345" if existing_tradesperson, else "")
- "scenario_text" (short reason for contacting Checkatrade)

Rules:
1. Return ONLY valid JSON. DO NOT include disclaimers or code fences.
2. If inbound_route = "phone", you can populate ivr_flow & ivr_selections. 
   Otherwise leave them "" / [].
3. user_type picks if membership_id is used (existing_tradesperson).
4. scenario_text is a short snippet (billing, complaint, membership renewal, etc.).
5. No additional text outside the JSON.
"""

classification_prompt_template = """
You are an AI classification assistant for Checkatrade.
Given the scenario text below, return a JSON object with:
{
  "classification": "...",  // e.g. "Billing", "Membership", "Tech Support", "Complaints", "General", etc.
  "priority": "...",        // "High", "Medium", "Low"
  "summary": "..."          // a short 1-2 sentence summary
}

Scenario text:
"{SCENARIO}"
"""

###############################################################################
# Helper function: generate a scenario
###############################################################################
def generate_scenario(selected_route=None):
    """
    Calls OpenAI ChatCompletion to produce a scenario in JSON.
    If selected_route is None, we let the LLM pick any route. 
    If selected_route is 'phone','whatsapp','email','web_form', we instruct the LLM to use that route.
    """
    # Build user content with or without a forced route
    if selected_route is None:
        user_content = scenario_generator_prompt_strict + "\n\nYou may pick any route (phone, whatsapp, email, web_form)."
    else:
        user_content = scenario_generator_prompt_strict + f"\n\nForce inbound_route to be '{selected_route}'."

    # Call the ChatCompletion endpoint:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # <--- custom model name as requested
        messages=[
            {"role": "system", "content": "You generate random inbound scenarios."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.3,
        max_tokens=300
    )

    raw_reply = response["choices"][0]["message"]["content"].strip()

    # Attempt to parse
    try:
        scenario_data = json.loads(raw_reply)
        return scenario_data
    except:
        # If parse fails, return an "error" scenario
        return {
            "inbound_route": "error",
            "ivr_flow": "",
            "ivr_selections": [],
            "user_type": "unknown",
            "phone_email": "",
            "membership_id": "",
            "scenario_text": "Error parsing scenario JSON."
        }

###############################################################################
# Helper function: classify scenario
###############################################################################
def classify_scenario(text):
    """
    Classify scenario text using classification_prompt_template.
    Return a dict: { "classification": "...", "priority": "...", "summary": "..." }
    """
    prompt = classification_prompt_template.replace("{SCENARIO}", text)

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # same custom model name
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
st.title("Checkatrade AI Demo (IVR + GPT-4o-mini)")
st.write("""
Generate inbound scenarios (phone, WhatsApp, email, web form), 
classify them, and view a live dashboard. 
Uses a custom model "gpt-4o-mini" (make sure this model exists in your account).
""")

# -----------------------------------------------------------------------------
# SECTION 1: SCENARIO SELECTION
# -----------------------------------------------------------------------------
st.header("1. Scenario Generation")

col1, col2 = st.columns(2)

with col1:
    # Choose "Random" or "Specific" route
    random_or_specific = st.radio("Pick inbound route method", ["Random", "Specific"])
with col2:
    route_choice = None
    if random_or_specific == "Specific":
        route_choice = st.selectbox("Select inbound route", ["phone", "whatsapp", "email", "web_form"])
    else:
        st.write("Route will be chosen by the AI (Random).")

# Button to generate scenario
if st.button("Generate Scenario"):
    with st.spinner("Generating scenario..."):
        if random_or_specific == "Random":
            scenario_data = generate_scenario(None)
        else:
            scenario_data = generate_scenario(route_choice)

        st.session_state["generated_scenario"] = scenario_data
        st.success("Scenario generated!")

if st.session_state["generated_scenario"]:
    st.subheader("Generated Scenario (Raw JSON)")
    st.json(st.session_state["generated_scenario"])

# -----------------------------------------------------------------------------
# SECTION 2: Classify & Store
# -----------------------------------------------------------------------------
st.header("2. Classify This Scenario")
if st.session_state["generated_scenario"]:
    scenario_text = st.session_state["generated_scenario"].get("scenario_text", "")
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
                    "summary": result.get("summary", "")
                }

                # Append to session DataFrame
                st.session_state["inquiries"] = pd.concat(
                    [st.session_state["inquiries"], pd.DataFrame([new_row])],
                    ignore_index=True
                )

                st.success(f"Classified as {new_row['classification']} (Priority: {new_row['priority']}).")
        else:
            st.warning("No scenario text found. Generate a scenario first.")
else:
    st.info("Generate a scenario above.")

# -----------------------------------------------------------------------------
# SECTION 3: Dashboard & Data
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
    st.write("No inquiries yet. Please generate and classify a scenario.")

# -----------------------------------------------------------------------------
# SECTION 4: Export Logged Data
# -----------------------------------------------------------------------------
st.header("4. Export Data")

if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")
