import streamlit as st
import pymongo
import certifi

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Main Home",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTHENTICATION CHECK ---
if 'logged_in_email' not in st.session_state or not st.session_state['logged_in_email']:
    st.warning("⚠️ Please log in first to access this page.")
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

# --- FETCH USER DATA ---
logged_in_email = st.session_state['logged_in_email']
user_data = users_collection.find_one({"email": logged_in_email})
if not user_data:
    st.error("Could not find user data. Please log in again.")
    st.page_link("1_login_page.py", label="Go to Login Page")
    st.stop()
user_name = user_data.get("name", user_data.get("username", logged_in_email))

# --- SIDEBAR ---
with st.sidebar:
    st.success(f"Logged in as:\n**{user_name}**")
    st.markdown(f"({logged_in_email})")
    
    if st.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.page_link("1_login_page.py", label="Logged out. Go to Login Page.", icon="🏠")
        st.rerun()

# --- MAIN PAGE LAYOUT ---
st.title(f"Welcome, {user_name}!")
st.markdown("---")

# 1. Navigation Section
st.header("📄 Navigation")
st.markdown("Select a page to continue your work.")
col1, col2 = st.columns(2)

with col1:
    if st.button("📈 Choose CMC", use_container_width=True):
        st.info("Navigating to Choose CMC page...")
        st.switch_page("pages/2_choosecmc.py")

    if st.button("📢 Post/View Notices", use_container_width=True):
        st.info("Navigating to the Notices page...")
        st.switch_page("pages/notice.py")

with col2:
    if st.button("📂 View Documents", use_container_width=True):
        st.info("Navigating to Document Viewer...")
        st.switch_page("pages/docview.py")

    if st.button("✔️ Tasks", use_container_width=True):
        st.info("Navigating to the Tasks page...")
        st.switch_page("pages/tasks.py")

st.markdown("---")

# 2. Recent Notices Section (MODIFIED)
st.header("📜 Recent Notices")

# Fetch the 5 most recent notices, sorted by timestamp
latest_notices = list(notices_collection.find().sort("timestamp", -1).limit(5))

if not latest_notices:
    st.info("No notices have been posted yet.")
else:
    for notice in latest_notices:
        notice_col1, notice_col2 = st.columns([4, 1])
        with notice_col1:
            # --- MODIFIED: Use red color for urgent notice titles ---
            if notice.get('is_urgent'):
                st.markdown(f"<h3 style='color: #FF4B4B;'>🚨 {notice['title']}</h3>", unsafe_allow_html=True)
            else:
                st.subheader(notice['title'])
            
            # Display content or download button based on type
            if notice['type'] == 'message':
                st.write(notice.get('content', '*No content*'))
            elif notice['type'] == 'pdf':
                st.download_button(
                    label=f"📄 Download {notice.get('filename', 'PDF')}",
                    data=notice['file_data'],
                    file_name=notice.get('filename', 'notice.pdf'),
                    mime='application/pdf'
                )
        with notice_col2:
            st.markdown(f"""
            <div style="text-align: right;">
                <small>Posted by: <b>{notice.get('author_name', 'N/A')}</b></small><br>
                <small>{notice['timestamp'].strftime('%d %b %Y, %I:%M %p')}</small>
            </div>
            """, unsafe_allow_html=True)
        st.divider()

def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()        