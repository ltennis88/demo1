import streamlit as st
import openai
import pandas as pd
import json
import time
import random
import plotly.express as px
import os
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import re
from collections import Counter

###############################################################################
# Helper Functions
###############################################################################
def render_analytics_dashboard():
    """Render the analytics dashboard with all metrics and visualizations."""
    if "token_usage" not in st.session_state or not st.session_state["token_usage"]["generations"]:
        st.info("No analytics data available yet. Generate some responses to see analytics.")
        return

    st.header("Analytics Dashboard")
    
    # Get token data
    token_data = st.session_state["token_usage"]
    generations = token_data["generations"]
    num_generations = len(generations)
    
    # Calculate totals
    total_cost = sum(gen.get("total_cost", 0) for gen in generations)
    total_input_tokens = sum(gen.get("input_tokens", 0) for gen in generations)
    total_output_tokens = sum(gen.get("output_tokens", 0) for gen in generations)
    
    # Calculate averages
    avg_cost = total_cost / num_generations if num_generations > 0 else 0
    avg_input_tokens = total_input_tokens / num_generations if num_generations > 0 else 0
    avg_output_tokens = total_output_tokens / num_generations if num_generations > 0 else 0
    
    # Display totals
    st.subheader("LLM Metrics")
    st.write("##### Total Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col2:
        st.metric("Total Input Tokens", f"{total_input_tokens:,}")
    with col3:
        st.metric("Total Output Tokens", f"{total_output_tokens:,}")
    
    # Display averages
    st.write("##### Average Metrics (per response)")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Avg Cost", f"${avg_cost:.4f}")
    with col5:
        st.metric("Avg Input Tokens", f"{int(avg_input_tokens):,}")
    with col6:
        st.metric("Avg Output Tokens", f"{int(avg_output_tokens):,}")
    
    # Display response time metrics if available
    response_times = [gen.get("response_time", 0) for gen in generations]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        st.write("##### Response Time Metrics")
        col7, col8, col9 = st.columns(3)
        with col7:
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
        with col8:
            st.metric("Max Response Time", f"{max_response_time:.2f}s")
        with col9:
            st.metric("Min Response Time", f"{min_response_time:.2f}s")

    # Display classification and priority distributions
    if "inquiries" in st.session_state and not st.session_state["inquiries"].empty:
        df = st.session_state["inquiries"]
        
        st.subheader("Classification Metrics")
        # Create two columns for the pie charts
        pie_col1, pie_col2 = st.columns(2)
        
        with pie_col1:
            # Classification distribution with pie chart
            st.write("##### Classification Distribution")
            if "classification" in df.columns and not df["classification"].isna().all():
                classification_counts = df["classification"].value_counts()
                fig_class = px.pie(
                    values=classification_counts.values,
                    names=classification_counts.index
                )
                fig_class.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_class, use_container_width=True)

        with pie_col2:
            # User Type distribution with pie chart
            st.write("##### User Type Distribution")
            if "user_type" in df.columns and not df["user_type"].isna().all():
                user_type_counts = df["user_type"].value_counts()
                fig_user = px.pie(
                    values=user_type_counts.values,
                    names=user_type_counts.index,
                    color_discrete_map={
                        "existing_homeowner": "#4CAF50",      # Green
                        "existing_tradesperson": "#2196F3",   # Blue
                        "prospective_homeowner": "#FFA726",   # Orange
                        "prospective_tradesperson": "#9C27B0"  # Purple
                    }
                )
                fig_user.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_user, use_container_width=True)

        # Create another row with two columns for contact method and department
        pie_col3, pie_col4 = st.columns(2)
        
        with pie_col3:
            # Contact Method (inbound_route) distribution with pie chart
            st.write("##### Contact Method Distribution")
            if "inbound_route" in df.columns and not df["inbound_route"].isna().all():
                route_counts = df["inbound_route"].value_counts()
                fig_route = px.pie(
                    values=route_counts.values,
                    names=route_counts.index,
                    color_discrete_map={
                        "phone": "#FF4B4B",     # Red
                        "email": "#4CAF50",     # Green
                        "whatsapp": "#2196F3",  # Blue
                        "web_form": "#FFA726"   # Orange
                    }
                )
                fig_route.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_route, use_container_width=True)

        with pie_col4:
            # Department distribution with pie chart
            st.write("##### Department Distribution")
            if "department" in df.columns and not df["department"].isna().all():
                department_counts = df["department"].value_counts()
                fig_dept = px.pie(
                    values=department_counts.values,
                    names=department_counts.index
                )
                fig_dept.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_dept, use_container_width=True)

        # Common topics analysis with bubble tags
        st.write("##### Common Topics & Themes")
        if "summary" in df.columns and not df["summary"].isna().all():
            summaries = " ".join(df["summary"].fillna("")).lower()
            words = re.findall(r'\b\w+\b', summaries)
            word_counts = Counter(words)
            
            # Filter out common stop words and short words
            stop_words = set(['and', 'the', 'to', 'of', 'in', 'for', 'a', 'with', 'is', 'are', 'was', 'were'])
            themes = [(word, count) for word, count in word_counts.most_common(10) 
                     if word not in stop_words and len(word) > 3]
            
            if themes:
                # Create bubble tags HTML with updated styling
                st.markdown("""
                <style>
                .bubble-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    margin-top: 10px;
                }
                .bubble-tag {
                    background-color: #2979FF;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    width: fit-content;
                }
                .bubble-count {
                    background-color: rgba(255, 255, 255, 0.2);
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 12px;
                    white-space: nowrap;
                }
                </style>
                <div class="bubble-container">
                """, unsafe_allow_html=True)
                
                # Generate bubble tags
                bubble_tags = []
                for word, count in themes:
                    bubble_tags.append(f"""
                    <div class="bubble-tag">
                        {word.title()}
                        <span class="bubble-count">{count}</span>
                    </div>
                    """)
                
                st.markdown("".join(bubble_tags) + "</div>", unsafe_allow_html=True)
            else:
                st.text("No common themes found yet")
        else:
            st.text("No summary data available for theme analysis")

