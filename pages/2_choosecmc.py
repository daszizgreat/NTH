import streamlit as st
import pandas as pd
from pymongo import MongoClient
import base64
import os

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="MongoDB Data Viewer 🔎",
    page_icon="🔎",
    layout="wide",
)

# --- Background Image Setup ---
# Function to encode local image to base64
def get_base64_image(image_path):
    # Use raw string for the path to handle backslashes correctly
    if not os.path.exists(image_path):
        st.error(f"Background image not found at path: {image_path}")
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Path to your background image
BACKGROUND_IMAGE_PATH = r"C:pic4.jpg"
base64_image = get_base64_image(BACKGROUND_IMAGE_PATH)

# Inject custom CSS for background if image is found
if base64_image:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/avif;base64,{base64_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* You might want to adjust text colors for better readability on the background */
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stButton>button, .stMultiSelect label, .stNumberInput label {{
            color: white; /* Example: make text white */
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6); /* Add text shadow for better readability */
        }}
        /* Make expander background slightly transparent dark for readability */
        div.st-emotion-cache-s2s5r {{ /* Target the expander content area */
            background-color: rgba(30, 30, 30, 0.7); /* Darker transparent background */
            padding: 15px;
            border-radius: 10px;
        }}
        div.st-emotion-cache-1n4k3ym p {{ /* Target expander text content */
            color: white; /* Ensure text inside expander is white */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("🔎 Interactive MongoDB Data Viewer")
st.write("Use the filters to find the data you need, then enter the row number to send its CMC value to the calculator.")

# --- 2. MongoDB Connection ---
MONGO_CONNECTION_STRING = "mongodb+srv://soumyadeepdas11sc2020_db_user:bHAVX6vEMTGIL2mo@nthofficial.qr39fql.mongodb.net/?retryWrites=true&w=majority&appName=nthofficial"

@st.cache_resource
def get_mongo_client():
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Could not connect to MongoDB: {e}")
        return None

client = get_mongo_client()

# --- 3. Data Fetching ---
@st.cache_data(ttl=60)
def fetch_data(_client):
    if _client:
        db = _client["calibration_db"]
        collection = db["scope"]
        data = list(collection.find({}, {'_id': 0}))
        return pd.DataFrame(data)
    return pd.DataFrame()

if not client:
    st.stop()
else:
    df = fetch_data(client)

if df.empty:
    st.warning("No data found in the collection.")
    st.stop()

# --- 4. Filters (Re-added) ---
with st.expander("📊 Show / Hide Filters", expanded=True):
    COLUMNS_TO_FILTER = [
        "Nature", "Measurand or Reference", "Calibration or Measurement Method",
        "Measurement Range and Additional Parameters", "CMC (Upper Bound)"
    ]
    filters = {}
    for column in COLUMNS_TO_FILTER:
        if column in df.columns:
            unique_values = df[column].dropna().unique()
            selected_values = st.multiselect(
                label=f"Filter by {column}",
                options=sorted(unique_values),
                key=f"filter_{column}"
            )
            if selected_values:
                filters[column] = selected_values

# Apply filters
filtered_df = df.copy()
for column, selected_values in filters.items():
    filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

# --- 5. Display Data and Selection Logic (Corrected) ---
st.markdown("---")
st.header("Data Table")
st.write(f"Displaying **{len(filtered_df)}** of **{len(df)}** total records.")
# Display the dataframe with its index, which the user will need for selection
st.dataframe(filtered_df, use_container_width=True)

st.markdown("---")
st.header("Select a Row")

# Check if there's any data to select from after filtering
if not filtered_df.empty:
    # Create a number input for the user to enter the row index
    max_index = len(filtered_df) - 1
    selected_index = st.number_input(
        f"Enter the row number (0 to {max_index}) you want to use:",
        min_value=0,
        max_value=max_index,
        step=1
    )

    if st.button("Use Selected CMC and Go to Calculator"):
        try:
            # Get the data from the selected row using the index
            selected_row = filtered_df.iloc[selected_index]
            cmc_value = selected_row["CMC (Upper Bound)"]

            # Store the CMC value in the session state to share it
            st.session_state['selected_cmc'] = cmc_value

            # Switch to the calculator page
            st.switch_page("pages/3_Calculator.py")

        except (KeyError, IndexError):
            st.error("Could not retrieve the CMC value for the selected row. Please check the index and try again.")
else:
    st.warning("No data matches the current filter criteria.")


def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()