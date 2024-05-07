import streamlit as st
import datetime
import numpy as np
import pandas as pd
import altair as alt
from st_files_connection import FilesConnection
import hashlib
from io import BytesIO
import io
from PIL import Image
import requests
import pytz
import openpyxl
import boto3
import warnings


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



# Function to upload a file to S3
def upload_file_to_s3(file_content, bucket_name, object_name, aws_access_key, aws_secret_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    try:
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)
        return True, f"Successfully uploaded {object_name} to {bucket_name}"
    except Exception as e:
        return False, f"Error uploading to S3: {str(e)}"

def call_lambda_merge(input_bucket, pivot_file_key, report_file_key, output_bucket, output_file_key):
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    payload = {
        "input_bucket": input_bucket,
        "pivot_file_key": pivot_file_key,
        "report_file_key": report_file_key,
        "output_bucket": output_bucket,
        "output_file_key": output_file_key
    }
    response = lambda_client.invoke(
        FunctionName='quicksight-consolidator',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    response_from_lambda = json.load(response['Payload'])
    return response_from_lambda


def display_dashboard():
    st.title("Upload Excel Files to S3")

    file1 = st.file_uploader("Upload the first Excel file", type=["xlsx"])
    file2 = st.file_uploader("Upload the second Excel file", type=["xlsx"])

    if st.button("Process and Upload to S3", disabled=not (file1 and file2)):
        with st.spinner('Uploading files to S3...'):
            bucket_name = st.secrets["bucket_name"]
            aws_access_key = st.secrets["aws_access_key"]
            aws_secret_key = st.secrets["aws_secret_key"]

            file_pivot = file1 if "PivotTable" in file1.name else file2
            file_report = file1 if file_pivot != file1 else file2
            
            pivot_key = "pivot_data.xlsx"
            report_key = "report_data.xlsx"
            output_key = "merged_data.xlsx"
            
            # Upload files
            upload_file_to_s3(file_pivot.getvalue(), bucket_name, pivot_key, aws_access_key, aws_secret_key)
            upload_file_to_s3(file_report.getvalue(), bucket_name, report_key, aws_access_key, aws_secret_key)

            # Call Lambda
            response = call_lambda_merge(bucket_name, pivot_key, report_key, bucket_name, output_key)
            st.success(f"Lambda function executed: {response['body']}")

            # Optionally, you can provide a link to download the merged file or notify that it is available in S3
            st.markdown(f"**Merged file available in S3:** {bucket_name}/{output_key}")

st.session_state['is_loading'] = False


if __name__ == "__main__":
    main()