def update_analytics(section="main"):
    """Update analytics display."""
    render_analytics_dashboard()

###############################################################################
# 1) EARLY INITIALIZATION - To prevent SessionInfo errors
###############################################################################
# Initialize all session state variables at the very beginning
if "page" not in st.session_state:
    st.session_state["page"] = "main"

if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = None

if "current_case_id" not in st.session_state:
    st.session_state["current_case_id"] = None

# Initialize inquiries early to avoid issues
if "inquiries" not in st.session_state:
    # Create a placeholder until we can properly load in the full initialization section
    st.session_state["inquiries"] = pd.DataFrame(columns=[
        "timestamp", "inbound_route", "ivr_flow", "ivr_selections", "user_type",
        "phone_email", "membership_id", "scenario_text", "classification",
        "department", "subdepartment", "priority", "summary", "related_faq_category", "account_name", 
        "account_location", "account_reviews", "account_jobs", "project_cost", 
        "payment_status", "estimated_response_time", "agent_notes", "case_status"
    ])

# Initialize generated_scenario variable to avoid SessionInfo errors
if "generated_scenario" not in st.session_state:
    st.session_state["generated_scenario"] = {
        "inbound_route": "",
        "scenario_text": "",
        "user_type": "",
        "account_details": {
            "name": "",
            "location": "",
            "latest_reviews": "",
            "latest_jobs": "",
            "project_cost": "",
            "payment_status": ""
        }
    }

# Initialize classification variable to avoid SessionInfo errors
if "classification_result" not in st.session_state:
    st.session_state["classification_result"] = {
        "classification": "",
        "department": "",
        "subdepartment": "",
        "priority": "",
        "summary": "",
        "related_faq_category": "",
        "estimated_response_time": ""
    }

