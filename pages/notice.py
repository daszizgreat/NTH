import streamlit as st
import pymongo
import certifi
import datetime
import time

# --- PAGE CONFIGURATION ---
# The theme is now permanently set to "light" in the .streamlit/config.toml file.
st.set_page_config(
    page_title="Create Notice",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- AUTHENTICATION CHECK ---
if 'logged_in_email' not in st.session_state or not st.session_state['logged_in_email']:
    st.warning("⚠️ Please log in first to create a notice.")
    st.page_link("1_login_page.py", label="Go to Login Page", icon="🏠")
    st.stop()

# --- MONGODB CONNECTION ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas11sc2020_db_user:bHAVX6vEMTGIL2mo@nthofficial.qr39fql.mongodb.net/?retryWrites=true&w=majority&appName=nthofficial"
DB_NAME = "Nth"

@st.cache_resource
def get_mongo_client():
    """Establishes a cached connection to MongoDB."""
    try:
        client = pymongo.MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return None

client = get_mongo_client()

if not client:
    st.stop()

db = client[DB_NAME]
users_collection = db.users
notices_collection = db.notices

# --- FETCH CURRENT USER DATA ---
logged_in_email = st.session_state['logged_in_email']
user_data = users_collection.find_one({"email": logged_in_email})
user_name = user_data.get("name", "Unknown User")

# --- SIDEBAR ---
with st.sidebar:
    st.success(f"Logged in as:\n**{user_name}**")
    if st.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.page_link("1_login_page.py", label="Logged out. Go to Login Page.", icon="🏠")
        st.rerun()

# --- PAGE TITLE AND FORM ---
st.title("📝 Create a New Notice")
st.markdown("Use this page to post a new text or PDF notice for the team.")

with st.form("new_notice_form", clear_on_submit=True):
    notice_type = st.radio(
        "1. Select Notice Type:",
        ("Text Message", "PDF Document"),
        horizontal=True
    )
    
    title = st.text_input("2. Notice Title*", placeholder="e.g., Quarterly Performance Review Schedule")
    
    content = None
    pdf_file = None

    if notice_type == "Text Message":
        content = st.text_area("3. Message Content*", height=250, placeholder="Enter all the details of your notice here...")
    else: # PDF Document
        pdf_file = st.file_uploader(
            "3. Upload PDF Document*",
            type="pdf",
            help="Upload a notice in PDF format. The maximum file size is 16MB."
        )

    is_urgent = st.checkbox("🚨 Mark as Urgent")
    
    submitted = st.form_submit_button("Post This Notice")

    if submitted:
        is_valid = True
        if not title:
            st.warning("⚠️ Please provide a title for the notice.")
            is_valid = False
        
        if notice_type == "Text Message" and not content:
            st.warning("⚠️ Please enter a message for the notice.")
            is_valid = False
            
        if notice_type == "PDF Document" and not pdf_file:
            st.warning("⚠️ Please upload a PDF file for the notice.")
            is_valid = False

        if is_valid:
            try:
                notice_document = {
                    "title": title,
                    "type": "message" if notice_type == "Text Message" else "pdf",
                    "author_email": logged_in_email,
                    "author_name": user_name,
                    "timestamp": datetime.datetime.now(),
                    "is_urgent": is_urgent
                }
                
                if notice_type == "Text Message":
                    notice_document["content"] = content
                    notices_collection.insert_one(notice_document)
                    st.success("✅ Text notice posted successfully!")
                
                elif notice_type == "PDF Document":
                    pdf_bytes = pdf_file.getvalue()
                    if len(pdf_bytes) > 16 * 1024 * 1024:
                        st.error("❌ File size exceeds the 16MB limit. Please upload a smaller file.")
                    else:
                        notice_document["filename"] = pdf_file.name
                        notice_document["file_data"] = pdf_bytes
                        notices_collection.insert_one(notice_document)
                        st.success("✅ PDF notice uploaded successfully!")

                time.sleep(1.5)
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred while saving the notice: {e}")
def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()