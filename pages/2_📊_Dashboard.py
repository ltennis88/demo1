import streamlit as st
import pandas as pd
import json
import plotly.express as px
import random

# Page config
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Add the same CSS from main app
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
</style>
""", unsafe_allow_html=True)

st.title("Analytics Dashboard")

# Load inquiries
try:
    with open("inquiries.json", "r") as f:
        inquiries_data = json.load(f)
    df = pd.DataFrame(inquiries_data)
    
    # Sort by timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
except Exception as e:
    st.error(f"Error loading inquiries: {str(e)}")
    df = pd.DataFrame()

if len(df) > 0:
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

    # Data Exports
    st.header("Data Exports")
    if len(df) > 0:
        csv_data = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv")

        json_data = df.to_json(orient="records")
        st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json")
    else:
        st.write("No data to export yet.")
else:
    st.info("No inquiries found. Generate and classify some scenarios first.") 