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
elif st.session_state["section"] == "analytics":
    render_analytics_dashboard()
else:
    st.info("Generate a scenario above before classification.")

###############################################################################
# 3) LOAD FAQ / TAXONOMY DATA
###############################################################################
@st.cache_data
def load_faq_csv():
    """
    Loads the CSV file with FAQ/taxonomy data and converts it to an optimized dictionary structure.
    Returns both the DataFrame (for backward compatibility) and the optimized dictionary.
    """
    try:
        # First try with semicolon delimiter
        try:
            df = pd.read_csv("faq_taxonomy.csv", sep=';', encoding='utf-8')
        except:
            # If that fails, try with comma
            df = pd.read_csv("faq_taxonomy.csv", sep=',', encoding='utf-8')
            
        # Check if we have the expected columns
        required_columns = ["Type", "Category", "Question"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"CSV file is missing required columns: {', '.join(missing_columns)}")
            return pd.DataFrame(columns=required_columns + ["Answer"]), {}
            
        # If no Answer column exists, add an empty one
        if "Answer" not in df.columns:
            df["Answer"] = ""
        
        # Create optimized dictionary structure
        faq_dict = {
            'by_question': {},  # For direct question lookups
            'by_category': {},  # Group FAQs by category
            'by_type': {},      # Group FAQs by type
            'all_faqs': []      # List of all FAQ dictionaries
        }
        
        # Populate the dictionary structure
        for _, row in df.iterrows():
            faq_entry = {
                'question': row['Question'],
                'answer': row['Answer'],
                'type': row['Type'],
                'category': row['Category']
            }
            
            # Add to all_faqs list
            faq_dict['all_faqs'].append(faq_entry)
            
            # Index by question for direct lookups
            faq_dict['by_question'][row['Question']] = faq_entry
            
            # Group by category
            category = row['Category']
            if category not in faq_dict['by_category']:
                faq_dict['by_category'][category] = []
            faq_dict['by_category'][category].append(faq_entry)
            
            # Group by type
            faq_type = row['Type']
            if faq_type not in faq_dict['by_type']:
                faq_dict['by_type'][faq_type] = []
            faq_dict['by_type'][faq_type].append(faq_entry)
        
        # Store the dictionary in session state for global access
        st.session_state['faq_dict'] = faq_dict
        
        return df, faq_dict
        
    except Exception as e:
        error_message = f"Error loading faq_taxonomy.csv: {str(e)}. Please ensure the file exists and is in plain text CSV format."
        st.error(error_message)
        print(error_message)  # Also log to console for debugging
        # Return empty DataFrame and dictionary
        return pd.DataFrame(columns=["Type", "Category", "Question", "Answer"]), {}

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

