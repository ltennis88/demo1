import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def show_analytics():
    """
    Display the Analytics Dashboard page content
    """
    st.title("Analytics Dashboard")
    
    # Load inquiries from session state
    if "inquiries" in st.session_state:
        df = st.session_state["inquiries"]
    else:
        # If not in session state, try to load from file
        try:
            with open("inquiries.json", "r") as f:
                inquiries_data = json.load(f)
            df = pd.DataFrame(inquiries_data)
        except Exception as e:
            st.error(f"Error loading inquiries: {str(e)}")
            df = pd.DataFrame()
    
    if len(df) > 0:
        # Convert timestamp to datetime for analysis
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except:
            pass
        
        # Get current date for filtering
        current_date = pd.to_datetime(datetime.now())
        
        # Tabs for different analysis views
        tab1, tab2, tab3 = st.tabs(["Overview Metrics", "Classification Analysis", "Time Analysis"])
        
        with tab1:
            st.subheader("Overview Metrics")
            
            # Summary metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Inquiries", len(df))
            
            with col2:
                # Calculate open cases (not resolved or closed)
                if 'case_status' in df.columns:
                    open_cases = df[~df['case_status'].isin(['Resolved', 'Closed'])].shape[0]
                    st.metric("Open Cases", open_cases)
                else:
                    st.metric("Open Cases", "N/A")
            
            with col3:
                # High priority cases
                if 'priority' in df.columns:
                    high_priority = df[df['priority'] == 'High'].shape[0]
                    st.metric("High Priority Cases", high_priority)
                else:
                    st.metric("High Priority Cases", "N/A")
            
            with col4:
                # Calculate average response time
                if 'estimated_response_time' in df.columns:
                    # Extract number of hours from strings like "24 hours"
                    try:
                        df['hours'] = df['estimated_response_time'].str.extract('(\d+)').astype(float)
                        avg_time = df['hours'].mean()
                        st.metric("Avg. Response Time", f"{avg_time:.1f} hours")
                    except:
                        st.metric("Avg. Response Time", "N/A")
                else:
                    st.metric("Avg. Response Time", "N/A")
            
            # Case Status Distribution
            if 'case_status' in df.columns:
                st.subheader("Case Status Distribution")
                status_counts = df['case_status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.pie(status_counts, values='Count', names='Status', 
                             color_discrete_sequence=px.colors.sequential.Viridis)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # User Type Distribution
            if 'user_type' in df.columns:
                st.subheader("User Type Distribution")
                user_counts = df['user_type'].value_counts().reset_index()
                user_counts.columns = ['User Type', 'Count']
                
                fig = px.bar(user_counts, x='User Type', y='Count', 
                           color='Count', color_continuous_scale='Viridis')
                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    xaxis=dict(tickangle=0)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Classification Analysis")
            
            # Classification Distribution
            if 'classification' in df.columns:
                st.subheader("Classification Types")
                class_counts = df['classification'].value_counts().reset_index()
                class_counts.columns = ['Classification', 'Count']
                
                fig = px.bar(class_counts, x='Classification', y='Count', 
                           color='Count', color_continuous_scale='Viridis')
                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    xaxis=dict(tickangle=-45)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Priority Distribution
            if 'priority' in df.columns:
                st.subheader("Priority Distribution")
                
                # Custom order for priorities
                priority_order = ['Low', 'Medium', 'High']
                df['priority_ordered'] = pd.Categorical(df['priority'], categories=priority_order, ordered=True)
                
                priority_counts = df['priority_ordered'].value_counts().reset_index()
                priority_counts.columns = ['Priority', 'Count']
                
                # Sort by our custom order
                priority_counts = priority_counts.sort_values('Priority')
                
                # Custom colors for priorities
                colors = {'Low': '#69f0ae', 'Medium': '#ffab40', 'High': '#ff5252'}
                
                fig = px.pie(priority_counts, values='Count', names='Priority',
                             color='Priority', color_discrete_map=colors)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    height=350,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # Department Distribution
            if 'department' in df.columns:
                st.subheader("Department Distribution")
                dept_counts = df['department'].value_counts().reset_index()
                dept_counts.columns = ['Department', 'Count']
                
                fig = px.bar(dept_counts, x='Department', y='Count', 
                           color='Count', color_continuous_scale='Viridis')
                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    xaxis=dict(tickangle=-45)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Time Analysis")
            
            # Time series of inquiries over time
            if 'timestamp' in df.columns:
                # Create a date column
                df['date'] = df['timestamp'].dt.date
                
                # Count inquiries by date
                time_counts = df.groupby('date').size().reset_index(name='Count')
                
                # Ensure we have a continuous date range
                if len(time_counts) > 1:
                    date_range = pd.date_range(start=min(time_counts['date']), end=max(time_counts['date']))
                    date_df = pd.DataFrame({'date': date_range})
                    time_counts = pd.merge(date_df, time_counts, on='date', how='left').fillna(0)
                
                fig = px.line(time_counts, x='date', y='Count', 
                             title='Inquiries Volume Over Time')
                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=50, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    xaxis_title="Date",
                    yaxis_title="Number of Inquiries"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Inbound route distribution over time
                if 'inbound_route' in df.columns:
                    st.subheader("Inbound Route Distribution")
                    
                    route_time = df.groupby(['date', 'inbound_route']).size().reset_index(name='Count')
                    
                    fig = px.line(route_time, x='date', y='Count', color='inbound_route',
                                title='Inbound Routes Over Time')
                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=10, t=50, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"),
                        xaxis_title="Date",
                        yaxis_title="Number of Inquiries"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for analysis. Generate some scenarios first.")

def show_analytics_content():
    """
    Display the Analytics Dashboard content without the page title
    for use within the main app.py page
    """
    # Load inquiries from session state
    if "inquiries" in st.session_state:
        df = st.session_state["inquiries"]
    else:
        # If not in session state, try to load from file
        try:
            with open("inquiries.json", "r") as f:
                inquiries_data = json.load(f)
            df = pd.DataFrame(inquiries_data)
        except Exception as e:
            st.error(f"Error loading inquiries: {str(e)}")
            df = pd.DataFrame() 