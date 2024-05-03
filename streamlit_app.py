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
    page_title="Upload",
    page_icon=image,
    layout="wide",
    initial_sidebar_state="expanded"
)


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


# Function to upload DataFrame to S3 as an Excel file
def upload_df_to_s3(df, bucket_name, object_name, aws_access_key, aws_secret_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    # Convert DataFrame to Excel file in memory
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    try:
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=excel_buffer.getvalue())
        return True, f"Successfully uploaded {object_name} to {bucket_name}"
    except Exception as e:
        return False, f"Error uploading to S3: {str(e)}"

# Function to read Excel files with error handling
def read_excel_with_error_handling(file):
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None

# Streamlit dashboard
def display_dashboard():
    st.title("Upload DataFrames to S3")

    # File upload boxes (only accepting Excel files)
    file1 = st.file_uploader("Upload the first Excel file", type=["xlsx"])
    file2 = st.file_uploader("Upload the second Excel file", type=["xlsx"])

    # To manage the spinner state
    is_loading = st.session_state.get('is_loading', False)

    # Button for uploading to S3
    if not is_loading:
        upload_button = st.button("Upload to S3", disabled=not (file1 and file2))
    else:
        upload_button = False

    if upload_button:
        st.session_state['is_loading'] = True
        with st.spinner('Uploading data...'):
            df1 = read_excel_with_error_handling(file1)
            df2 = read_excel_with_error_handling(file2)

            # Load credentials from Streamlit secrets
            bucket_name = st.secrets["bucket_name"]
            object_name1 = st.secrets["object_name1"]
            object_name2 = st.secrets["object_name2"]
            aws_access_key = st.secrets["aws_access_key"]
            aws_secret_key = st.secrets["aws_secret_key"]

            # Upload first file
            success1, message1 = upload_df_to_s3(df1, bucket_name, object_name1, aws_access_key, aws_secret_key)
            # Upload second file
            success2, message2 = upload_df_to_s3(df2, bucket_name, object_name2, aws_access_key, aws_secret_key)

            # Check upload status
            if success1 and success2:
                st.success("Both files were successfully uploaded to S3!")
            else:
                st.error("One or both files failed to upload. Check the error messages above.")
                st.write(message1)
                st.write(message2)
        
        # Set the spinner state back to False
        st.session_state['is_loading'] = False



if __name__ == "__main__":
    main()