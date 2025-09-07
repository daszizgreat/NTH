import streamlit as st
import pandas as pd
import datetime
import base64
import os
import re # Import regular expressions for parsing column names

# --- Initialize Session State ---
# Using more descriptive names for session state keys
if 'certificate_html_content' not in st.session_state:
    st.session_state.certificate_html_content = None
if 'certificate_filename' not in st.session_state:
    st.session_state.certificate_filename = None
if 'results_df_for_editing' not in st.session_state:
    st.session_state.results_df_for_editing = None
if 'file_has_been_saved' not in st.session_state:
    st.session_state.file_has_been_saved = False
if 'current_parameter' not in st.session_state:
    st.session_state.current_parameter = "Insulation Resistance" # Default value
# NEW: Add session state for units
if 'unit_range' not in st.session_state:
    st.session_state.unit_range = 'V'
if 'unit_std' not in st.session_state:
    st.session_state.unit_std = 'MΩ'


# --- Helper function to embed the header image ---
def get_image_as_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"Header image not found at '{path}'. Please ensure 'pic_header.png' is in the main directory.")
        return None

# --- DYNAMIC Certificate HTML Template ---
def get_certificate_html(data, header_img_base64, unit_range, unit_std):
    # Dynamically build the results table rows from the data
    results_rows_html = ""
    for res in data.get('calibration_results', []):
        results_rows_html += f"""
        <tr>
            <td>{res.get('sl_no', '')}</td>
            <td>{res.get('range_value', '')}</td>
            <td>{res.get('standard_value', '')}</td>
            <td>{res.get('indicated_value', ' ')}</td>
            <td>{res.get('uncertainty_value', '')}</td>
        </tr>
        """

    # This HTML structure remains largely the same, but the table part is now more robust
    return f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Calibration Certificate Annexure</title><style>body{{font-family:'Times New Roman',Times,serif;font-size:12pt;line-height:1.6;background-color:#f0f0f0;margin:0;padding:0}}.page{{background:white;width:210mm;min-height:297mm;display:block;margin:2em auto;padding:15mm;box-shadow:0 0 .5cm rgba(0,0,0,.5);box-sizing:border-box}}.header-img{{width:100%;display:block;margin-bottom:25px}}.title{{text-align:center;font-weight:bold;font-size:14pt;margin-bottom:25px;text-decoration:underline}}.details-table{{width:100%;border-collapse:collapse;margin-bottom:20px}}.details-table td{{padding:4px 0;vertical-align:top}}.details-table .label-num{{width:3%;font-weight:bold}}.details-table .label-text{{width:35%;font-weight:bold}}.details-table .colon{{width:2%;text-align:center;font-weight:bold}}.results-header{{font-weight:bold;margin-bottom:0;font-size:13pt}}.results-table{{width:100%;border-collapse:collapse;margin-top:10px;text-align:center}}.results-table th,.results-table td{{border:1px solid black;padding:6px;font-size:11pt}}.results-table th{{font-weight:bold}}.footer-notes{{margin-top:25px;font-size:10pt;line-height:1.5}}@media print{{body{{background:none}}.page{{width:auto;min-height:auto;margin:0;box-shadow:none;border:none}}@page{{size:A4;margin:15mm}}}}</style></head><body><div class="page"><img src="data:image/png;base64,{header_img_base64}" alt="Header" class="header-img"><p class="title">ANNEXURE</p><table class="details-table"><tr><td class="label-num">1.</td><td class="label-text">Date of Calibration</td><td class="colon">:</td><td>{data.get('date_of_calibration','')}</td></tr><tr><td class="label-num">2.</td><td class="label-text">Next Calibration Due</td><td class="colon">:</td><td>{data.get('next_calibration_due','')}</td></tr><tr><td class="label-num">3.</td><td class="label-text">Description of Sample</td><td class="colon">:</td><td>{data.get('description_sample','')}</td></tr><tr><td></td><td class="label-text" style="padding-left:0px">Make : {data.get('description_make','')}, Sl No.</td><td class="colon">:</td><td>{data.get('description_sl_no','')}</td></tr><tr><td class="label-num">4.</td><td class="label-text">Identification of Method Used</td><td class="colon">:</td><td>{data.get('method_used','')}</td></tr><tr><td class="label-num">5.</td><td class="label-text">Environmental Conditions</td><td class="colon">:</td><td>Temperature: {data.get('env_temp','')} &#176;C, Relative Humidity: {data.get('env_humidity','')} %</td></tr><tr><td class="label-num">6.</td><td class="label-text">Major Standards/Equipment</td><td class="colon">:</td><td>{data.get('major_standards','')}</td></tr><tr><td class="label-num">7.</td><td class="label-text">Site of Calibration</td><td class="colon">:</td><td>{data.get('site_of_calibration','')}</td></tr><tr><td class="label-num">8.</td><td class="label-text">Traceability of Measurement</td><td class="colon">:</td><td>{data.get('traceability_details','')}</td></tr><tr><td class="label-num">9.</td><td class="label-text">NTH Identification Mark on Calibration Sticker</td><td class="colon">:</td><td>{data.get('nth_id_mark','')}</td></tr></table><p class="results-header">10. Results of Calibration:</p>
    <p style="text-align:justify;margin-top:5px">As desired the sample was subjected to accuracy test of {data.get('parameter', '').lower()} with the results given below:</p>
    <table class="results-table">
        <thead>
            <tr>
                <th rowspan="2">Sl. No.</th>
                <th>{data.get('parameter', 'N/A')}</th>
                <th>Standard</th>
                <th>Indicated</th>
                <th>Expanded</th>
            </tr>
            <tr>
                <th>Range ({unit_range})</th>
                <th>Value ({unit_std})</th>
                <th>value by the<br>EUC* ({unit_std})</th>
                <th>Uncertainty at<br>95% C.L. & k=2 (±{unit_std})</th>
            </tr>
        </thead>
        <tbody>{results_rows_html}</tbody>
    </table>
    <div class="footer-notes"><p>{data.get('euc_note', '')}</p><p>The reported expanded uncertainty is at coverage factor k=2 which corresponds to a coverage probability of approximately 95% for a normal distribution.</p></div></div></body></html>
    """

# --- Main App ---
st.set_page_config(layout="wide", page_title="Annexure Generator")
st.title("Annexure Generator")
st.info("Fill in the details below to generate a calibration annexure. 📝")

# --- DYNAMICALLY PROCESS IMPORTED DATA ---
if 'exported_data' in st.session_state and not st.session_state.exported_data.empty:
    imported_df = st.session_state.exported_data.copy()
    
    if 'parameter_name' in st.session_state:
        st.session_state.current_parameter = st.session_state['parameter_name']
        del st.session_state['parameter_name']
    
    def find_col(df, keyword):
        for col in df.columns:
            if keyword in col:
                return col
        return None

    range_col = find_col(imported_df, 'Range')
    std_val_col = find_col(imported_df, 'Standard Value')
    indicated_col = find_col(imported_df, 'Indicated value')
    uncertainty_col = find_col(imported_df, 'Expanded Uncertainty')

    if all([range_col, std_val_col, indicated_col, uncertainty_col]):
        unit_range = re.search(r'\((.*?)\)', range_col).group(1) if re.search(r'\((.*?)\)', range_col) else ''
        unit_std = re.search(r'\((.*?)\)', std_val_col).group(1) if re.search(r'\((.*?)\)', std_val_col) else ''
        
        st.session_state.unit_range = unit_range
        st.session_state.unit_std = unit_std

        processed_df = pd.DataFrame({
            f'Range ({unit_range})': imported_df[range_col],
            f'Standard Value ({unit_std})': imported_df[std_val_col],
            f'Indicated Value ({unit_std})': imported_df[indicated_col],
            f'Uncertainty (±{unit_std})': imported_df[uncertainty_col]
        })
        
        st.session_state.results_df_for_editing = processed_df
    
    del st.session_state['exported_data']


# --- FORM FOR MANUAL ENTRY ---
with st.form("manual_entry_form"):
    st.header("Annexure Details")
    col1, col2 = st.columns(2)
    with col1:
        date_cal = st.date_input("**1. Date of Calibration**", datetime.date.today()); desc_sample = st.text_input("**3. Description of Sample**", "Digital Insulation Tester"); desc_make = st.text_input("**Make**", "RISHABH"); method = st.text_input("**4. Identification of Method Used**", "NTH/High Resistance/01"); temp = st.text_input("**5. Environmental Temperature (°C)**", "25+/-4"); major_std = st.text_input("**6. Major Standards/Equipment**", "Decade Megaohm Box.")
    with col2:
        date_due = st.date_input("**2. Next Calibration Due**", datetime.date(2025, 8, 20)); sl_no = st.text_input("**Serial No.**", "2411091563"); nth_mark = st.text_input("**9. NTH Identification Mark**", "25EL16E6N"); humidity = st.text_input("**Environmental Humidity (%)**", "30 - 75%"); site = st.text_input("**7. Site of Calibration**", "NTH(ER), Salt Lake, Kolkata")
    traceability = st.text_area("**8. Traceability of Measurement**", "Eazycare Technoconsure Pvt. Ltd. vide certificate no. 2408189/N038/SD/02 valid upto 13.05.2026")
    
    st.divider()
    st.header("10. Results of Calibration")
    
    if st.session_state.results_df_for_editing is not None:
        st.success("✅ Data successfully imported from the Uncertainty Calculator!")
        df_for_editor = st.session_state.results_df_for_editing
    else:
        st.info("The table is empty. Populate it manually or export data from the 'Uncertainty Calculator' page.")
        df_for_editor = pd.DataFrame({
            "Range (V)": [], "Standard Value (MΩ)": [],
            "Indicated Value (MΩ)": [], "Uncertainty (±MΩ)": []
        })

    edited_results = st.data_editor(df_for_editor, num_rows="dynamic", use_container_width=True)
    
    # --- START: MODIFIED SECTION ---
    # Added a text input for the EUC note to make it editable
    euc_note = st.text_input("**Note for EUC***", "EUC* - Equipment Under Calibration & the value mentioned above is the average of 5 readings")
    # --- END: MODIFIED SECTION ---

    st.divider()
    filename_input = st.text_input("**Filename for Download** (without .html)", "Annexure_25EL16E6N")
    submitted = st.form_submit_button("➡️ Generate & Preview Annexure")

# --- PROCESS FORM SUBMISSION ---
if submitted:
    header_img_base64 = get_image_as_base64('pic_header.png')
    if header_img_base64:
        with st.spinner("Generating your preview..."):
            form_data = {
                'date_of_calibration': date_cal.strftime('%d.%m.%Y'), 'next_calibration_due': date_due.strftime('%d.%m.%Y'),
                'description_sample': desc_sample, 'description_make': desc_make, 'description_sl_no': sl_no,
                'method_used': method, 'env_temp': temp, 'env_humidity': humidity, 'major_standards': major_std, 
                'site_of_calibration': site, 'traceability_details': traceability, 'nth_id_mark': nth_mark,
                'parameter': st.session_state.current_parameter,
                'euc_note': euc_note # Added the editable note to the form data
            }
            
            unit_range = st.session_state.get('unit_range', '')
            unit_std = st.session_state.get('unit_std', '')
            
            calibration_results = []
            
            for index, row in edited_results.iterrows():
                if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == "": continue
                
                standard_value_formatted = f"{row.iloc[1]} {unit_std}"
                indicated_value_formatted = f"{row.iloc[2]} {unit_std}"

                uncertainty_formatted = ""
                try:
                    uncertainty_float = float(row.iloc[3])
                    if uncertainty_float < 1:
                        rounded_uncertainty = f"{uncertainty_float:.4f}"
                    else:
                        rounded_uncertainty = f"{uncertainty_float:.3f}"
                    uncertainty_formatted = f"{rounded_uncertainty} {unit_std}"
                except (ValueError, TypeError):
                    uncertainty_formatted = f"{row.iloc[3]} {unit_std}"
                
                calibration_results.append({
                    'sl_no': index + 1,
                    'range_value': str(row.iloc[0]),
                    'standard_value': standard_value_formatted, 
                    'indicated_value': indicated_value_formatted,
                    'uncertainty_value': uncertainty_formatted
                })
            
            form_data['calibration_results'] = calibration_results
            
            st.session_state.certificate_html_content = get_certificate_html(form_data, header_img_base64, unit_range, unit_std)
            st.session_state.certificate_filename = filename_input
            st.session_state.file_has_been_saved = False

# --- DISPLAY PREVIEW AND FINALIZE DOCUMENT ---
if st.session_state.certificate_html_content:
    st.header("📄 Annexure Preview")
    st.components.v1.html(st.session_state.certificate_html_content, height=600, scrolling=True)
    st.divider()
    st.header("💾 Finalize Document")
    
    save_col, clear_col = st.columns(2)
    
    with save_col:
        if st.button("✅ Finalize & Save", use_container_width=True, type="primary"):
            SAVE_DIR = "previous_tests"
            os.makedirs(SAVE_DIR, exist_ok=True)
            
            file_path = os.path.join(SAVE_DIR, f"{st.session_state.certificate_filename}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(st.session_state.certificate_html_content)
            
            st.success(f"File saved to server at: `{file_path}`")
            st.session_state.file_has_been_saved = True

        if st.session_state.file_has_been_saved:
            st.download_button(
                label="⬇️ Download Annexure to Computer",
                data=st.session_state.certificate_html_content,
                file_name=f"{st.session_state.certificate_filename}.html",
                mime="text/html",
                use_container_width=True
            )

    with clear_col:
        if st.button("❌ Start New / Clear Preview", use_container_width=True):
            st.session_state.certificate_html_content = None
            st.session_state.certificate_filename = None
            st.session_state.results_df_for_editing = None
            st.session_state.file_has_been_saved = False
            st.rerun()

def hide_sidebar():
    st.markdown("""
        <style> [data-testid="stSidebar"] { display: none; } </style>
    """, unsafe_allow_html=True)

hide_sidebar()