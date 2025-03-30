import streamlit as st
import openai
import pandas as pd
import json
import time
import random

###############################################################################
# 1) CONFIGURE OPENAI
###############################################################################
# Hard-coded key for private demo (NOT recommended in production or public repos).
openai.api_key = "YOUR_OPENAI_API_KEY_HERE"

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

# We'll store the generated scenario in session state so we can classify it
if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

###############################################################################
# 3) SCENARIO GENERATION PROMPTS
###############################################################################
# This prompt handles both random route OR user-specified route logic (phone, whatsapp, email, web_form).
# If route is phone, it picks one of two IVR flows (Flow A or Flow B), random IVR selections, final spoken_text, etc.
scenario_generator_prompt_base = """
You are a scenario generator for Checkatrade’s inbound contact system.
Produce a single inbound scenario in JSON format with the following structure:

{
  "inbound_route": "...",
  "ivr_flow": "...",           
  "ivr_selections": [],
  "user_type": "...",
  "phone_email": "...",
  "membership_id": "...",
  "scenario_text": "..."
}

Rules & Logic:
1. inbound_route can be one of: phone, whatsapp, email, web_form.
2. If inbound_route = "phone":
   - Randomly pick between two IVR flows (Flow A or Flow B).
   - Flow A:
       1. "Tradesperson" or "Homeowner"
       2. If tradesperson: [join (1), renewal (2), negative review (3), more business (4), other inquiries (5)]
       3. If homeowner: [reputable tradesperson(1), complaint(2), payment(3), general(4), if tradesperson press 5]
   - Flow B is the second set you have for phone:
       "Thank you for calling Checker Trade... etc."
       Similar structure: tradesperson vs homeowner, sub-options, etc.
   - "ivr_selections": an array of the pressed options or text labels. 
   - Then generate a final spoken_text that might confirm or override the selected IVR path.
   - "membership_id" only if user_type is "existing_tradesperson", else empty.
3. If inbound_route = "whatsapp" or "email" or "web_form", no IVR flow needed, so ivr_flow = "", ivr_selections = [].
4. user_type can be: existing_tradesperson, existing_homeowner, prospective_tradesperson, prospective_homeowner.
5. If user_type is existing_tradesperson, produce membership_id like "T-12345". 
   Otherwise, membership_id = "".
6. phone_email:
   - If inbound_route = phone or whatsapp, produce a random phone number e.g. +44 7700 XXXYYY
   - If inbound_route = email, produce a random email e.g. "someone@example.com"
   - If inbound_route = web_form, can be an email or empty.
7. scenario_text: mention a typical reason (billing, negative review, membership renewal, complaint, etc.).
8. Return valid JSON ONLY (no extra commentary).
"""

# Classification prompt
classification_prompt_template = """
You are an AI classification assistant for Checkatrade. 
Given the scenario text below, return a JSON object with:
{
  "classification": "...",  // e.g. "Billing", "Membership", "Tech Support", "Complaints", "General", etc.
  "priority": "...",        // "High", "Medium", or "Low"
  "summary": "..."          // a short 1-2 sentence summary
}

Scenario text:
"{SCENARIO}"
"""

###############################################################################
# Helper function to talk to OpenAI for scenario generation
###############################################################################
def generate_scenario(selected_route=None):
    """
    Calls the OpenAI Chat API to produce a scenario in JSON.
    If selected_route is None, let the model pick any route.
    If selected_route is 'phone', 'whatsapp', etc., we instruct the model to use that route.
    """
    # Build a user prompt that includes or excludes the route constraint
    if selected_route is None:
        user_content = scenario_generator_prompt_base + "\n\nGenerate any route (phone, whatsapp, email, or web_form)."
    else:
        user_content = scenario_generator_prompt_base + f"\n\nForce the inbound_route to be '{selected_route}'."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You generate random inbound scenarios for Checkatrade."},
            {"role": "user", "content": user_content}
        ],
        temperature=0.9,
        max_tokens=400
    )
    raw_reply = response["choices"][0]["message"]["content"].strip()
    
    # Attempt to parse
    try:
        scenario_data = json.loads(raw_reply)
        return scenario_data
    except:
        # If JSON parse fails, return an error scenario
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
# Helper function to classify scenario
###############################################################################
def classify_scenario(text):
    """
    Classify scenario text using the classification_prompt_template
    Return a dict with classification, priority, summary
    """
    prompt = classification_prompt_template.replace("{SCENARIO}", text)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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
st.title("Checkatrade AI Demo with IVR Logic for Phone Calls")
st.write("""
A simple Streamlit app to (1) generate random or route-specific inbound scenarios, 
(2) incorporate IVR flows if phone, (3) classify them with OpenAI, and (4) display a dashboard.
""")

# ---------------------------
# SECTION 1: SCENARIO SELECTION
# ---------------------------
st.header("1. Scenario Generation")

col1, col2 = st.columns(2)

with col1:
    # Let user choose: "Random route" or a specific route
    random_or_specific = st.radio("How do you want to pick the inbound route?", 
                                  ["Random", "Specific"])
with col2:
    # If user picks "Specific," let them choose which one
    route_choice = None
    if random_or_specific == "Specific":
        route_choice = st.selectbox("Select inbound route", ["phone", "whatsapp", "email", "web_form"])
    else:
        st.write("Route will be randomly chosen by the AI.")

if st.button("Generate Scenario"):
    with st.spinner("Generating scenario..."):
        if random_or_specific == "Random":
            scenario_data = generate_scenario(None)  # Let the AI pick any route
        else:
            scenario_data = generate_scenario(route_choice)  # Force the chosen route

        st.session_state["generated_scenario"] = scenario_data
        st.success("Scenario generated successfully!")

# Display scenario
if st.session_state["generated_scenario"]:
    st.subheader("Generated Scenario (Raw JSON)")
    st.json(st.session_state["generated_scenario"])


# ---------------------------
# SECTION 2: Classify & Store
# ---------------------------
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
            st.warning("No scenario text to classify. Please generate a scenario first.")
else:
    st.info("Generate a scenario above first.")

# ---------------------------
# SECTION 3: Dashboard & Data
# ---------------------------
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


# ---------------------------
# SECTION 4: Export Logged Data
# ---------------------------
st.header("4. Export Data")
if len(df) > 0:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

    json_data = df.to_json(orient="records")
    st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
else:
    st.write("No data to export yet.")
