import streamlit as st
import pandas as pd
import json

def show_inquiries():
    """
    Display the View Inquiries page content
    """
    st.title("View Inquiries")
    
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
        # Display the most recent inquiry card first with full details
        st.subheader("Most Recent Inquiry")
        
        # Get the most recent inquiry
        recent_row = df.iloc[0]
        
        # Create a collapsible container for the most recent inquiry
        with st.expander("View Most Recent Inquiry", expanded=True):
            # Create a container with background color for entire inquiry
            with st.container():
                # Header with classification and priority
                st.markdown(f"### {recent_row['classification']} (Priority: {recent_row['priority']})")
                
                # Basic information in 2 columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Timestamp:**")
                    st.text(recent_row['timestamp'])
                    
                    if recent_row['inbound_route']:
                        st.markdown("**Inbound Route:**")
                        st.text(recent_row['inbound_route'])
                    
                    if recent_row['ivr_flow']:
                        st.markdown("**IVR Flow:**")
                        st.text(recent_row['ivr_flow'])
                    
                    if recent_row['ivr_selections']:
                        st.markdown("**IVR Selections:**")
                        st.text(recent_row['ivr_selections'])
                
                with col2:
                    if recent_row['user_type']:
                        st.markdown("**User Type:**")
                        st.text(recent_row['user_type'])
                    
                    if recent_row['phone_email']:
                        st.markdown("**Phone/Email:**")
                        st.text(recent_row['phone_email'])
                    
                    if recent_row['membership_id']:
                        st.markdown("**Membership ID:**")
                        st.text(recent_row['membership_id'])
                
                # Account details section if available
                has_account_info = (recent_row['account_name'] or recent_row['account_location'] or 
                                recent_row['account_reviews'] or recent_row['account_jobs'] or
                                recent_row['membership_id'])
                
                if has_account_info:
                    st.markdown("### Account Details")
                    
                    if recent_row['account_name']:
                        st.markdown("**Name:**")
                        st.text(recent_row['account_name'])
                    
                    if recent_row['membership_id']:
                        st.markdown("**Membership ID:**")
                        st.text(recent_row['membership_id'])
                    
                    if recent_row['account_location']:
                        st.markdown("**Location:**")
                        st.text(recent_row['account_location'])
                    
                    if recent_row['account_reviews']:
                        st.markdown("**Latest Reviews:**")
                        st.text(recent_row['account_reviews'])
                    
                    if recent_row['account_jobs']:
                        st.markdown("**Latest Jobs:**")
                        st.text(recent_row['account_jobs'])
                    
                    # Show project cost and payment status if available
                    if recent_row['project_cost'] or recent_row['payment_status']:
                        st.markdown("**Project Details:**")
                        st.text(f"Project Cost: {recent_row['project_cost']} | Status: {recent_row['payment_status']}")
                
                # Scenario text section
                if recent_row['scenario_text']:
                    st.markdown("### Scenario Text")
                    st.text(recent_row['scenario_text'])
                
                # Classification Summary section
                st.markdown("### Classification Summary")
                
                # Create classification display with proper styling
                with st.container():
                    # Set color for priority
                    priority_color = "#ffab40"  # default medium
                    if recent_row['priority'] == "High":
                        priority_color = "#ff5252"
                    elif recent_row['priority'] == "Low":
                        priority_color = "#69f0ae"
                    
                    # Classification details in 2 columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Classification:**")
                        st.text(recent_row['classification'])
                        
                        st.markdown("**Department:**")
                        st.text(recent_row['department'])
                        
                        st.markdown("**Subdepartment:**")
                        st.text(recent_row['subdepartment'])
                    
                    with col2:
                        st.markdown("**Priority:**")
                        # Use markdown for colored text
                        st.markdown(f"<span style='color:{priority_color};font-weight:bold;'>{recent_row['priority']}</span>", unsafe_allow_html=True)
                        
                        st.markdown("**Estimated Response Time:**")
                        st.text(recent_row['estimated_response_time'])
                    
                    # Summary in full width
                    st.markdown("**Summary:**")
                    st.text(recent_row['summary'])
                    
                    # Related FAQ category if available
                    if 'related_faq_category' in recent_row and recent_row['related_faq_category']:
                        st.markdown("**Related FAQ Category:**")
                        st.text(recent_row['related_faq_category'])
                
                # Case Management section
                st.markdown("### Case Management")
                
                # Show current case status with color coding
                case_status = recent_row.get('case_status', 'New')
                status_color = "#64B5F6"  # Default blue
                if case_status == "Resolved" or case_status == "Closed":
                    status_color = "#4CAF50"  # Green
                elif case_status == "In Progress":
                    status_color = "#FFA726"  # Orange
                elif case_status == "Awaiting Customer" or case_status == "Awaiting Tradesperson":
                    status_color = "#FFD54F"  # Amber
                
                st.markdown("**Case Status:**")
                st.markdown(f"<span style='color:{status_color};font-weight:bold;'>{case_status}</span>", unsafe_allow_html=True)
                
                # Allow agent to update case status and notes
                with st.expander("Update Case", expanded=False):
                    # Case status selection
                    case_status_options = ["New", "In Progress", "Awaiting Customer", "Awaiting Tradesperson", "Resolved", "Closed"]
                    selected_status = st.selectbox(
                        "Update Case Status:",
                        options=case_status_options,
                        index=case_status_options.index(case_status) if case_status in case_status_options else 0,
                        key=f"status_{df.index[0]}"
                    )
                    
                    # Agent notes text area
                    agent_notes = st.text_area(
                        "Agent Notes:",
                        value=recent_row.get('agent_notes', ''),
                        height=150,
                        placeholder="Enter your notes about the case here...",
                        key=f"notes_{df.index[0]}"
                    )
                    
                    # Save button for agent updates
                    if st.button("Save Updates", key=f"save_{df.index[0]}"):
                        # Get the index in the original DataFrame
                        idx = df.index[0]
                        
                        # Update the parent session state DataFrame
                        st.session_state["inquiries"].at[idx, "case_status"] = selected_status
                        st.session_state["inquiries"].at[idx, "agent_notes"] = agent_notes
                        
                        # Save changes to file
                        try:
                            # Convert timestamps to strings to make JSON serializable
                            df_copy = st.session_state["inquiries"].copy()
                            if 'timestamp' in df_copy.columns and not df_copy.empty:
                                df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                            
                            # Save to file
                            json_data = df_copy.to_dict(orient="records")
                            with open("inquiries.json", "w") as f:
                                json.dump(json_data, f, indent=2)
                            
                            st.success(f"Case updated - Status: {selected_status}")
                            
                            # Refresh the page to show updated data
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Failed to save updates: {str(e)}")
                
                # Display existing agent notes if any
                if recent_row.get('agent_notes'):
                    st.markdown("**Current Agent Notes:**")
                    st.text_area("", value=recent_row.get('agent_notes', ''), disabled=True, height=100)
        
        # Show previous inquiries
        if len(df) > 1:
            st.subheader("Previous Inquiries")
            with st.expander("See More Inquiries", expanded=True):
                for idx, row in df.iloc[1:].iterrows():
                    # Add collapsible section for each previous inquiry
                    with st.expander(f"Inquiry #{idx} - {row['classification']} (Priority: {row['priority']})", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Timestamp:**")
                            st.text(row['timestamp'])
                            
                            if row['inbound_route']:
                                st.markdown("**Inbound Route:**")
                                st.text(row['inbound_route'])
                        
                        with col2:
                            if row['user_type']:
                                st.markdown("**User Type:**")
                                st.text(row['user_type'])
                            
                            if row['phone_email']:
                                st.markdown("**Phone/Email:**")
                                st.text(row['phone_email'])
                        
                        # Display scenario text if available
                        if row['scenario_text']:
                            st.markdown("**Scenario Text:**")
                            st.text(row['scenario_text'])
                        
                        # Display classification info
                        st.markdown("**Classification Summary:**")
                        st.text(f"{row['classification']} ({row['priority']}) - {row['summary']}")
                        
                        # Case status
                        case_status = row.get('case_status', 'New')
                        status_color = "#64B5F6"  # Default blue
                        if case_status == "Resolved" or case_status == "Closed":
                            status_color = "#4CAF50"  # Green
                        elif case_status == "In Progress":
                            status_color = "#FFA726"  # Orange
                        elif case_status == "Awaiting Customer" or case_status == "Awaiting Tradesperson":
                            status_color = "#FFD54F"  # Amber
                        
                        st.markdown("**Case Status:**")
                        st.markdown(f"<span style='color:{status_color};font-weight:bold;'>{case_status}</span>", unsafe_allow_html=True)
                        
                        # Update case button
                        with st.expander("Update Case", expanded=False):
                            # Case status selection
                            case_status_options = ["New", "In Progress", "Awaiting Customer", "Awaiting Tradesperson", "Resolved", "Closed"]
                            selected_status = st.selectbox(
                                "Update Case Status:",
                                options=case_status_options,
                                index=case_status_options.index(case_status) if case_status in case_status_options else 0,
                                key=f"status_{idx}"
                            )
                            
                            # Agent notes text area
                            agent_notes = st.text_area(
                                "Agent Notes:",
                                value=row.get('agent_notes', ''),
                                height=150,
                                placeholder="Enter your notes about the case here...",
                                key=f"notes_{idx}"
                            )
                            
                            # Save button for agent updates
                            if st.button("Save Updates", key=f"save_{idx}"):
                                # Update the parent session state DataFrame
                                st.session_state["inquiries"].at[idx, "case_status"] = selected_status
                                st.session_state["inquiries"].at[idx, "agent_notes"] = agent_notes
                                
                                # Save changes to file
                                try:
                                    # Convert timestamps to strings to make JSON serializable
                                    df_copy = st.session_state["inquiries"].copy()
                                    if 'timestamp' in df_copy.columns and not df_copy.empty:
                                        df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                                    
                                    # Save to file
                                    json_data = df_copy.to_dict(orient="records")
                                    with open("inquiries.json", "w") as f:
                                        json.dump(json_data, f, indent=2)
                                    
                                    st.success(f"Case {idx} updated - Status: {selected_status}")
                                    
                                    # Refresh the page to show updated data
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Failed to save updates: {str(e)}")
                            
                            # Display existing agent notes if any
                            if row.get('agent_notes'):
                                st.markdown("**Current Agent Notes:**")
                                st.text_area("", value=row.get('agent_notes', ''), disabled=True, height=100, key=f"display_notes_{idx}")
    else:
        st.info("No inquiries found. Generate and classify some scenarios first.") 