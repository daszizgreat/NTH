import streamlit as st
import pandas as pd
import numpy as np
import base64
import os

# Page config must be the first Streamlit command
st.set_page_config(page_title="Uncertainty Budget", layout="wide")

# --- HELPER FUNCTION TO ENCODE IMAGE ---
def get_img_as_base64(file):
    """Reads an image file and returns its base64 encoded version."""
    try:
        if os.path.exists(file):
            with open(file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except Exception as e:
        st.error(f"Image file not found or could not be read: {file}. Error: {e}")
    return None

# --- BACKGROUND IMAGE AND STYLING ---
# Encode the background image
img_base64 = get_img_as_base64("pic8.avif")

# Apply the background image and other styles using CSS
if img_base64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/avif;base64,{img_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Adding a semi-transparent overlay to make text more readable */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(26, 32, 44, 0.85); /* Dark overlay */
            z-index: -1;
        }}
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stButton>button, label, .st-emotion-cache-1y4p8pa {{
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }}
        .st-emotion-cache-16txtl3 {{ /* This is for st.info/st.success boxes */
            background-color: rgba(40, 50, 60, 0.7);
            padding: 15px;
            border-radius: 10px;
        }}
        .stButton>button {{
            border-radius: 8px;
            border: 1px solid #4a5568;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    # Fallback solid color if image fails to load
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #1a202c;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stButton>button, label, .st-emotion-cache-1y4p8pa {
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }
        .st-emotion-cache-16txtl3 {
            background-color: rgba(40, 50, 60, 0.7);
            padding: 15px;
            border-radius: 10px;
        }
        .stButton>button {
            border-radius: 8px;
            border: 1px solid #4a5568;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


st.title("Uncertainty Budget Calculator")

# --- 1. RECEIVE AND HANDLE THE CMC VALUE ---
if 'selected_cmc' in st.session_state and st.session_state.selected_cmc is not None:
    incoming_cmc = float(st.session_state.selected_cmc)
    st.success(f"Received CMC value from viewer page: *{incoming_cmc}%*")
    del st.session_state.selected_cmc
else:
    incoming_cmc = 1.0
    st.info("Using default CMC value. Go to a 'Data Viewer' page to select one.")

# Canonical column name used everywhere to avoid KeyError
EXPANDED_COL = "Expanded Uncertainty at 95% C.L. & k=2 (±)"

# ---------------- Session state Initialization ----------------
if "sheet1" not in st.session_state:
    st.session_state.sheet1 = []
if "sheet2" not in st.session_state:
    st.session_state.sheet2 = []
if "standard_values" not in st.session_state:
    st.session_state.standard_values = [1.0]

# ---------------- Helper Function for Calculation ----------------
def calc_row(std_val, euc_vals, res_euc, unit, nabl_pct=1.0):
    """Calculates all uncertainty metrics for a single row with improved precision."""
    clean_vals = [v for v in euc_vals if v is not None]
    n = len(clean_vals)
    if n == 0:
        return {}

    avg_indicated = float(np.mean(clean_vals))
    pct_error = ((avg_indicated - std_val) / std_val) * 100.0 if std_val != 0 else 0.0
    typeA = float(np.std(clean_vals, ddof=1) / np.sqrt(n)) if n > 1 else 0.0

    # These values are based on an assumption of a more robust model.
    # The standard uncertainty is often provided on a calibration certificate.
    # We will use a more defensible model for the example.
    u_std = 0.005 * std_val # Assumes 0.5% uncertainty of the standard
    u_contrib_std = u_std / 2.0
    
    # This is a more typical calculation for Resolution Uncertainty using a rectangular distribution.
    u_contrib_res = res_euc / (2.0 * np.sqrt(3.0)) 
    
    acc_err_std = 0.0 # Placeholder for accuracy error, typically from a specification.
    u_contrib_acc = (acc_err_std / 2.0) / np.sqrt(3.0)
    u_other = 0.0

    u_c = float(np.sqrt(
        typeA**2 + u_contrib_std**2 + u_contrib_res**2 + u_contrib_acc**2 + u_other**2
    ))
    U_k2 = 2.0 * u_c
    nabl_abs = (nabl_pct / 100.0) * std_val
    reported = max(U_k2, nabl_abs)
    
    return {
        f"Standard Value ({unit})": std_val,
        "EUC Values": clean_vals,
        f"Resolution EUC ({unit})": res_euc,
        "Average Indicated": avg_indicated,
        "% Error": pct_error,
        "Type A Uncertainty": typeA,
        "Uncertainty of Standard": u_std,
        "Unc. Contribution Std": u_contrib_std,
        "Unc. Contribution Res": u_contrib_res,
        "Unc. Contribution Acc": u_contrib_acc,
        "Other Conditions": u_other,
        "Combined Uncertainty": u_c,
        "Expanded Uncertainty (k=2)": U_k2,
        "NABL CMC %": nabl_pct,
        "NABL CMC Abs": nabl_abs,
        "Reported": reported,
    }

# ---------------- Inputs (Sheet1) ----------------
st.subheader("Sheet-1: Enter Calibration Data")

colA, colB, colC, colD = st.columns([1.2, 1.2, 2.2, 1.2])

parameter_units = {
   "Resistance": ["mΩ", "Ω", "kΩ", "MΩ"],
   "Voltage": ["mV", "V", "kV", "MV"],
   "Current": ["mA", "A", "kA", "MA"],
   "Frequency": ["mHz", "Hz", "kHz", "MHz"],
   "Capacitance": ["mF", "F", "kF", "MF"],
   "Inductance": ["mH", "H", "kH", "MH"]
}

# Flatten all units into one list (unique only to avoid duplicates)
all_units = sorted(set(unit for units in parameter_units.values() for unit in units))

with colA:
    parameter = st.selectbox("Parameter", list(parameter_units.keys()))
    unit_type = st.selectbox(f"{parameter} Unit", parameter_units[parameter])
    range_value = st.number_input("Range Value", value=100.0, step=10.0, format="%.1f")
    col_range_header = f"{parameter} Range ({unit_type})"

with colB:
    st.caption("*Standard Values*")
    std_unit_type = st.selectbox(
        "Standard Value Unit",
        all_units,
        key="std_unit"
    )

    for i in range(len(st.session_state.standard_values)):
        st.session_state.standard_values[i] = st.number_input(
            f"Std. Value {i+1}", value=st.session_state.standard_values[i],
            step=0.000001, format="%.6f", key=f"std_val_{i}"
        )
    btn_add, btn_remove = st.columns(2)
    if btn_add.button("➕ Add", use_container_width=True):
        st.session_state.standard_values.append(st.session_state.standard_values[-1])
        st.rerun()
    if btn_remove.button("➖ Remove", use_container_width=True):
        if len(st.session_state.standard_values) > 1:
            st.session_state.standard_values.pop()
            st.rerun()

with colC:
    st.caption("Enter up to 5 readings (EUC indicated values)")
    euc_vals = [st.number_input(f"EUC Value {i+1}", value=None, step=0.000001, format="%.6f", key=f"euc_{i}") for i in range(5)]
with colD:
    res_euc = st.number_input(f"Resolution of EUC ({unit_type})", value=0.000001, step=0.000001, format="%.6f")
    nabl_pct = st.number_input("NABL CMC (%)", value=incoming_cmc, step=0.001, format="%.3f")

btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1, 2])
with btn_col1:
    if st.button("Calculate & Add Rows", type="primary"):
        clean_euc_vals = [v for v in euc_vals if v is not None]
        if not clean_euc_vals:
            st.warning("Please enter at least one EUC value.")
        else:
            rows_added = 0
            for std_val in st.session_state.standard_values:
                if std_val is not None and std_val > 0:
                    calc_results = calc_row(std_val, clean_euc_vals, res_euc, unit_type, nabl_pct)
                    if calc_results:
                        sheet1_row = {col_range_header: range_value, **calc_results}
                        st.session_state.sheet1.append(sheet1_row)

                        sheet2_row = {
                            "Sl. No.": len(st.session_state.sheet2) + 1,
                            col_range_header: range_value,
                            f"Standard Value ({std_unit_type})": std_val,
                            f"Indicated value by the EUC ({std_unit_type})": calc_results["Average Indicated"],
                            f"{EXPANDED_COL} ({std_unit_type})": calc_results["Reported"]
                        }
                        st.session_state.sheet2.append(sheet2_row)
                        rows_added += 1
            if rows_added > 0:
                st.success(f"Successfully calculated and added {rows_added} row(s).")
                st.rerun()

