#!/usr/bin/env python3
"""
Chronos Talent - Main Program
"""

import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Chronos Talent Job Board",
    page_icon="🎯",
    layout="wide"
)

# Debug: Show database count
conn = sqlite3.connect('chronos.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM jobs")
count = cursor.fetchone()[0]
conn.close()

st.sidebar.success(f"📊 Database: {count} jobs loaded")

# Main title
st.title("🎯 Chronos Talent Job Board")
st.markdown("Find your next opportunity in tech")

# Load jobs from database
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_jobs():
    conn = sqlite3.connect('chronos.db')
    query = """
    SELECT 
        title,
        company,
        location,
        salary_range as salary,
        description,
        job_url as url,
        posted_date,
        is_applied
    FROM jobs 
    ORDER BY posted_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Load the data
df = load_jobs()

# Sidebar filters
st.sidebar.header("🔍 Filter Jobs")

# Company filter
companies = ['All'] + sorted(df['company'].unique().tolist())
selected_company = st.sidebar.selectbox("Company", companies)

# Location filter
locations = ['All'] + sorted(df['location'].unique().tolist())
selected_location = st.sidebar.selectbox("Location", locations)

# Filter logic
filtered_df = df.copy()
if selected_company != 'All':
    filtered_df = filtered_df[filtered_df['company'] == selected_company]
if selected_location != 'All':
    filtered_df = filtered_df[filtered_df['location'] == selected_location]

# Show stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Jobs", len(filtered_df))
with col2:
    st.metric("Companies", filtered_df['company'].nunique())
with col3:
    st.metric("Locations", filtered_df['location'].nunique())

# Display jobs
for idx, job in filtered_df.iterrows():
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(job['title'])
            st.markdown(f"**{job['company']}** • {job['location']}")
            if job['salary']:
                st.markdown(f"💰 {job['salary']}")
            st.markdown(job['description'][:200] + "..." if len(job['description']) > 200 else job['description'])
            
        with col2:
            st.markdown(f"📅 {job['posted_date']}")
            if job['url']:
                st.link_button("✅ Apply on WhatsApp", job['url'], use_container_width=True)
            else:
                st.button("Apply", disabled=True, use_container_width=True)

# Command-line functionality (when run directly)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "mine":
        print("🚀 Starting Chronos Talent mining mode...")
        from scrapers.linkedin_scraper import LinkedInScraper
        from database import SessionLocal, Job
        
        def mine_jobs():
            """Find new jobs"""
            print("\n" + "="*50)
            print("🤖 CHRONOS TALENT - JOB MINING")
            print("="*50)
            
            scraper = LinkedInScraper()
            
            try:
                jobs_found = scraper.search_jobs()
                
                session = SessionLocal()
                total_jobs = session.query(Job).count()
                pending = session.query(Job).filter_by(is_applied=False).count()
                session.close()
                
                print("\n" + "="*50)
                print("📊 SUMMARY")
                print("="*50)
                print(f"✅ New jobs found: {jobs_found}")
                print(f"📁 Total jobs in database: {total_jobs}")
                print(f"⏳ Pending applications: {pending}")
                print("="*50 + "\n")
                
            finally:
                scraper.close()
        
        mine_jobs()