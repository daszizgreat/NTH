import streamlit as st
import datetime
from pymongo import MongoClient
import pytz # Required for timezone conversions

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Document Viewer")
st.title("📄 Document Viewer & Manager")

# --- START: MONGODB MODIFICATIONS ---

# ⚠️ WARNING: Hardcoding credentials is NOT recommended for production.
# This method is suitable for local testing only.
MONGO_URI = "mongodb+srv://soumyadeepdas11sc2020_db_user:bHAVX6vEMTGIL2mo@nthofficial.qr39fql.mongodb.net/?retryWrites=true&w=majority&appName=nthofficial"

@st.cache_resource
def init_connection():
    """Initializes and returns a MongoDB client connection."""
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_documents_from_db(db_collection):
    """Fetches document details from the MongoDB collection."""
    documents_details = []
    try:
        # Fetch only the necessary fields to be efficient
        cursor = db_collection.find({}, {"filename": 1, "saved_at_utc": 1, "html_content": 1, "_id": 0})
        
        # Define the local timezone for user-friendly display
        local_tz = pytz.timezone("Asia/Kolkata")

        for doc in cursor:
            # Convert the UTC datetime from the DB to the local timezone
            saved_datetime_local = doc['saved_at_utc'].astimezone(local_tz)

            documents_details.append({
                "name": doc.get("filename", "No Filename"),
                "date": saved_datetime_local.date(), # Store as date object for filtering
                "datetime": saved_datetime_local,     # Store full datetime for sorting
                "html_content": doc.get("html_content", "<p>Error: HTML content not found.</p>")
            })
    except Exception as e:
        st.error(f"An error occurred while fetching data from the database: {e}")
    return documents_details

# --- END: MONGODB MODIFICATIONS ---


# --- Main Application ---

# Initialize connection
client = init_connection()

# Get the list of all saved annexures from the database
if client:
    db = client.nthofficial
    collection = db.certificates
    all_files = get_documents_from_db(collection)
else:
    all_files = []
    st.warning("Could not connect to the database. No documents can be displayed.")


# --- Filtering and Sorting Controls ---
with st.expander("🔍 Find Documents & Filter Results", expanded=True):
    search_col, date_col, sort_col = st.columns([2, 2, 1])

    with search_col:
        search_query = st.text_input("Search by filename", placeholder="e.g., Annexure_25EL16E6N")
    
    with date_col:
        if all_files:
            min_date = min(f['date'] for f in all_files)
        else:
            min_date = datetime.date.today() - datetime.timedelta(days=30)
        
        today = datetime.date.today()

        date_range = st.date_input(
            "Filter by creation date",
            (min_date, today),
            min_value=min_date,
            max_value=today,
            format="DD.MM.YYYY"
        )
    
    with sort_col:
        sort_order = st.selectbox(
            "Sort by",
            ("Newest first", "Oldest first"),
            label_visibility="collapsed"
        )

st.divider()

# --- Filtering and Sorting Logic ---
if all_files:
    filtered_files = all_files

    # Apply search query
    if search_query:
        filtered_files = [f for f in filtered_files if search_query.lower() in f['name'].lower()]

    # Apply date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_files = [f for f in filtered_files if start_date <= f['date'] <= end_date]
    
    # Apply sorting
    if sort_order == "Newest first":
        filtered_files.sort(key=lambda x: x['datetime'], reverse=True)
    else:
        filtered_files.sort(key=lambda x: x['datetime'])

    # --- Display Results ---
    st.header(f"Found {len(filtered_files)} matching document(s)")
    
    if not filtered_files:
        st.info("No documents match your current search and filter criteria.")
    else:
        preview_placeholder = st.empty()

        for file in filtered_files:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(file['name'])
                    st.caption(f"Saved On: {file['datetime'].strftime('%d %B %Y, %I:%M %p')}")
                
                with col2:
                    # --- START: MODIFIED BUTTON LOGIC ---
                    # The HTML content is already loaded from the database
                    html_content = file['html_content']

                    # View Button: Displays content in the placeholder
                    if st.button("👁️ View", key=f"view_{file['name']}", use_container_width=True):
                        with preview_placeholder.container(border=True):
                            st.header(f"📄 Preview: {file['name']}")
                            st.components.v1.html(html_content, height=600, scrolling=True)
                            if st.button("❌ Close Preview", key=f"close_{file['name']}"):
                                preview_placeholder.empty()

                    # Download Button
                    st.download_button(
                        label="📥 Download",
                        data=html_content,
                        file_name=file['name'],
                        mime="text/html",
                        key=f"dl_{file['name']}",
                        use_container_width=True
                    )
                    # --- END: MODIFIED BUTTON LOGIC ---
else:
    st.info("There are no documents to display from the database.")

def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()