@st.cache_data
def load_guarantee_terms():
    """Load the guarantee terms from file."""
    try:
        with open("guarantee_terms.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        st.error("Guarantee terms file not found")
        return ""

@st.cache_data
def build_faq_context(faq_dict):
    """
    Converts FAQ dictionary into a bullet point format for context building.
    Uses the optimized dictionary structure.
    """
    if not faq_dict or not faq_dict.get('all_faqs'):
        return "No FAQ/taxonomy data available."
    
    lines = []
    for faq in faq_dict['all_faqs']:
        typ = str(faq['type'])
        cat = str(faq['category'])
        ques = str(faq['question'])
        lines.append(f"- Type: {typ} | Category: {cat} | Q: {ques}")
    return "\n".join(lines)

@st.cache_data
def build_base_context():
    """Cache the base context that doesn't change per request"""
    faq_df, faq_dict = load_faq_csv()
    faq_context = build_faq_context(faq_dict)
    membership_terms = load_membership_terms()
    guarantee_terms = load_guarantee_terms()
    
    return f"""
FAQ Information:
{faq_context}

Membership Terms:
{membership_terms}

Guarantee Terms:
{guarantee_terms}
"""

def build_context(df, scenario_text):
    """Build context from FAQ and terms for classification and response."""
    base_context = build_base_context()
    
    # Only add the scenario-specific part
    full_context = f"""
{base_context}

Current Customer Scenario:
{scenario_text}
"""
    return full_context

df_faq, faq_dict = load_faq_csv()
membership_terms = load_membership_terms()
guarantee_terms = load_guarantee_terms()

###############################################################################
# 4) SET UP SESSION STATE
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

###############################################################################
# 5) BUILD FAQ CONTEXT STRING FROM CSV
###############################################################################
faq_context = build_faq_context(faq_dict)

###############################################################################
# 6) SCENARIO GENERATION PROMPTS
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
# 7) USER TYPE PROMPTS
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
# 8) CLASSIFICATION PROMPT
###############################################################################
@st.cache_data
def get_classification_template():
    """Cache the classification template including departments and JSON structure"""
    return """
Department Options:
- Consumer Support (Account Issues, Job Issues, Payments, Resolving Issues)
- Technical Support (App Issues, Website Issues, Integration Issues)
- Quality Assurance (Tradesperson Vetting, Review Verification, Complaint Investigation)
- Tradesperson Support (Account Management, Jobs, Payments, Technical Issues)
- Finance (Billing, Refunds, Financial Disputes)
- Legal (Contract Issues, Guarantee Claims, Compliance)

Required JSON Structure:
{
  "classification": "...",
  "department": "...",
  "subdepartment": "...",
  "priority": "High|Medium|Low",
  "summary": "...",
  "related_faq_category": "...",
  "estimated_response_time": "..."
}
"""

def classify_scenario(text):
    """Classify the scenario and return structured classification data."""
    try:
        # Start timing
        start_time = time.time()
        
        # Get cached components
        base_context = build_base_context()
        classification_template = get_classification_template()
        
        # Build minimal dynamic prompt
        classification_prompt = f"""Based on this scenario and context, classify the inquiry and return ONLY a valid JSON object (no other text).

Context:
{base_context}

Scenario:
{text}

Classification Guidelines:
{classification_template}"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a classification system that only returns valid JSON objects."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )
        
        # Calculate token usage and costs
        input_tokens = response["usage"]["prompt_tokens"]
        output_tokens = response["usage"]["completion_tokens"]
        total_tokens = response["usage"]["total_tokens"]
        
        # Split input tokens into cached and non-cached portions
        cached_tokens = len(base_context.split()) + len(classification_template.split())
        non_cached_tokens = input_tokens - cached_tokens
        
        # Calculate costs using appropriate rates
        cached_input_cost = calculate_token_cost(cached_tokens, "cached_input")
        non_cached_input_cost = calculate_token_cost(non_cached_tokens, "input")
        output_cost = calculate_token_cost(output_tokens, "output")
        total_cost = cached_input_cost + non_cached_input_cost + output_cost
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Store usage data
        usage_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "non_cached_input_tokens": non_cached_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cached_input_cost": cached_input_cost,
            "non_cached_input_cost": non_cached_input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "response_time": response_time,
            "operation": "classification"
        }
        
        st.session_state["token_usage"]["generations"].append(usage_data)
        st.session_state["token_usage"]["total_input_tokens"] += input_tokens
        st.session_state["token_usage"]["total_output_tokens"] += output_tokens
        st.session_state["token_usage"]["total_cost"] += total_cost
        st.session_state["token_usage"]["response_times"].append(response_time)
        
        # Parse the classification response
        try:
            response_text = response["choices"][0]["message"]["content"].strip()
            if not response_text:
                raise json.JSONDecodeError("Empty response", "", 0)
                
            classification_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["classification", "department", "subdepartment", "priority", 
                             "summary", "related_faq_category", "estimated_response_time"]
            missing_fields = [field for field in required_fields if field not in classification_data]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            return classification_data
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing classification JSON: {str(e)}")
            return {
                "classification": "General",
                "department": "Consumer Support",
                "subdepartment": "General Inquiries",
                "priority": "Medium",
                "summary": "Could not parse classification response.",
                "related_faq_category": "",
                "estimated_response_time": "48 hours"
            }
            
    except Exception as e:
        st.error(f"Error in classification: {str(e)}")
        return {
            "classification": "General",
            "department": "Consumer Support",
            "subdepartment": "General Inquiries",
            "priority": "Medium",
            "summary": f"Error during classification: {str(e)}",
            "related_faq_category": "",
            "estimated_response_time": "48 hours"
        }

###############################################################################
# 9) HELPER: GENERATE SCENARIO VIA OPENAI
###############################################################################
def calculate_token_cost(tokens, token_type):
    """Calculate the cost for tokens based on their type.
    
    Args:
        tokens (int): Number of tokens
        token_type (str): Type of tokens ('input', 'cached_input', or 'output')
    
    Returns:
        float: Cost in dollars
    """
    # GPT-4o mini pricing per 1M tokens:
    # Input: $0.150 / 1M tokens
    # Cached input: $0.075 / 1M tokens
    # Output: $0.600 / 1M tokens
    
    cost_per_million = {
        'input': 0.150,  # $0.150 per 1M tokens
        'cached_input': 0.075,  # $0.075 per 1M tokens
        'output': 0.600,  # $0.600 per 1M tokens
    }
    
    # Convert cost per million to cost per token
    cost_per_token = cost_per_million[token_type] / 1_000_000
    
    return tokens * cost_per_token

def track_token_usage(operation, cached_input_tokens=0, non_cached_input_tokens=0, output_tokens=0, response_time=0):
    """Track token usage and costs in session state"""
    if "token_usage" not in st.session_state:
        st.session_state["token_usage"] = {
            "generations": [],
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0,
            "response_times": []
        }
    
    # Ensure all values are numbers
    cached_input_tokens = int(cached_input_tokens or 0)
    non_cached_input_tokens = int(non_cached_input_tokens or 0)
    output_tokens = int(output_tokens or 0)
    response_time = float(response_time or 0)
    
    # Calculate costs
    cached_input_cost = calculate_token_cost(cached_input_tokens, "cached_input")
    non_cached_input_cost = calculate_token_cost(non_cached_input_tokens, "input")
    output_cost = calculate_token_cost(output_tokens, "output")
    total_cost = cached_input_cost + non_cached_input_cost + output_cost
    
    # Store usage data
    usage_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operation": operation,
        "cached_input_tokens": cached_input_tokens,
        "non_cached_input_tokens": non_cached_input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": cached_input_tokens + non_cached_input_tokens + output_tokens,
        "cached_input_cost": cached_input_cost,
        "non_cached_input_cost": non_cached_input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "response_time": response_time
    }
    
    # Update session state
    st.session_state["token_usage"]["generations"].append(usage_data)
    st.session_state["token_usage"]["total_input_tokens"] += (cached_input_tokens + non_cached_input_tokens)
    st.session_state["token_usage"]["total_output_tokens"] += output_tokens
    st.session_state["token_usage"]["total_cost"] += total_cost
    st.session_state["token_usage"]["response_times"].append(response_time)
    
    return usage_data

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
# 10) HELPER: CLASSIFY SCENARIO VIA OPENAI
###############################################################################
def score_faq_relevance(key_topics, faq_entry):
    """Score a single FAQ's relevance - runs in parallel"""
    try:
        faq_prompt = f"""
        Compare these two texts and rate their relevance on a scale of 0-10:
        
        Customer Issue Summary:
        {key_topics}
        
        FAQ Question:
        {faq_entry['question']}
        FAQ Category: {faq_entry['category']}
        FAQ Type: {faq_entry['type']}
        
        Only respond with a number 0-10, where:
        0 = Completely unrelated
        5 = Somewhat related but not directly applicable
        10 = Highly relevant and directly applicable
        """
        
        score_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a relevance scoring system. Only respond with a number 0-10."},
                {"role": "user", "content": faq_prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        
        try:
            # Extract just the score as a float
            relevance_score = float(score_response['choices'][0]['message']['content'].strip())
            return relevance_score
        except (ValueError, KeyError, TypeError):
            return 0
    except Exception:
        return 0

def find_relevant_faq(scenario_text, faq_dataframe):
    """Find the most relevant FAQ for a given scenario using keyword matching first."""
    try:
        # Get the optimized FAQ dictionary from session state
        faq_dict = st.session_state.get('faq_dict', {})
        if not faq_dict:
            _, faq_dict = load_faq_csv()
            
        # Quick keyword matching first
        scenario_keywords = set(word.lower() for word in str(scenario_text).split() if len(word) > 3)
        best_match = None
        best_score = 0
        best_answer = None
        
        # Try keyword matching first
        for faq_entry in faq_dict['all_faqs']:
            question = str(faq_entry['question']).lower()
            answer = str(faq_entry['answer'])
            category = str(faq_entry['category']).lower()
            faq_type = str(faq_entry['type']).lower()
            
            # Combine all text for matching
            faq_text = f"{question} {category} {faq_type}"
            faq_keywords = set(word.lower() for word in faq_text.split() if len(word) > 3)
            
            # Calculate score based on keyword matches
            common_words = scenario_keywords & faq_keywords
            score = len(common_words) * 2  # Give more weight to keyword matches
            
            # Boost score for exact phrase matches
            for phrase in scenario_text.lower().split('.'):
                if phrase.strip() and phrase.strip() in question:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_match = faq_entry['question']
                best_answer = answer
        
        # Only use semantic search if keyword matching didn't find a good match
        if best_score < 4:
            try:
                # Get cached key topics if available
                key_topics = st.session_state.get('faq_key_topics', {}).get(str(scenario_text))
                
                # If not cached, extract key topics
                if not key_topics:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Extract key topics from this customer scenario."},
                            {"role": "user", "content": str(scenario_text)}
                        ],
                        temperature=0,
                        max_tokens=150
                    )
                    key_topics = response['choices'][0]['message']['content']
                    
                    # Cache the key topics
                    if 'faq_key_topics' not in st.session_state:
                        st.session_state['faq_key_topics'] = {}
                    st.session_state['faq_key_topics'][str(scenario_text)] = key_topics
                
                # Score each FAQ
                for faq_entry in faq_dict['all_faqs']:
                    score = score_faq_relevance(key_topics, faq_entry)
                    if score > best_score:
                        best_score = score
                        best_match = faq_entry['question']
                        best_answer = faq_entry['answer']
            except Exception as e:
                st.error(f"Error in semantic search: {str(e)}")
            
            # Return results if we found a good match
            if best_match and best_score >= 3:
                return best_match, best_answer, best_score
            
        # Return results if we found a good match
        if best_match and best_score >= 3:
            return best_match, best_answer, best_score
            
        return None, None, 0
        
    except Exception as e:
        st.error(f"Error in FAQ matching: {str(e)}")
        return None, None, 0

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