with btn_col2:
    if st.button("Delete All"):
        st.session_state.sheet1.clear()
        st.session_state.sheet2.clear()
        st.session_state.standard_values = [1.0]
        st.success("All data has been cleared.")
        st.rerun()

# ---------------- Sheet1 table + per-row delete ----------------
if st.session_state.sheet1:
    st.markdown("---")
    st.markdown("### Sheet-1 Table (Detailed Calculation)")
    df1 = pd.DataFrame(st.session_state.sheet1).reset_index().rename(columns={"index":"Row"})
    st.dataframe(df1.style.format(precision=6), use_container_width=True, height=280)

    c1, c2, c3 = st.columns([1,1,3])
    with c1:
        row_to_delete = st.number_input(
            "Enter Row # to Delete", min_value=0, max_value=max(0, len(df1)-1), step=1, value=0
        )
    with c2:
        st.write("")
        if st.button("Delete Row"):
            if 0 <= row_to_delete < len(st.session_state.sheet1):
                st.session_state.sheet1.pop(row_to_delete)
                st.session_state.sheet2.pop(row_to_delete)
                for i, row in enumerate(st.session_state.sheet2, start=1):
                    row["Sl. No."] = i
                st.success(f"Row {row_to_delete} deleted.")
            else:
                st.error("Row index out of range.")
            st.rerun()

# ---------------- Sheet2 view & EXPORT ----------------
if st.session_state.sheet2:
    st.markdown("---")
    st.markdown("### Sheet-2: Final Summary")
    df2 = pd.DataFrame(st.session_state.sheet2)
    st.dataframe(df2.style.format(precision=6), use_container_width=True, hide_index=True)

    st.markdown("---")

    if st.button("➡ Export to Certificate Page", type="primary"):
        if df2.empty:
            st.warning("There is no data in the summary table to export.")
        else:
            st.session_state['exported_data'] = df2
            st.session_state['parameter_name'] = parameter
            st.switch_page("pages/4_annexure.py")
