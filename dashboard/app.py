import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import datetime
import plotly.express as px
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from resume_tailor import ResumeTailor
except ImportError:
    st.error("resume_tailor.py not found. Please create it in the main folder.")
    ResumeTailor = None

# Page config
st.set_page_config(
    page_title="Chronos Talent - Job Dashboard",
    page_icon="🎯",
    layout="wide"
)

# Initialize resume tailor
@st.cache_resource
def init_resume_tailor():
    if ResumeTailor:
        return ResumeTailor()
    return None

tailor = init_resume_tailor()

# Connect to database
@st.cache_resource
def init_connection():
    return create_engine('sqlite:///chronos.db')

engine = init_connection()

# Load jobs data
@st.cache_data(ttl=600)
def load_jobs():
    try:
        query = "SELECT * FROM jobs"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Title
st.title("🎯 Chronos Talent - AI Job Mining & Resume Tailoring")
st.markdown("---")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Job Dashboard", "📄 CV Upload & Tailor", "📁 My Resumes"])

with tab1:
    try:
        df = load_jobs()
        
        if df.empty:
            st.warning("No jobs found in database. Run the miner first: python main.py")
        else:
            st.success(f"✅ Loaded {len(df)} jobs from database!")
            
            # Show available columns for debugging
            with st.expander("📋 Database Structure"):
                st.write("Available columns:", list(df.columns))
                st.dataframe(df.head(3))
            
            # Sidebar filters
            with st.sidebar:
                st.header("Job Filters")
                
                # Company filter (safely)
                if 'company' in df.columns:
                    companies = ['All'] + sorted(df['company'].dropna().unique().tolist())
                    selected_company = st.selectbox("Company", companies)
                else:
                    selected_company = 'All'
                    st.info("Company column not found")
                
                # Location filter (safely)
                if 'location' in df.columns:
                    locations = ['All'] + sorted(df['location'].dropna().unique().tolist())
                    selected_location = st.selectbox("Location", locations)
                else:
                    selected_location = 'All'
                    st.info("Location column not found")
                
                st.markdown("---")
                st.metric("Total Jobs", len(df))
            
            # Apply filters safely
            filtered_df = df.copy()
            if selected_company != 'All' and 'company' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['company'] == selected_company]
            if selected_location != 'All' and 'location' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['location'] == selected_location]
            
            # Display jobs
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📋 Available Jobs")
                
                # Determine which columns to display
                display_cols = []
                for col in ['title', 'company', 'location']:
                    if col in filtered_df.columns:
                        display_cols.append(col)
                
                if not filtered_df.empty and display_cols:
                    for idx, job in filtered_df.iterrows():
                        title = job.get('title', 'No Title')
                        company = job.get('company', 'Unknown Company')
                        expander_title = f"💼 {title}"
                        if company != 'Unknown Company':
                            expander_title += f" at {company}"
                        
                        with st.expander(expander_title):
                            if 'location' in job and pd.notna(job['location']):
                                st.write(f"**Location:** {job['location']}")
                            
                            if 'description' in job and pd.notna(job['description']):
                                st.write(f"**Description:** {job['description'][:200]}...")
                            else:
                                st.write("No description available")
                            
                            if 'url' in job and pd.notna(job['url']):
                                st.markdown(f"🔗 [Apply Here]({job['url']})")
                            
                            # Add tailor button for this job
                            if tailor:
                                if st.button(f"🎯 Tailor My Resume for this Job", key=f"tailor_{idx}"):
                                    st.session_state['selected_job'] = job.to_dict()
                                    st.session_state['active_tab'] = "CV Upload & Tailor"
                                    st.rerun()
                else:
                    st.info("No jobs to display")
            
            with col2:
                st.subheader("📊 Quick Stats")
                st.metric("Jobs Found", len(filtered_df))
                
                # Safe company count
                if 'company' in filtered_df.columns:
                    st.metric("Companies", filtered_df['company'].nunique())
                    
                    # Safe chart
                    company_counts = filtered_df['company'].value_counts().head(5)
                    if not company_counts.empty:
                        st.bar_chart(company_counts)
                else:
                    st.info("Company data not available")
    
    except Exception as e:
        st.error(f"Error in dashboard: {str(e)}")
        st.info("Check your database structure and columns")