@st.cache_data
def generate_response_template(inbound_route):
    """Cache response templates for different routes"""
    templates = {
        "email": """
        Subject: RE: {classification}
        
        Dear {name},
        
        Thank you for contacting Checkatrade. I understand your inquiry regarding {summary}.
        
        {response_body}
        
        {next_steps}
        
        Best regards,
        Checkatrade Support Team
        """,
        "whatsapp": """
        Hi {name},
        
        Thanks for messaging Checkatrade. Regarding your {summary}:
        
        {response_body}
        
        {next_steps}
        
        Best,
        Checkatrade Support
        """
    }
    return templates.get(inbound_route, "")

def generate_response_suggestion(scenario_dict, classification_dict):
    """Generate a response suggestion using the scenario and classification."""
    try:
        # Start timing
        start_time = time.time()
        
        # Get cached response template
        template = generate_response_template(scenario_dict.get("inbound_route", ""))
        
        # Build minimal context
        context = f"""
        Customer Scenario:
        {scenario_dict.get('scenario_text', '')}
        
        User Type: {scenario_dict.get('user_type', '')}
        Classification: {classification_dict.get('classification', '')}
        Priority: {classification_dict.get('priority', '')}
        Summary: {classification_dict.get('summary', '')}
        
        Instructions:
        1. Be professional and empathetic
        2. Address all aspects of the customer's query
        3. Keep the response concise but informative
        4. Provide clear next steps
        """
        
        # Only include account details if they exist and are relevant
        account_details = scenario_dict.get('account_details', {})
        if any(account_details.values()):
            context += "\nCustomer Details:\n"
            for key, value in account_details.items():
                if value:
                    context += f"{key}: {value}\n"
        
        # Process relevant FAQ
        try:
            relevant_faq, faq_answer, faq_relevance = find_relevant_faq(scenario_dict.get('scenario_text', ''), load_faq_csv())
            if relevant_faq and faq_answer and faq_relevance >= 3:
                context += f"""
                Relevant FAQ:
                Question: {relevant_faq}
                Answer: {faq_answer}
                """
        except Exception as e:
            st.error(f"Error finding relevant FAQ: {str(e)}")
        
        # Generate response using OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Customer Support Agent for Checkatrade. Provide a concise, professional response."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract token usage
            input_tokens = len(context.split())
            output_tokens = response.usage.completion_tokens
            
            # Calculate costs
            input_cost = calculate_token_cost(input_tokens, "input")
            output_cost = calculate_token_cost(output_tokens, "output")
            
            # Track usage
            track_token_usage(
                operation="response_generation",
                non_cached_input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time
            )
            
            return (
                response.choices[0].message.content,
                input_tokens,
                output_tokens,
                input_cost,
                output_cost
            )
            
        except Exception as e:
            st.error(f"Error in OpenAI call: {str(e)}")
            return "Sorry, I couldn't generate a response at this time. Please try again later.", 0, 0, 0, 0
            
    except Exception as e:
        st.error(f"Error in response generation: {str(e)}")
        return "Sorry, I couldn't generate a response at this time. Please try again later.", 0, 0, 0, 0

