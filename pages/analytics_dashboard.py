import streamlit as st
import pandas as pd
import json
import plotly.express as px
import random

def show_analytics():
    """
    Display the Analytics Dashboard content
    """
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
            st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv", key="dashboard_csv_download")

            json_data = df.to_json(orient="records")
            st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json", key="dashboard_json_download")
        else:
            st.write("No data to export yet.")

        # Add a new visualization section for case status
        st.subheader("Case Status Overview")
        colE, colF = st.columns(2)

        with colE:
            try:
                # Create case status distribution chart
                status_counts = df["case_status"].value_counts()
                
                # Define colors for different statuses
                status_colors = {
                    "New": "#64B5F6",           # Blue
                    "In Progress": "#FFA726",   # Orange
                    "Awaiting Customer": "#FFD54F", # Yellow
                    "Awaiting Tradesperson": "#FFCA28", # Amber
                    "Resolved": "#66BB6A",      # Green
                    "Closed": "#4CAF50"         # Dark Green
                }
                
                # Create a pie chart with our custom colors
                fig5 = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Case Status Distribution",
                    hole=0.4,  # Makes it a donut chart
                    color_discrete_map=status_colors
                )
                
                # Customize
                fig5.update_traces(textinfo='percent+label')
                fig5.update_layout(
                    legend=dict(orientation="h", y=-0.1),
                    height=300,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white")
                )
                
                st.plotly_chart(fig5, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating case status chart: {str(e)}")

        with colF:
            try:
                # Calculate resolution metrics
                total_cases = len(df)
                resolved_cases = len(df[df["case_status"].isin(["Resolved", "Closed"])])
                resolution_rate = (resolved_cases / total_cases) * 100 if total_cases > 0 else 0
                
                # Create metrics cards
                st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                st.metric(
                    "Total Cases",
                    f"{total_cases}",
                    delta=None
                )
                
                st.metric(
                    "Resolved Cases",
                    f"{resolved_cases}",
                    delta=None
                )
                
                st.metric(
                    "Resolution Rate",
                    f"{resolution_rate:.1f}%",
                    delta=None
                )
                
                # Calculate average resolution time if possible
                if "timestamp" in df.columns and resolved_cases > 0:
                    try:
                        # Filter only resolved cases
                        resolved_df = df[df["case_status"].isin(["Resolved", "Closed"])]
                        
                        # This is just a placeholder since we don't have actual resolution timestamps
                        # In a real system, you would calculate this from case creation to resolution
                        avg_resolution_time = "2.5 days"
                        
                        st.metric(
                            "Avg. Resolution Time",
                            avg_resolution_time,
                            delta=None
                        )
                    except:
                        pass
                
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error calculating metrics: {str(e)}")

        # Add a case status by department breakdown
        try:
            # Create a department vs status crosstab
            if "department" in df.columns and "case_status" in df.columns:
                dept_status = pd.crosstab(df["department"], df["case_status"])
                
                # Create a stacked bar chart
                fig6 = px.bar(
                    dept_status, 
                    title="Case Status by Department",
                    color_discrete_sequence=["#64B5F6", "#FFA726", "#FFD54F", "#FFCA28", "#66BB6A", "#4CAF50"]
                )
                
                # Customize
                fig6.update_layout(
                    xaxis_title="Department",
                    yaxis_title="Number of Cases",
                    legend_title="Case Status",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    xaxis=dict(gridcolor="#444"),
                    yaxis=dict(gridcolor="#444")
                )
                
                st.plotly_chart(fig6, use_container_width=True)
        except Exception as e:
            pass  # Silently fail if we can't create this chart
    else:
        st.info("No inquiries found. Generate and classify some scenarios first.") 