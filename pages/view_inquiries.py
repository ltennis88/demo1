import streamlit as st
import pandas as pd
import json
from app import find_relevant_faq, generate_response_suggestion, df_faq, save_inquiries_to_file

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
            
            # Classification summary section
            st.markdown("<div class='inquiry-section'>Classification Summary</div>", unsafe_allow_html=True)
            
            if recent_row['classification']:
                st.markdown("<div class='inquiry-label'>Classification:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['classification']}</div>", unsafe_allow_html=True)
            
            if recent_row['priority']:
                st.markdown("<div class='inquiry-label'>Priority:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['priority']}</div>", unsafe_allow_html=True)
            
            if recent_row['summary']:
                st.markdown("<div class='inquiry-label'>Summary:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{recent_row['summary']}</div>", unsafe_allow_html=True)
            
            # Add FAQ suggestion and response suggestion
            st.markdown("<div class='inquiry-section'>Assistance Information</div>", unsafe_allow_html=True)
            
            # First search for relevant FAQ
            faq_category = ""
            # Try to parse the classification result to get related_faq_category
            try:
                # Check if we can find something related to faq_category in the summary
                if "faq" in recent_row['summary'].lower():
                    faq_category = recent_row['summary'].lower().split("faq")[1].strip().strip(".:,")
            except:
                pass
                
            relevant_faq, faq_score = find_relevant_faq(recent_row['scenario_text'], df_faq)
            
            # Only display FAQ if it meets the relevance threshold
            if relevant_faq and faq_score >= 3:
                st.markdown("<div class='inquiry-label'>Suggested FAQ:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail'>{relevant_faq}</div>", unsafe_allow_html=True)
            
            # Generate response suggestion for email or whatsapp
            inbound_route = recent_row['inbound_route']
            if inbound_route in ["email", "whatsapp"]:
                # Recreate scenario structure from row data
                scenario_dict = {
                    "inbound_route": recent_row['inbound_route'],
                    "scenario_text": recent_row['scenario_text'],
                    "user_type": recent_row['user_type'],
                    "account_details": {
                        "name": recent_row['account_name'],
                        "location": recent_row['account_location'],
                        "latest_reviews": recent_row['account_reviews'],
                        "latest_jobs": recent_row['account_jobs'],
                        "project_cost": recent_row['project_cost'],
                        "payment_status": recent_row['payment_status']
                    }
                }
                
                # Recreate classification structure
                classification_dict = {
                    "classification": recent_row['classification'],
                    "priority": recent_row['priority'],
                    "summary": recent_row['summary']
                }
                
                response_suggestion = generate_response_suggestion(scenario_dict, classification_dict)
                
                st.markdown(f"<div class='inquiry-label'>Suggested {inbound_route.capitalize()} Response:</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='inquiry-detail' style='white-space: pre-wrap;'>{response_suggestion}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
        
        # Show previous inquiries in a collapsible expander
        if len(df) > 1:
            with st.expander("See More Inquiries"):
                # Show the rest of the inquiries (excluding the most recent one)
                for idx, row in df.iloc[1:].iterrows():
                    # Use a header for each inquiry instead of a nested expander
                    st.markdown(f"<div style='font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;'>Inquiry #{idx} - {row['classification']} (Priority: {row['priority']})</div>", unsafe_allow_html=True)
                    st.markdown("<div class='info-container'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='inquiry-label'>Timestamp:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['timestamp']}</div>", unsafe_allow_html=True)
                        
                        if row['inbound_route']:
                            st.markdown("<div class='inquiry-label'>Inbound Route:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['inbound_route']}</div>", unsafe_allow_html=True)
                        
                        if row['ivr_flow']:
                            st.markdown("<div class='inquiry-label'>IVR Flow:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['ivr_flow']}</div>", unsafe_allow_html=True)
                        
                        if row['ivr_selections']:
                            st.markdown("<div class='inquiry-label'>IVR Selections:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['ivr_selections']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        if row['user_type']:
                            st.markdown("<div class='inquiry-label'>User Type:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['user_type']}</div>", unsafe_allow_html=True)
                        
                        if row['phone_email']:
                            st.markdown("<div class='inquiry-label'>Phone/Email:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['phone_email']}</div>", unsafe_allow_html=True)
                        
                        if row['membership_id']:
                            st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['membership_id']}</div>", unsafe_allow_html=True)
                    
                    # Account details section - only show if there's actual account info
                    has_account_info = (row['account_name'] or row['account_location'] or 
                                       row['account_reviews'] or row['account_jobs'] or
                                       row['membership_id'])
                    
                    if has_account_info:
                        st.markdown("<div class='inquiry-section'>Account Details</div>", unsafe_allow_html=True)
                        
                        if row['account_name']:
                            st.markdown("<div class='inquiry-label'>Name:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['account_name']}</div>", unsafe_allow_html=True)
                        
                        if row['membership_id']:
                            st.markdown("<div class='inquiry-label'>Membership ID:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['membership_id']}</div>", unsafe_allow_html=True)
                        
                        if row['account_location']:
                            st.markdown("<div class='inquiry-label'>Location:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['account_location']}</div>", unsafe_allow_html=True)
                        
                        if row['account_reviews']:
                            st.markdown("<div class='inquiry-label'>Latest Reviews:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['account_reviews']}</div>", unsafe_allow_html=True)
                        
                        if row['account_jobs']:
                            st.markdown("<div class='inquiry-label'>Latest Jobs:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>{row['account_jobs']}</div>", unsafe_allow_html=True)
                        
                        # Show project cost and payment status side by side if available
                        if row['project_cost'] or row['payment_status']:
                            st.markdown("<div class='inquiry-label'>Project Details:</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='inquiry-detail'>Project Cost: {row['project_cost']} &nbsp;&nbsp;&nbsp; Status: {row['payment_status']}</div>", unsafe_allow_html=True)
                    
                    # Scenario text section
                    if row['scenario_text']:
                        st.markdown("<div class='inquiry-section'>Scenario Text</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['scenario_text']}</div>", unsafe_allow_html=True)
                    
                    # Classification summary section
                    st.markdown("<div class='inquiry-section'>Classification Summary</div>", unsafe_allow_html=True)
                    
                    if row['classification']:
                        st.markdown("<div class='inquiry-label'>Classification:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['classification']}</div>", unsafe_allow_html=True)
                    
                    if row['priority']:
                        st.markdown("<div class='inquiry-label'>Priority:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['priority']}</div>", unsafe_allow_html=True)
                    
                    if row['summary']:
                        st.markdown("<div class='inquiry-label'>Summary:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{row['summary']}</div>", unsafe_allow_html=True)
                    
                    # Add FAQ suggestion
                    relevant_faq, faq_score = find_relevant_faq(row['scenario_text'], df_faq)
                    
                    # Only display FAQ if it meets the relevance threshold
                    if relevant_faq and faq_score >= 3:
                        st.markdown("<div class='inquiry-section'>Assistance Information</div>", unsafe_allow_html=True)
                        st.markdown("<div class='inquiry-label'>Suggested FAQ:</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='inquiry-detail'>{relevant_faq}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)  # Close info-container div
        
        # Data export controls
        st.subheader("Data Exports")
        if len(df) > 0:
            csv_data = df.to_csv(index=False)
            st.download_button("Download CSV", data=csv_data, file_name="inquiries.csv", mime="text/csv", key="inquiries_csv_download")
            
            json_data = df.to_json(orient="records")
            st.download_button("Download JSON", data=json_data, file_name="inquiries.json", mime="application/json", key="inquiries_json_download")
    else:
        st.info("No inquiries found. Generate and classify some scenarios first.")

def show_inquiries_content():
    """
    Display the View Inquiries content without the page title
    for use within the main app.py page
    """
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