with tab2:
    if not tailor:
        st.error("ResumeTailor not available. Check resume_tailor.py file.")
    else:
        st.header("📄 Upload Your CV for Tailoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Your Information")
            user_name = st.text_input("Your Name", key="user_name")
            target_role = st.selectbox(
                "Target Role",
                ["Sales Development Representative", "Account Executive", "BDR", "Tech Sales", "SaaS Sales"]
            )
            
            uploaded_file = st.file_uploader(
                "Upload your CV (PDF or DOCX)",
                type=['pdf', 'docx', 'txt'],
                help="Upload your current resume to get it tailored for specific jobs"
            )
            
            if uploaded_file and user_name and st.button("📤 Upload CV"):
                with st.spinner("Uploading CV..."):
                    try:
                        filename = tailor.save_uploaded_cv(uploaded_file, user_name)
                        st.success(f"✅ CV uploaded successfully!")
                        st.session_state['last_upload'] = filename
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
        
        with col2:
            st.subheader("2. Select Job to Target")
            
            # Show jobs for targeting
            df = load_jobs()
            if not df.empty:
                # Create job options safely
                job_options = []
                for idx, row in df.iterrows():
                    title = row.get('title', 'Unknown Title')
                    company = row.get('company', 'Unknown Company')
                    job_options.append(f"{title} at {company}")
                
                if job_options:
                    selected_job_display = st.selectbox("Choose a job", job_options)
                    
                    # Get selected job index
                    selected_idx = job_options.index(selected_job_display)
                    selected_job = df.iloc[selected_idx]
                    
                    if 'description' in selected_job and pd.notna(selected_job['description']):
                        st.write("**Job Description:**")
                        st.info(selected_job['description'][:300] + "...")
                    else:
                        st.write("No description available for this job")
                    
                    # Get user's resumes
                    if user_name:
                        try:
                            user_resumes = tailor.get_user_resumes(user_name)
                            if not user_resumes.empty:
                                resume_options = [f"{row['original_filename']} ({row['upload_date'][:10]})" 
                                                for idx, row in user_resumes.iterrows()]
                                selected_resume = st.selectbox("Choose your CV", resume_options)
                                
                                if st.button("🎯 Generate Tailored Resume", type="primary"):
                                    with st.spinner("AI is tailoring your resume..."):
                                        # Get resume ID
                                        resume_idx = resume_options.index(selected_resume)
                                        resume_id = user_resumes.iloc[resume_idx]['id']
                                        job_id = selected_job.get('id', idx + 1)
                                        
                                        # Tailor resume
                                        output_path = tailor.tailor_resume(resume_id, job_id)
                                        
                                        if output_path:
                                            st.success("✅ Resume tailored successfully!")
                                            try:
                                                with open(output_path, 'r', encoding='utf-8') as f:
                                                    tailored_content = f.read()
                                                
                                                st.subheader("Your Tailored Resume:")
                                                st.text_area("Preview", tailored_content, height=300)
                                                
                                                # Download button
                                                company_name = selected_job.get('company', 'Company')
                                                job_title = selected_job.get('title', 'Job')
                                                st.download_button(
                                                    label="📥 Download Tailored Resume",
                                                    data=tailored_content,
                                                    file_name=f"tailored_{company_name}_{job_title}.txt",
                                                    mime="text/plain"
                                                )
                                            except Exception as e:
                                                st.error(f"Error reading tailored resume: {e}")
                            else:
                                st.warning("No CV found. Please upload your CV first in step 1.")
                        except Exception as e:
                            st.error(f"Error getting resumes: {e}")
                else:
                    st.warning("No jobs available with proper titles")
            else:
                st.warning("No jobs available. Run the miner first.")

with tab3:
    if not tailor:
        st.error("ResumeTailor not available. Check resume_tailor.py file.")
    else:
        st.header("📁 Your Uploaded Resumes")
        
        try:
            # Show all resumes
            resumes_df = tailor.get_user_resumes()
            
            if not resumes_df.empty:
                display_cols = []
                for col in ['user_name', 'original_filename', 'upload_date']:
                    if col in resumes_df.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        resumes_df[display_cols],
                        use_container_width=True
                    )
                
                # Show tailored resumes folder
                st.subheader("📂 Tailored Resumes")
                if os.path.exists('tailored_resumes'):
                    tailored_files = os.listdir('tailored_resumes')
                    
                    if tailored_files:
                        selected_tailored = st.selectbox("Select a tailored resume", tailored_files)
                        if selected_tailored:
                            file_path = os.path.join('tailored_resumes', selected_tailored)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                st.text_area("Resume Content", content, height=300)
                            except Exception as e:
                                st.error(f"Error reading file: {e}")
                    else:
                        st.info("No tailored resumes yet. Use the CV Upload tab to create one!")
                else:
                    st.info("Tailored resumes folder not found")
            else:
                st.info("No resumes uploaded yet.")
        except Exception as e:
            st.error(f"Error loading resumes: {e}")

# Footer
st.markdown("---")
st.markdown("🚀 **Chronos Talent** - AI-Powered Job Mining & Resume Tailoring System")