# Initialize other session state variables used throughout the app
for key in ["current_case_id", "page", "classified", "token_usage", "csv_loaded", "inquiries_loaded"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Set default values for specific variables
if st.session_state["token_usage"] is None:
    st.session_state["token_usage"] = {
        "generations": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0,
        "response_times": []
    }

if st.session_state["page"] is None:
    st.session_state["page"] = "generate"

if st.session_state["classified"] is None:
    st.session_state["classified"] = False

if st.session_state["csv_loaded"] is None:
    st.session_state["csv_loaded"] = False

if st.session_state["inquiries_loaded"] is None:
    st.session_state["inquiries_loaded"] = False

# Define token cost constants
TOKEN_COSTS = {
    "input": 0.15,      # $0.15 per 1M tokens
    "cached_input": 0.075,  # $0.075 per 1M tokens
    "output": 0.60      # $0.60 per 1M tokens
}

# Initialize cached values
if "cached_response_prompt" not in st.session_state:
    st.session_state["cached_response_prompt"] = ""
    
if "cached_response_prompt_tokens" not in st.session_state:
    st.session_state["cached_response_prompt_tokens"] = 0

###############################################################################
# 2) PAGE CONFIGURATION & OPENAI SETUP
###############################################################################
# Use simplified page config without custom theme
st.set_page_config(
    layout="wide", 
    page_title="Contact Center AI Assistant",
    initial_sidebar_state="collapsed"
)

# Setup API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Add global CSS for better UI
st.markdown("""
<style>
/* Basic theme overrides */
.stApp {
    background-color: #121212;
}

.main .block-container {
    padding: 2rem;
    max-width: 95%;
}

/* Common styles */
.info-container {
    background-color: #1E1E1E;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #424242;
}

.inquiry-label {
    font-weight: bold;
    color: #64B5F6;
    margin-bottom: 5px;
}

.inquiry-detail {
    background-color: #2C2C2C;
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 12px;
}

/* Priority colors */
.priority-high { color: #F44336; font-weight: bold; }
.priority-medium { color: #FFA726; font-weight: bold; }
.priority-low { color: #4CAF50; font-weight: bold; }

/* Center the main app container */
.main {
    align-items: center !important;
    display: flex !important;
    justify-content: center !important;
}

/* Fix main content layout */
.main .block-container {
    max-width: 1200px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Reduce sidebar width */
[data-testid="stSidebar"] {
    width: 12rem !important;
    min-width: 12rem !important;
    max-width: 12rem !important;
    background-color: #1E1E1E !important;
    border-right: 1px solid #424242 !important;
}

[data-testid="stSidebar"] > div:first-child {
    width: 12rem !important;
    min-width: 12rem !important;
    max-width: 12rem !important;
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

/* Utility classes for cards and containers */
.info-container {
    background-color: #2C2C2C;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #424242;
}
.inquiry-label {
    font-weight: bold;
    color: #64B5F6;
    margin-bottom: 5px;
}
.inquiry-detail {
    background-color: #1E1E1E;
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 12px;
}
.inquiry-section {
    font-weight: bold;
    font-size: 16px;
    margin-top: 15px;
    margin-bottom: 10px;
    color: #90CAF9;
    border-bottom: 1px solid #424242;
    padding-bottom: 5px;
}
.priority-high {
    color: #F44336;
    font-weight: bold;
}
.priority-medium {
    color: #FFA726;
    font-weight: bold;
}
.priority-low {
    color: #4CAF50;
    font-weight: bold;
}
/* Style for classification styling */
.classification-card {
    background-color: #2C2C2C;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #424242;
}
.classification-header {
    font-weight: bold;
    font-size: 14px;
    color: #90CAF9;
    margin-bottom: 10px;
    border-bottom: 1px solid #424242;
    padding-bottom: 5px;
}
.field-label {
    font-weight: bold;
    color: #64B5F6;
    margin-bottom: 5px;
}
.field-value {
    background-color: #1E1E1E;
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 12px;
    font-family: monospace;
    white-space: pre-wrap;
    font-size: 13px;
}

/* Override entire layout structure */
.css-18e3th9 {
    padding-top: 1rem;
    padding-bottom: 10rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Force main content to take full width */
.css-1d391kg {
    width: 100% !important;
    padding-left: 0 !important;
}

/* Reset flex layout from Streamlit */
.css-1y4p8pa {
    margin-left: 0 !important;
    max-width: 100% !important;
}

/* Fix main content layout */
.main .block-container {
    max-width: 95% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    margin-left: 0 !important;
}

/* Push content leftwards and increase width */
section[data-testid="stSidebar"] ~ .css-1d391kg {
    width: 100% !important;
    margin-left: 0 !important;
    padding-left: 1rem !important;
}

/* Container styling for better use of space */
.stApp > div:not([data-testid="stSidebar"]) {
    margin-left: 0 !important;
}

/* Override Streamlit's default column spacing */
.row-widget.stRadio > div {
    flex-direction: column;
}
</style>
""", unsafe_allow_html=True)

# Add a clear title for the main page
st.title("Contact Center AI Assistant")

# Create horizontal navigation with buttons
col1, col2, col3 = st.columns(3)
with col1:
    main_btn = st.button("🏠 Main Dashboard", use_container_width=True, 
                      type="primary" if st.session_state.get("section", "main") == "main" else "secondary")
with col2:
    inquiries_btn = st.button("📋 View Inquiries", use_container_width=True,
                          type="primary" if st.session_state.get("section", "main") == "inquiries" else "secondary")
with col3:
    analytics_btn = st.button("📊 Analytics Dashboard", use_container_width=True,
                          type="primary" if st.session_state.get("section", "main") == "analytics" else "secondary")

# Handle navigation using section state
if "section" not in st.session_state:
    st.session_state["section"] = "main"

if main_btn:
    st.session_state["section"] = "main"
if inquiries_btn:
    st.session_state["section"] = "inquiries" 
if analytics_btn:
    st.session_state["section"] = "analytics"

# Setup API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Main page content based on current page
if st.session_state["section"] == "main":
    st.header("Generate New Inquiry")
elif st.session_state["section"] == "inquiries":
    st.header("View Inquiries")
    # Display inquiries directly in main app
    df = st.session_state["inquiries"]
    if len(df) > 0:
        # Sort inquiries by timestamp in descending order (most recent first)
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
        except:
            # If timestamp conversion fails, just use the existing order
            pass
        
        # Display all inquiries in a collapsible container
        for idx, row in df.iterrows():
            # Use a header for each inquiry instead of a nested expander
            with st.expander(f"Inquiry #{idx+1} - {row['classification']} (Priority: {row['priority']})"):
                st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['timestamp']}</div>", unsafe_allow_html=True)
                    
                    if 'inbound_route' in row and row['inbound_route']:
                        st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['inbound_route']}</div>", unsafe_allow_html=True)
                    
                    if 'ivr_flow' in row and row['ivr_flow']:
                        st.markdown("<div class='inquiry-label'>IVR Flow:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['ivr_flow']}</div>", unsafe_allow_html=True)
                    
                    if 'ivr_selections' in row and row['ivr_selections']:
                        st.markdown("<div class='inquiry-label'>IVR Selections:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['ivr_selections']}</div>", unsafe_allow_html=True)
                
                with col2:
                    if 'user_type' in row and row['user_type']:
                        st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['user_type']}</div>", unsafe_allow_html=True)
                    
                    if 'phone_email' in row and row['phone_email']:
                        st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['phone_email']}</div>", unsafe_allow_html=True)
                    
                    if 'membership_id' in row and row['membership_id']:
                        st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['membership_id']}</div>", unsafe_allow_html=True)
                
                # Classification summary section only
                st.markdown("<div class='inquiry-section'>Classification Summary</div>", unsafe_allow_html=True)
                
                if 'classification' in row and row['classification']:
                    st.markdown("<div class='inquiry-label'>Classification:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['classification']}</div>", unsafe_allow_html=True)
                
                if 'priority' in row and row['priority']:
                    st.markdown("<div class='inquiry-label'>Priority:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['priority']}</div>", unsafe_allow_html=True)
                
                if 'summary' in row and row['summary']:
                    st.markdown("<div class='inquiry-label'>Summary:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['summary']}</div>", unsafe_allow_html=True)
                
                # Show scenario text
                if 'scenario_text' in row and row['scenario_text']:
                    st.markdown("<div class='inquiry-section'>Scenario Details</div>", unsafe_allow_html=True)
                    st.markdown("<div class='inquiry-label'>Scenario Text:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{row['scenario_text']}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
    else:
        st.info("No inquiries found. Generate a scenario and classify it to create inquiries.")

    # Data Export section
    st.header("Data Export")
    if "inquiries" in st.session_state and len(st.session_state["inquiries"]) > 0:
        df = st.session_state["inquiries"]
        json_data = df.to_json(orient="records")
        st.download_button(
            "Download JSON",
            data=json_data,
            file_name="inquiries.json",
            mime="application/json"
        )
    else:
        st.info("No data to export yet.")

elif st.session_state["section"] == "analytics":
# -----------------------------------------------------------------------------
# EXPORT LOGGED DATA
# -----------------------------------------------------------------------------
# This section is removed as it's now part of the analytics expander

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def extract_key_topics(scenario_text):
    """Extract key topics from the scenario using OpenAI."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a customer service assistant. Extract the key topics from this scenario."},
                {"role": "user", "content": scenario_text}
            ],
            temperature=0,
            max_tokens=150
        )
        
        # Extract key topics from the response
        key_topics = response.choices[0].message.content
        
        # Cache the key topics for this scenario
        if 'faq_key_topics' not in st.session_state:
            st.session_state['faq_key_topics'] = {}
        st.session_state['faq_key_topics'][str(scenario_text)] = key_topics
        
        return key_topics
    except Exception as e:
        st.error(f"Error extracting key topics: {str(e)}")
        return None

def process_relevant_faq(scenario_text, faq_dataframe, context):
    """Process and find relevant FAQ entries."""
    try:
        relevant_faq, faq_answer, faq_relevance = find_relevant_faq(scenario_text, faq_dataframe)
        if relevant_faq and faq_answer and faq_relevance >= 7:
            return context + f"""
Relevant FAQ:
Question: {relevant_faq}
Answer: {faq_answer}
"""
        return context
    except Exception as e:
        st.error(f"Error finding relevant FAQ: {str(e)}")
        return context
