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
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts
import pytz


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


def display_dashboard():
    st.write("These Nuts")