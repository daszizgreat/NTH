import streamlit as st
import pymongo
from datetime import date
import base64
import os
import smtplib
from email.mime.text import MIMEText
import re  # For input validation
def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()
# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Centralized Registration",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- HELPER FUNCTIONS ---

def is_valid_email(email):
    """Checks if the email has a valid format using regex."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

def send_confirmation_email(email_id, name):
    """Sends a registration confirmation email with hardcoded credentials."""
    sender_email = 'teamnexusofficial25@gmail.com'
    sender_password = 'qkmm yqcq vqtm vmoq'

    subject = "✅ Registration Successful - Welcome to National Test House !"
    body = f"""Hi {name},

Welcome aboard!

Your registration with National test house  was successful. We are thrilled to have you as part of our community.

You can now proceed to log in.

Best regards,
National Test House Team!
"""
    message = MIMEText(body)
    message["Subject"], message["From"], message["To"] = subject, sender_email, email_id
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email_id, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send confirmation email: {e}")
        return False

# --- BACKGROUND IMAGE & CSS ---
def get_base64_image(image_path):
    """Reads an image file and returns its base64 encoded version."""
    if not os.path.exists(image_path):
        st.error(f"Image not found at path: {image_path}")
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

background_image_path = "pic4.jpg"
img_base64 = get_base64_image(background_image_path)

if img_base64:
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap');
        
        .stApp {{
            background: url("data:image/jpg;base64,{img_base64}") no-repeat center center fixed;
            background-size: cover;
        }}
        
        .main-title {{
            font-family: 'Gaegu', cursive; font-size: 3.5rem; text-align: center;
            color: black; /* This was already here, but the inline style below makes sure it applies */
            padding-bottom: 1rem;
        }}
        
        div[data-testid="stForm"], div.st-emotion-cache-1r6slb0 {{
            background-color: rgba(46, 51, 56, 0.85);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 2rem 3rem;
        }}
        
        .stTextInput label, .stDateInput label, .stSelectbox label, .st-emotion-cache-1n4k3ym p {{
            color: #FFFFFF !important; font-weight: bold;
            font-family: 'Source Code Pro', monospace; font-size: 1.1rem;
        }}
        
        .stButton>button {{
            background-color: #6c47ff; color: white; border-radius: 12px;
            border: none; padding: 12px 28px; font-weight: bold;
            transition: all 0.3s ease; display: block; margin: 1rem auto 0 auto;
            font-family: 'Source Code Pro', monospace;
        }}
        .stButton>button:hover {{
            background-color: #5837d4; box-shadow: 0 0 20px #6c47ff;
            transform: scale(1.05);
        }}
    </style>
    """, unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas11sc2020_db_user:bHAVX6vEMTGIL2mo@nthofficial.qr39fql.mongodb.net/?retryWrites=true&w=majority&appName=nthofficial"

@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB and caches it."""
    try:
        client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
        client.admin.command('ping') # Verify connection is successful
        return client
    except Exception as e:
        st.error(f"Could not connect to the database: {e}")
        return None

client = get_mongo_client()
if not client:
    st.stop() # Stops the app if database connection fails
db = client.Nth
users_collection = db.users

# --- SESSION STATE INITIALIZATION ---
if 'registration_complete' not in st.session_state:
    st.session_state.registration_complete = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'email_failed' not in st.session_state:
    st.session_state.email_failed = False

# --- PAGE LAYOUT & LOGIC ---
st.markdown('<h1 class="main-title" style="color: black;">Registration Info</h1>', unsafe_allow_html=True)

if not st.session_state.registration_complete:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.image("pic1.png", use_container_width=True)

    with col2:
        with st.form("registration_form"):
            name = st.text_input("🧑‍💼 Full Name")
            email = st.text_input("📧 Email Address")
            password = st.text_input("🔑 Create a Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            birthdate = st.date_input("🎂 Birthdate", min_value=date(1940, 1, 1), max_value=date.today())
            gender = st.selectbox("⚧️ Gender", ["Male", "Female", "Other", "Prefer not to say"])
            submitted = st.form_submit_button("🚀 Launch Profile")

        if st.button("🔑 Already have an account? Log In", use_container_width=True):
            st.switch_page("pages/1_login.py")

    if submitted:
        if not all([name, email, password, confirm_password]):
            st.warning("⚠️ Please fill out all fields.")
        elif not is_valid_email(email):
            st.warning("📧 Please enter a valid email address.")
        elif password != confirm_password:
            st.error("❌ Passwords do not match.")
        elif len(password) < 8:
            st.warning("🔑 Password must be at least 8 characters long.")
        else:
            if users_collection.find_one({"email": email}):
                st.error("❌ This email address is already registered.")
            else:
                today = date.today()
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

                user_data = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "birthdate": birthdate.isoformat(),
                    "age": age,
                    "gender": gender,
                    "created_at": today.isoformat()
                }

                try:
                    users_collection.insert_one(user_data)
                    if not send_confirmation_email(email, name):
                        st.session_state.email_failed = True
                    st.session_state.registration_complete = True
                    st.session_state.user_name = name
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred during registration: {e}")
else:
    st.balloons()
    st.success(f"✅ Welcome aboard, {st.session_state.user_name}!")
    st.info("Your registration is complete. A confirmation has been sent to your email.")
    if st.session_state.email_failed:
        st.warning("Your account was created, but we couldn't send the confirmation email.")

    if st.button("🔑 Proceed to Login", use_container_width=True):
        st.switch_page("pages/1_login.py")


