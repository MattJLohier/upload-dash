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

def merge_in_chunks(file_pivot, file_report, output_file, progress=None, chunk_size=10000):
    df_report = pd.read_excel(file_report, sheet_name="Product Details", header=5)
    df_report.set_index("Product", inplace=True)

    temp_csv = io.StringIO()
    df_pivot_table = pd.read_excel(file_pivot, sheet_name="Product & Pricing Pivot Data", header=3)
    df_pivot_table.to_csv(temp_csv, index=False)
    temp_csv.seek(0)

    total_chunks = sum(1 for _ in pd.read_csv(temp_csv, chunksize=chunk_size))
    temp_csv.seek(0)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for i, chunk in enumerate(pd.read_csv(temp_csv, chunksize=chunk_size)):
            chunk.set_index("Product", inplace=True)
            merged_chunk = chunk.join(df_report, how='inner', lsuffix='_pivot', rsuffix='_report')
            merged_chunk.reset_index(inplace=True)
            startrow = i * chunk_size
            merged_chunk.to_excel(writer, index=False, startrow=startrow, header=(i == 0))

            if progress:
                progress.progress((i + 1) / total_chunks)

def display_dashboard():
    st.title("Upload Excel Files to S3")

    file1 = st.file_uploader("Upload the first Excel file", type=["xlsx"])
    file2 = st.file_uploader("Upload the second Excel file", type=["xlsx"])

    is_loading = st.session_state.get('is_loading', False)

    if not is_loading:
        upload_button = st.button("Process and Upload to S3", disabled=not (file1 and file2))
    else:
        upload_button = False

    if upload_button:
        st.session_state['is_loading'] = True

        progress = st.progress(0)

        with st.spinner('Processing data...'):
            file_pivot = file1 if "PivotTable" in file1.name else file2
            file_report = file1 if file_pivot != file1 else file2

            output = io.BytesIO()
            merge_in_chunks(file_pivot, file_report, output, progress)

            bucket_name = st.secrets["bucket_name"]
            merged_object_name = "Merged_Data.xlsx"
            aws_access_key = st.secrets["aws_access_key"]
            aws_secret_key = st.secrets["aws_secret_key"]
            
            st.write("Uploading Combined Data")
            
            output.seek(0)
            success, message = upload_file_to_s3(output.getvalue(), bucket_name, merged_object_name, aws_access_key, aws_secret_key)

            if success:
                st.success("Merged data file was successfully uploaded to S3!")
            else:
                st.error("Failed to upload merged data to S3.")
                st.write(message)
        
        st.session_state['is_loading'] = False



if __name__ == "__main__":
    main()