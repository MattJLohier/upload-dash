import streamlit as st
import datetime
import numpy as np
import pandas as pd
import altair as alt
from st_files_connection import FilesConnection
import hashlib
from io import BytesIO
from PIL import Image
import requests
import pytz
import openpyxl
import boto3


# URL of the image you want to use as the page icon
icon_url = "https://i.postimg.cc/Y0XLcpg7/scooper-s.png"

# Download the image
response = requests.get(icon_url)
image = Image.open(BytesIO(response.content))

# Set the Streamlit page configuration with the custom icon
st.set_page_config(
    page_title="Scooper Dashboard",
    page_icon=image,
    layout="wide",
    initial_sidebar_state="expanded"
)

def display_dashboard():
    alt.themes.enable("dark")
    st.markdown("<h1 style='text-align: left;'><span style='color: #317bd4;'>Scooper</span> Dashboard</h1>", unsafe_allow_html=True)
    st.markdown('**Welcome to Scooper Dashboard**')
    st.info('Scooper is a Python tool hosted on AWS (Lambda/S3/EC2) that uses Selenium and Pandas to scrape new product certifications and placements from official manufacturer websites.') 
    #st.markdown("---")
    st.subheader("Directory")
    st.markdown("""
    ##### Imaging Equipment 🖨️ #####
    - Printers, Multifunction Devices, Scanners, Digital Duplicators 
    ##### Computers 💻 #####
    - Laptops, Notebooks, Desktops, Tablets, Workstations
    ##### Televisions 📺 #####
    - Televisions & Set Top Boxes
    ##### Telephones ☎️ #####
    ##### Fridges 🧊 #####
    ##### Dishwashers 🧼 #####
    ##### Electric Cookware 🍳 #####
    ##### Displays 🖥️ #####
    ##### Audio/Video 🎙️ #####
    ##### Enterprise Servers 🌐 #####
    """)
    st.markdown("---")
    st.caption('Created by Matt Lohier') 
    with st.container():
        st.write("")  # Optional: Use st.empty() if you prefer no filler text at all
        linkedin_url = "https://www.linkedin.com/in/matt-lohier/"  # Change this URL to your specific LinkedIn profile or page
        personal_website_url = "https://matt-lohier.com/"  # Change this to your personal website URL
        st.markdown(f"""
        <a href="{linkedin_url}" target="_blank" style='display: inline-block; padding-right: 10px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' style='width:32px; height:32px;'>
        </a><!--
        --><a href="{personal_website_url}" target="_blank" style='display: inline-block;'>
            <img src='https://i.postimg.cc/9MbrTWL9/portfolio.png' style='width:32px; height:32px;'>
        </a>
        """, unsafe_allow_html=True)
        st.markdown('---')


def sidebar():
    st.sidebar.image("https://i.postimg.cc/XJdg0y7b/scooper-logo.png", use_column_width=True)
    st.sidebar.markdown("---")

def login(username, password):
    try:
        # Access the dictionary of usernames and hashed passwords directly
        user_passwords = st.secrets["credentials"]
        # Convert the input password to its hashed version
        input_hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # Check if the username exists and if the hashed password matches
        if user_passwords.get(username) == input_hashed_password:
            return True
    except KeyError as e:
        st.error(f"KeyError: {e} - Check your secrets.toml configuration.")
        return False
    return False
    

def display_login_form():
    # Create three columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:  # Middle column for the form
        st.markdown("""
        <center>
            <img src='https://i.postimg.cc/XJdg0y7b/scooper-logo.png' width='300'>
        </center>
        """, unsafe_allow_html=True)
        with st.form(key='login_form'):
            # Input fields for username and password
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                if login(username, password):  # Assume login is a function defined to check credentials
                    st.session_state['logged_in'] = True  # Update session state
                    st.rerun()
                else:
                    st.error("Invalid username or password")


def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        if 'page' not in st.session_state:
            st.session_state['page'] = 'home'
        
        sidebar()

        # Redirect based on the selected page
        if st.session_state['page'] == 'home':
            display_dashboard()
        elif st.session_state['page'] == 'certifications':
            display_certifications_page()  # Renamed for clarity
        elif st.session_state['page'] == 'placements':
            display_placements_page()  # Renamed for clarity
    else:
        display_login_form()


def page1():
    st.title("Page 1")
    st.write("Welcome to Page 1")
    sidebar()


# Function to upload DataFrame to S3
def upload_df_to_s3(df, bucket_name, object_name, aws_access_key, aws_secret_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    csv_buffer = df.to_csv(index=False)
    try:
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=csv_buffer)
        return f"Successfully uploaded {object_name} to {bucket_name}"
    except Exception as e:
        return f"Error uploading to S3: {str(e)}"

# Function to handle CSV files
def read_csv_with_error_handling(file):
    try:
        return pd.read_csv(file, error_bad_lines=False, warn_bad_lines=True)
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return None

# Streamlit dashboard
def display_dashboard():
    st.title("Upload DataFrames to S3")

    # File upload boxes
    file1 = st.file_uploader("Upload the first file", type=["csv", "xlsx"])
    file2 = st.file_uploader("Upload the second file", type=["csv", "xlsx"])

    # Button for uploading to S3
    upload_button = st.button("Upload to S3", disabled=not (file1 and file2))

    if upload_button:
        df1 = read_csv_with_error_handling(file1) if file1.name.endswith('.csv') else pd.read_excel(file1)
        df2 = read_csv_with_error_handling(file2) if file2.name.endswith('.csv') else pd.read_excel(file2)

        # Load credentials from Streamlit secrets
        bucket_name = st.secrets["bucket_name"]
        object_name1 = st.secrets["object_name1"]
        object_name2 = st.secrets["object_name2"]
        aws_access_key = st.secrets["aws_access_key"]
        aws_secret_key = st.secrets["aws_secret_key"]

        # Upload DataFrames to S3
        message1 = upload_df_to_s3(df1, bucket_name, object_name1, aws_access_key, aws_secret_key)
        message2 = upload_df_to_s3(df2, bucket_name, object_name2, aws_access_key, aws_secret_key)
        st.write(message1)
        st.write(message2)




if __name__ == "__main__":
    main()