###############################################################################
# 11) STREAMLIT APP UI
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
                        # Calculate total input cost
                        total_input_cost = classification_data['cached_input_cost'] + classification_data['non_cached_input_cost']
                        
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
                                "Cached Input Tokens",
                                f"{classification_data['cached_input_tokens']:,}",
                                f"${classification_data['cached_input_cost']:.4f}"
                            )
                        
                        with metric_col3:
                            st.metric(
                                "Non-Cached Input Tokens",
                                f"{classification_data['non_cached_input_tokens']:,}",
                                f"${classification_data['non_cached_input_cost']:.4f}"
                            )
                        
                        with metric_col4:
                            st.metric(
                                "Output Tokens",
                                f"{classification_data['output_tokens']:,}",
                                f"${classification_data['output_cost']:.4f}"
                            )
                        
                        # Add total cost summary
                        st.markdown("<div class='inquiry-section'>Total Costs</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-label'>Total Input Cost (Cached + Non-Cached): ${total_input_cost:.4f}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-label'>Total Output Cost: ${classification_data['output_cost']:.4f}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-label'>Total Cost: ${classification_data['total_cost']:.4f}</div>", unsafe_allow_html=True)
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
                    keyword_faq, keyword_answer, keyword_score = find_relevant_faq(scenario_text, df_faq)
                    if keyword_faq and keyword_score >= 3:  # Higher threshold for keyword matching
                        # If we already have a FAQ but this one is more relevant, replace it
                        if keyword_score > faq_relevance_score:
                            relevant_faq = keyword_faq
                            relevant_answer = keyword_answer
                            faq_relevance_score = keyword_score

                # Only display FAQ if we have a sufficiently relevant match
                if relevant_faq and faq_relevance_score >= 3:
                    faq_content = f"""
                    <div class="classification-card">
                        <div class="classification-header">Relevant FAQ</div>
                        <div class="field-value"><strong>Question:</strong> {str(relevant_faq)}</div>
                    """
                    
                    # If we have an answer, display it as well
                    if 'relevant_answer' in locals() and relevant_answer:
                        faq_content += f"""
                        <div class="field-value"><strong>Answer:</strong> {str(relevant_answer)}</div>
                        """
                    
                    faq_content += "</div>"
                    st.markdown(faq_content, unsafe_allow_html=True)
                
                # Generate response suggestion for email or whatsapp
                inbound_route = st.session_state["generated_scenario"].get("inbound_route", "")
                if inbound_route in ["email", "whatsapp"]:
                    try:
                        response_text, input_tokens, output_tokens, input_cost, output_cost = generate_response_suggestion(
                        st.session_state["generated_scenario"], 
                        classification_result
                    )
                        response_card = f"""
                        <div class='classification-card'>
                            <div class='classification-header'>Suggested {inbound_route.capitalize()} Response</div>
                            <div class='field-value' style='white-space: pre-wrap;'>{str(response_text)}</div>
                        </div>
                        """
                        st.markdown(response_card, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Could not generate response suggestion: {str(e)}")
                        
                # Add metrics for the classification tokens and cost
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    last_usage = st.session_state["token_usage"]["generations"][-1]
                    response_time = last_usage.get("response_time", 0)
                    st.metric("Response Time", f"{response_time:.2f}s")
                
                with col2:
                    # Handle both token usage data structures
                    input_tokens = last_usage.get("input_tokens", last_usage.get("cached_input_tokens", 0) + last_usage.get("non_cached_input_tokens", 0))
                    input_cost = last_usage.get("input_cost", last_usage.get("cached_input_cost", 0) + last_usage.get("non_cached_input_cost", 0))
                    st.metric("Input Tokens", f"{input_tokens} (${input_cost:.4f})")
                
                with col3:
                    output_tokens = last_usage.get("output_tokens", 0)
                    output_cost = last_usage.get("output_cost", 0)
                    st.metric("Output Tokens", f"{output_tokens} (${output_cost:.4f})")
                    
                with col4:
                    total_cost = last_usage.get("total_cost", 0)
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
                if inbound_route in ["email", "whatsapp", "webform"] and 'response_suggestion' in locals():
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "response_suggestion"] = response_suggestion
                
                # Save any relevant FAQ that was found
                if relevant_faq and faq_relevance_score >= 3:
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "relevant_faq"] = relevant_faq
                    st.session_state["inquiries"].at[st.session_state["current_case_id"], "faq_relevance_score"] = faq_relevance_score
                    # Also save the FAQ answer if available
                    if 'relevant_answer' in locals() and relevant_answer:
                        st.session_state["inquiries"].at[st.session_state["current_case_id"], "relevant_faq_answer"] = relevant_answer
                
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
    # Analytics in expander
    with st.expander("View Analytics Dashboard", expanded=False):
        if "token_usage" in st.session_state and st.session_state["token_usage"]["generations"]:
            st.subheader("Analytics Overview")
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

        else:
            st.info("No analytics data available yet. Generate some responses to see analytics.")
    
    # View Inquiries section
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
