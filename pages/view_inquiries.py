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
            
            # Account details section
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
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Show previous inquiries
        if len(df) > 1:
            st.subheader("Previous Inquiries")
            with st.expander("See More Inquiries", expanded=True):
                for idx, row in df.iloc[1:].iterrows():
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
                    
                    # Display relevant data
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No inquiries found. Generate and classify some scenarios first.") 