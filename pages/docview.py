import streamlit as st
import os
import datetime

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Document Viewer")
st.title("📄 Document Viewer & Manager")

# --- Core Functions ---

def get_saved_files(directory):
    """Scans a directory for .html files and returns their details."""
    files_details = []
    # Check if the provided absolute path exists
    if not os.path.isdir(directory):
        st.error(f"Error: The specified directory does not exist or is not a directory.")
        st.code(directory) # Display the path for easier debugging
        return files_details

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            try:
                # Get modification time and convert to a datetime object
                mod_time = os.path.getmtime(file_path)
                mod_datetime = datetime.datetime.fromtimestamp(mod_time)
                
                files_details.append({
                    "name": filename,
                    "path": file_path,
                    "date": mod_datetime.date(), # Store as date object for filtering
                    "datetime": mod_datetime # Store full datetime for sorting
                })
            except Exception as e:
                st.error(f"Could not read metadata for {filename}: {e}")
    return files_details

# --- Main Application ---

# Define the directory where files are saved
# **THIS IS THE LINE THAT WAS CHANGED**
SAVE_DIR = r"pages\previous_tests"

# Get the list of all saved annexures
all_files = get_saved_files(SAVE_DIR)

# --- Filtering and Sorting Controls ---
with st.expander("🔍 Find Documents & Filter Results", expanded=True):
    # Use columns for a more compact layout
    search_col, date_col, sort_col = st.columns([2, 2, 1])

    with search_col:
        # 1. Search by Name
        search_query = st.text_input("Search by filename", placeholder="e.g., Annexure_25EL16E6N")
    
    with date_col:
        # 2. Filter by Date
        # Set default range from the earliest file date to today
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
        # 3. Sort by Age
        sort_order = st.selectbox(
            "Sort by",
            ("Newest first", "Oldest first"),
            label_visibility="collapsed" # Hide label as context is clear
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
        # Use a placeholder for the preview area
        preview_placeholder = st.empty()

        for file in filtered_files:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(file['name'])
                    st.caption(f"Last Modified: {file['datetime'].strftime('%d %B %Y, %I:%M %p')}")
                
                with col2:
                    # Read file content once for both buttons
                    try:
                        with open(file['path'], 'r', encoding='utf-8') as f:
                            html_content = f.read()
                    except Exception as e:
                        st.error(f"Could not read {file['name']}")
                        continue

                    # View Button: Displays content in the placeholder
                    if st.button("👁️ View", key=f"view_{file['name']}", use_container_width=True):
                        with preview_placeholder.container(border=True):
                            st.header(f"📄 Preview: {file['name']}")
                            st.components.v1.html(html_content, height=600, scrolling=True)
                            # Add a close button inside the preview
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
else:
    # This message will show if the directory is empty or doesn't exist.
    st.info("There are no previously saved documents to display in the specified directory.")

def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()
