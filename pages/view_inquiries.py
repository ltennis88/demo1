import streamlit as st
import pandas as pd
import json

def show_inquiries():
    """
    Display the View Inquiries page content
    """
    st.title("View Inquiries")
    
    # Load inquiries from session state
    df = st.session_state["inquiries"]
    
    if len(df) > 0:
        # Sort inquiries by timestamp in descending order (most recent first)
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
        except:
            # If timestamp conversion fails, just use the existing order
            pass
        
        # Display the most recent inquiry card first with full details
        st.subheader("Most Recent Inquiry")
        
        # Get the most recent inquiry
        recent_row = df.iloc[0]
        
        # Create a collapsible container for the most recent inquiry
        with st.expander("View Most Recent Inquiry", expanded=True):
            st.markdown("<div class='info-container'>", unsafe_allow_html=True)
            
            # Display header with classification and priority
            st.markdown(f"<div style='font-size: 18px; font-weight: bold; margin-bottom: 10px;'>{recent_row['classification']} (Priority: {recent_row['priority']})</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['timestamp']}</div>", unsafe_allow_html=True)
                
                if recent_row['inbound_route']:
                    st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['inbound_route']}</div>", unsafe_allow_html=True)
                
                if recent_row['ivr_flow']:
                    st.markdown("<div class='inquiry-label'>IVR Flow:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['ivr_flow']}</div>", unsafe_allow_html=True)
                
                if recent_row['ivr_selections']:
                    st.markdown("<div class='inquiry-label'>IVR Selections:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['ivr_selections']}</div>", unsafe_allow_html=True)
            
            with col2:
                if recent_row['user_type']:
                    st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['user_type']}</div>", unsafe_allow_html=True)
                
                if recent_row['phone_email']:
                    st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['phone_email']}</div>", unsafe_allow_html=True)
                
                if recent_row['membership_id']:
                    st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['membership_id']}</div>", unsafe_allow_html=True)
            
            # Account details section - only show if there's actual account info
            has_account_info = (recent_row['account_name'] or recent_row['account_location'] or 
                               recent_row['account_reviews'] or recent_row['account_jobs'] or
                               recent_row['membership_id'])
            
            if has_account_info:
                st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
                
                if recent_row['account_name']:
                    st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['account_name']}</div>", unsafe_allow_html=True)
                
                if recent_row['membership_id']:
                    st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['membership_id']}</div>", unsafe_allow_html=True)
                
                if recent_row['account_location']:
                    st.markdown("<div class='inquiry-label'>Location:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['account_location']}</div>", unsafe_allow_html=True)
                
                if recent_row['account_reviews']:
                    st.markdown("<div class='inquiry-label'>Latest Reviews:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['account_reviews']}</div>", unsafe_allow_html=True)
                
                if recent_row['account_jobs']:
                    st.markdown("<div class='inquiry-label'>Latest Jobs:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>{recent_row['account_jobs']}</div>", unsafe_allow_html=True)
                
                # Show project cost and payment status side by side if available
                if recent_row['project_cost'] or recent_row['payment_status']:
                    st.markdown("<div class='inquiry-label'>Project Details:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail'>Project Cost: {recent_row['project_cost']} &nbsp;&nbsp;&nbsp; Status: {recent_row['payment_status']}</div>", unsafe_allow_html=True)
            
            # Scenario text section
            if recent_row['scenario_text']:
                st.markdown("<div class='inquiry-section'>Scenario Text</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['scenario_text']}</div>", unsafe_allow_html=True)
            
            # Classification results section
            st.markdown("<div class='inquiry-section'>Classification Results</div>", unsafe_allow_html=True)
            
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
            .priority-high {
                color: #ff5252;
                font-weight: bold;
            }
            .priority-medium {
                color: #ffab40;
                font-weight: bold;
            }
            .priority-low {
                color: #69f0ae;
                font-weight: bold;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Start the styled container
            st.markdown("<div class='styled-container'>", unsafe_allow_html=True)
            
            # Create each classification field with proper formatting
            st.markdown(f"""
            <div class='result-row'>
                <div class='result-label'>Classification:</div>
                <div class='result-value'>{recent_row.get("classification", "Unknown")}</div>
            </div>
            
            <div class='result-row'>
                <div class='result-label'>Department:</div>
                <div class='result-value'>{recent_row.get("department", "Unknown")}</div>
            </div>
            
            <div class='result-row'>
                <div class='result-label'>Subdepartment:</div>
                <div class='result-value'>{recent_row.get("subdepartment", "Unknown")}</div>
            </div>
            
            <div class='result-row'>
                <div class='result-label'>Priority:</div>
                <div class='result-value'>
                    <span class='priority-{recent_row.get("priority", "medium").lower()}'>
                        {recent_row.get("priority", "Medium")}
                    </span>
                </div>
            </div>
            
            <div class='result-row'>
                <div class='result-label'>Estimated Response Time:</div>
                <div class='result-value'>{recent_row.get("estimated_response_time", "Unknown")}</div>
            </div>
            
            <div class='result-row'>
                <div class='result-label'>Summary:</div>
                <div class='result-value'>{recent_row.get("summary", "No summary available")}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add related FAQ category if available
            if recent_row.get('related_faq_category'):
                st.markdown(f"""
                <div class='result-row'>
                    <div class='result-label'>Related FAQ Category:</div>
                    <div class='result-value'>{recent_row.get("related_faq_category", "")}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Close the container
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Case Management section
            st.markdown("<div class='inquiry-section'>Case Management</div>", unsafe_allow_html=True)
            
            # Show current case status with color coding
            case_status = recent_row.get('case_status', 'New')
            status_color = "#64B5F6"  # Default blue
            if case_status == "Resolved" or case_status == "Closed":
                status_color = "#4CAF50"  # Green
            elif case_status == "In Progress":
                status_color = "#FFA726"  # Orange
            elif case_status == "Awaiting Customer" or case_status == "Awaiting Tradesperson":
                status_color = "#FFD54F"  # Amber
            
            st.markdown("<div class='inquiry-label'>Case Status:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='inquiry-detail' style='color: {status_color}; font-weight: bold;'>{case_status}</div>", unsafe_allow_html=True)
            
            # Allow agent to update case status and notes
            with st.expander("Update Case", expanded=False):
                # Case status selection
                case_status_options = ["New", "In Progress", "Awaiting Customer", "Awaiting Tradesperson", "Resolved", "Closed"]
                selected_status = st.selectbox(
                    "Update Case Status:",
                    options=case_status_options,
                    index=case_status_options.index(case_status) if case_status in case_status_options else 0
                )
                
                # Agent notes text area
                agent_notes = st.text_area(
                    "Agent Notes:",
                    value=recent_row.get('agent_notes', ''),
                    height=150,
                    placeholder="Enter your notes about the case here..."
                )
                
                # Save button for agent updates
                if st.button("Save Updates"):
                    # Update the DataFrame with the new status and notes
                    st.session_state["inquiries"].at[df.index[0], "case_status"] = selected_status
                    st.session_state["inquiries"].at[df.index[0], "agent_notes"] = agent_notes
                    
                    # Save to file
                    from app import save_inquiries_to_file
                    save_inquiries_to_file()
                    
                    st.success(f"Case updated - Status: {selected_status}")
                    st.experimental_rerun()
            
            # Display existing agent notes if any
            if recent_row.get('agent_notes'):
                st.markdown("<div class='inquiry-label'>Current Agent Notes:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail' style='white-space: pre-wrap;'>{recent_row.get('agent_notes', '')}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Show previous inquiries
        if len(df) > 1:
            st.subheader("Previous Inquiries")
            
            for idx, row in df.iloc[1:].iterrows():
                # Create an expander for each previous inquiry
                with st.expander(f"Inquiry #{idx} - {row['classification']} (Priority: {row['priority']})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['timestamp']}</div>", unsafe_allow_html=True)
                        
                        if row['inbound_route']:
                            st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['inbound_route']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        if row['user_type']:
                            st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['user_type']}</div>", unsafe_allow_html=True)
                        
                        if row['phone_email']:
                            st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['phone_email']}</div>", unsafe_allow_html=True)
                    
                    # Show scenario text if available
                    if row['scenario_text']:
                        st.markdown("<div class='inquiry-section'>Scenario Text</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['scenario_text']}</div>", unsafe_allow_html=True)
                    
                    # Classification results in same format as main inquiry
                    st.markdown("<div class='inquiry-section'>Classification Results</div>", unsafe_allow_html=True)
                    
                    # Start the styled container
                    st.markdown("<div class='styled-container'>", unsafe_allow_html=True)
                    
                    # Create each classification field with proper formatting
                    st.markdown(f"""
                    <div class='result-row'>
                        <div class='result-label'>Classification:</div>
                        <div class='result-value'>{row.get("classification", "Unknown")}</div>
                    </div>
                    
                    <div class='result-row'>
                        <div class='result-label'>Department:</div>
                        <div class='result-value'>{row.get("department", "Unknown")}</div>
                    </div>
                    
                    <div class='result-row'>
                        <div class='result-label'>Subdepartment:</div>
                        <div class='result-value'>{row.get("subdepartment", "Unknown")}</div>
                    </div>
                    
                    <div class='result-row'>
                        <div class='result-label'>Priority:</div>
                        <div class='result-value'>
                            <span class='priority-{row.get("priority", "medium").lower()}'>
                                {row.get("priority", "Medium")}
                            </span>
                        </div>
                    </div>
                    
                    <div class='result-row'>
                        <div class='result-label'>Estimated Response Time:</div>
                        <div class='result-value'>{row.get("estimated_response_time", "Unknown")}</div>
                    </div>
                    
                    <div class='result-row'>
                        <div class='result-label'>Summary:</div>
                        <div class='result-value'>{row.get("summary", "No summary available")}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add related FAQ category if available
                    if row.get('related_faq_category'):
                        st.markdown(f"""
                        <div class='result-row'>
                            <div class='result-label'>Related FAQ Category:</div>
                            <div class='result-value'>{row.get("related_faq_category", "")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Close the container
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Case Management for this inquiry
                    case_status = row.get('case_status', 'New')
                    
                    # Show case status
                    st.markdown("<div class='inquiry-section'>Case Management</div>", unsafe_allow_html=True)
                    status_color = "#64B5F6"  # Default blue
                    if case_status == "Resolved" or case_status == "Closed":
                        status_color = "#4CAF50"  # Green
                    elif case_status == "In Progress":
                        status_color = "#FFA726"  # Orange
                    elif case_status == "Awaiting Customer" or case_status == "Awaiting Tradesperson":
                        status_color = "#FFD54F"  # Amber
                    
                    st.markdown("<div class='inquiry-label'>Current Status:</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='inquiry-detail' style='color: {status_color}; font-weight: bold;'>{case_status}</div>", unsafe_allow_html=True)
                    
                    # Replace expander with a simple UI using columns and a button to toggle visibility
                    if st.button(f"📝 Update Case #{idx}", key=f"toggle_{idx}"):
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
                            from app import save_inquiries_to_file
                            save_inquiries_to_file()
                            
                            st.success(f"Case {idx} updated - Status: {selected_status}")
                            st.experimental_rerun()
                    
                    # Display existing agent notes if any
                    if row.get('agent_notes'):
                        st.markdown("<div class='inquiry-label'>Agent Notes:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail' style='white-space: pre-wrap;'>{row.get('agent_notes', '')}</div>", unsafe_allow_html=True)
    else:
        st.info("No inquiries found. Generate and classify some scenarios first.") 