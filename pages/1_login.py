import streamlit as st
import pymongo
import base64
import os
import smtplib
from email.mime.text import MIMEText
import time
import random

# --- OTP & EMAIL FUNCTIONS ---
def generate_otp(length=6):
    """Generates a random 6-digit OTP."""
    return ''.join(random.choice("0123456789") for _ in range(length))

def send_otp_via_email(email_id, user_name, otp):
    """Sends the OTP to the user's email address."""
    sender_email = 'teamnexusofficial25@gmail.com'  # Your email
    sender_password = 'qkmm yqcq vqtm vmoq'  # Your email app password
    subject = "Your One-Time Password (OTP) for Sign In"
    body = f"""Hello {user_name},

Your One-Time Password (OTP) to complete your sign in is:

OTP: {otp}

This password is valid for 10 minutes. Please do not share it with anyone.

Best regards,
Team Nexus
"""
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = email_id
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email_id, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send OTP email: {e}")
        return False

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Sign In",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FUNCTION TO ENCODE LOCAL IMAGE ---
def get_image_as_base64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# --- CUSTOM CSS ---
def load_css(image_path):
    base64_image = get_image_as_base64(image_path)
    background_style = f"""
        background-image: url(data:image/jpeg;base64,{base64_image});
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    """ if base64_image else "background-color: #1a1a1a;"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        .stApp {{ {background_style} }}
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 4rem; text-align: center;
            color: white; padding-bottom: 1rem;
        }}
        [data-testid="stForm"] {{
            background-color: rgba(30, 35, 40, 0.8);
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2.5rem 3.5rem;
            text-align: center;
        }}
        .stTextInput label {{
            color: #FFFFFF !important; font-weight: bold;
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem; 
        }}
        div[data-testid="stTextInput"] input {{
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem;
            text-align: center;
        }}
        [data-testid="stInfo"] {{
            text-align: center;
        }}
        .stButton>button {{
            background-image: linear-gradient(to right, #FF512F 0%, #DD2476 51%, #FF512F 100%);
            color: white; border-radius: 12px;
            border: none; padding: 15px 30px; font-weight: bold;
            transition: 0.5s; background-size: 200% auto;
            display: block; margin: 1.5rem auto 0 auto;
            font-family: 'Source Code Pro', monospace;
        }}
        .stButton>button:hover {{
            background-position: right center;
            color: #fff; text-decoration: none;
            transform: scale(1.05);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas11sc2020_db_user:bHAVX6vEMTGIL2mo@nthofficial.qr39fql.mongodb.net/?retryWrites=true&w=majority&appName=nthofficial"

@st.cache_resource
def get_mongo_client():
    try:
        client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return None
client = get_mongo_client()
if client:
    db = client.Nth
    users_collection = db.users
else:
    st.stop()

# --- Initialize Session State ---
# This state manages the multi-step login process
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = ""
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- HIDE SIDEBAR ---
def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()

# --- APP LAYOUT & LOGIC ---
IMAGE_PATH = r"pic5.jpg"
load_css(IMAGE_PATH)

st.markdown('<h1 class="main-title">Account Login</h1>', unsafe_allow_html=True)

# Step 1: Show the email and password form if OTP has not been sent yet
if not st.session_state.otp_sent:
    with st.form("login_form"):
        email = st.text_input("📧 Email Address")
        password = st.text_input("🔑 Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        if not email or not password:
            st.warning("⚠️ Please enter both your email and password.")
        else:
            # --- MODIFIED LOGIC ---
            # 🚨 SECURITY WARNING: Storing and comparing passwords in plaintext is highly insecure.
            # In a real application, you should hash passwords using a library like bcrypt.
            user_data = users_collection.find_one({"email": email, "password": password})
            
            if user_data:
                # If email and password are correct, then proceed to send OTP
                otp = generate_otp()
                user_name = user_data.get("name", "User")
                
                if send_otp_via_email(email, user_name, otp):
                    # Store details temporarily for OTP verification
                    st.session_state.otp_sent = True
                    st.session_state.otp_code = otp
                    st.session_state.user_email = email
                    st.success("✅ Password correct! An OTP has been sent to your email.")
                    st.rerun()
            else:
                st.error("❌ Invalid email or password. Please try again.")
else:
    # Step 2: Show the OTP verification form
    st.info(f"An OTP was sent to **{st.session_state.user_email}**. Please enter it below.")
    with st.form("verify_otp_form"):
        otp_input = st.text_input("🔑 Enter OTP", max_chars=6)
        verify_button = st.form_submit_button("Verify & Login")

    if verify_button:
        if otp_input == st.session_state.otp_code:
            st.success("✅ Login Successful! Redirecting...")
            st.balloons()
            
            # Store the verified email to be used on other pages
            st.session_state['logged_in_email'] = st.session_state.user_email
            
            # Clean up the temporary state variables used for the login process
            del st.session_state.otp_sent
            del st.session_state.otp_code
            del st.session_state.user_email
            
            time.sleep(2)
            st.switch_page("pages/main_home.py")
        else:
            st.error("❌ Invalid OTP. Please try again.")