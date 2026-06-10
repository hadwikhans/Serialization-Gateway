import streamlit as st
import pandas as pd
import os
from file_reader import FileReader
from datetime import datetime
import json

# Configure page
st.set_page_config(
    page_title="EPCIS Generator",
    page_icon="📋",
    layout="wide"
)

countries = {
    "AL (Albania)": "AL",
    "AR (Argentina)": "AR",
    "AM (Armenia)": "AM",
    "AU (Australia)": "AU",
    "AT (Austria)": "AT",
    "AZ (Azerbaijan)": "AZ",
    "BY (Belarus)": "BY",
    "BE (Belgium)": "BE",
    "BR (Brazil)": "BR",
    "BG (Bulgaria)": "BG",
    "CA (Canada)": "CA",
    "CL (Chile)": "CL",
    "CN (China)": "CN",
    "CO (Colombia)": "CO",
    "HR (Croatia)": "HR",
    "CZ (Czech Republic)": "CZ",
    "DK (Denmark)": "DK",
    "EG (Egypt)": "EG",
    "EE (Estonia)": "EE",
    "FI (Finland)": "FI",
    "FR (France)": "FR",
    "DE (Germany)": "DE",
    "GR (Greece)": "GR",
    "HK (Hong Kong)": "HK",
    "HU (Hungary)": "HU",
    "IS (Iceland)": "IS",
    "IN (India)": "IN",
    "ID (Indonesia)": "ID",
    "IR (Iran)": "IR",
    "IE (Ireland)": "IE",
    "IL (Israel)": "IL",
    "IT (Italy)": "IT",
    "JP (Japan)": "JP",
    "KZ (Kazakhstan)": "KZ",
    "KE (Kenya)": "KE",
    "KG (Kyrgyzstan)": "KG",
    "LV (Latvia)": "LV",
    "LT (Lithuania)": "LT",
    "LU (Luxembourg)": "LU",
    "MY (Malaysia)": "MY",
    "MT (Malta)": "MT",
    "MX (Mexico)": "MX",
    "MD (Moldova)": "MD",
    "NL (Netherlands)": "NL",
    "NZ (New Zealand)": "NZ",
    "NG (Nigeria)": "NG",
    "NO (Norway)": "NO",
    "PK (Pakistan)": "PK",
    "PE (Peru)": "PE",
    "PH (Philippines)": "PH",
    "PL (Poland)": "PL",
    "PT (Portugal)": "PT",
    "CY (Republic of Cyprus)": "CY",
    "KR (Republic of Korea)": "KR",
    "RO (Romania)": "RO",
    "RU (Russia)": "RU",
    "SA (Saudi Arabia)": "SA",
    "SG (Singapore)": "SG",
    "SK (Slovakia)": "SK",
    "SL (Slovenia)": "SL",
    "ZA (South Africa)": "ZA",
    "ES (Spain)": "ES",
    "LK (Sri Lanka)": "LK",
    "SE (Sweden)": "SE",
    "CH (Switzerland)": "CH",
    "TW (Taiwan)": "TW",
    "TJ (Tajikistan)": "TJ",
    "TZ (Tanzania)": "TZ",
    "TH (Thailand)": "TH",
    "TN (Tunisia)": "TN",
    "TR (Turkey)": "TR",
    "TM (Turkmenistan)": "TM",
    "UA (Ukraine)": "UA",
    "AE (United Arab Emirates)": "AE",
    "GB (United Kingdom)": "GB",
    "US (United States)": "US",
    "UY (Uruguay)": "UY",
    "UZ (Uzbekistan)": "UZ",
    "VE (Venezuela)": "VE",
    "VN (Vietnam)": "VN",
}

item_code_types = (
    "AT - PZN",
    "BE - APB Code",
    "BG - Bulgaria Serial Number",
    "BR - Anvisa Registration Number",
    "CA - DIN",
    "CH - SwissMedic",
    "CN - Drug Standard Code",
    "CN - National Drug Code",
    "CN - Subtype Code",
    "DE - PPN",
    "DE - PZN",
    "EAN13",
    "ES - Codigo National",
    "FR - CIP 13 code",
    "GR - EOF Code",
    "HR - Croatia National Code",
    "IN - Product Code",
    "Internal Material Code",
    "IT - Bollino",
    "KR - KFDA Code",
    "LU - Luxembourg National Number",
    "NIE",
    "NL - KNMP",
    "NRD - Nordic VNR Drug Code",
    "PT - AIM number",
    "SA - Saudi Drug Code",
    "SUKL - Czech Republic Code",
    "UK - AMPP",
    "US - NDC442",
    "US - NDC532",
    "US - NDC541",
    "US - NDC542",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .nav-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .step-completed {
        color: #28a745;
        font-weight: bold;
    }
    
    .step-current {
        color: #007bff;
        font-weight: bold;
        background-color: #e3f2fd;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
    }
    
    .step-locked {
        color: #6c757d;
    }
    
    .module-card {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: white;
    }
    
    .module-completed {
        border-left: 4px solid #28a745;
        background-color: #f8fff9;
    }
    
    .module-available {
        border-left: 4px solid #007bff;
    }
    
    .module-locked {
        border-left: 4px solid #6c757d;
        background-color: #f8f9fa;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "basic_info"

    if 'basic_data_completed' not in st.session_state:
        st.session_state.basic_data_completed = False

    if 'completed_modules' not in st.session_state:
        st.session_state.completed_modules = set()

    if 'basic_data' not in st.session_state:
        st.session_state.basic_data = {}
        
    # Initialize module data structures consistently
    if 'SNI_data' not in st.session_state:
        st.session_state.SNI_data = {
            'enabled': False,
            'commissioning': {},
            'aggregation': [],
            'disaggregation': [],
            'update': {}
        }
        
    if 'SPO_data' not in st.session_state:
        st.session_state.SPO_data = {
            'enabled': False,
            'decommissioning': {},
            'destruction': {},
            'sampling': {},
            'status_update': {}
        }
        
    if 'WHD_data' not in st.session_state:
        st.session_state.WHD_data = {
            'enabled': False,
            'inbound': {},
            'outbound': {}
        }
        
    if 'BPM_data' not in st.session_state:
        st.session_state.BPM_data = {
            'enabled': False,
            'reopen_lot': {},
            'end_of_lot': {}
        }
        
    if 'input_json_saved' not in st.session_state:
        st.session_state.input_json_saved = False
        
    if 'last_input_json_path' not in st.session_state:
        st.session_state.last_input_json_path = None

def debug_session_state():
    """Debug function to show current session state"""
    if st.secrets.get("debug_mode", False):
        with st.expander("🔍 Debug: Session State"):
            st.write("Current Step:", st.session_state.current_step)
            st.write("Basic Data Completed:", st.session_state.basic_data_completed)
            st.write("Completed Modules:", list(st.session_state.completed_modules))
            st.write("SNI Data Enabled:", st.session_state.SNI_data.get('enabled', False))
            st.write("SPO Data Enabled:", st.session_state.SPO_data.get('enabled', False))
            st.write("WHD Data Enabled:", st.session_state.WHD_data.get('enabled', False))

def auto_save_form_data():
    """Auto-save current form data to session state to prevent data loss"""
    # This function ensures that any widget changes are preserved
    # Streamlit automatically handles this through keys and session state
    pass
            
init_session_state()

# Define workflow steps
WORKFLOW_STEPS = {
    "basic_info": {
        "title": "📋 Basic Information",
        "description": "Collect essential data",
        "required": True
    },
    "SNI": {
        "title": "🔄 Serial Number Interchange",
        "description": "Manage serial number operations",
        "required": False
    },
    "SPO": {
        "title": "📊 Serial Post Operations",
        "description": "Post Serial Operations",
        "required": False
    },
    "WHD": {
        "title": "🚀 Warehouse Delivery",
        "description": "Inbound and Outbound delivery",
        "required": False
    },
    "BPM": {
        "title": "🏭 Batch Production Management",
        "description": "Manage batch production: Re-open Lot and End of Lot",
        "required": False
    }
}

def get_step_status(step_id):
    """Get the status of a workflow step"""
    if step_id == "basic_info":
        return "completed" if st.session_state.basic_data_completed else "current"
    else:
        # For testing: always allow access to all modules
        if step_id in st.session_state.completed_modules:
            return "completed"
        elif st.session_state.current_step == step_id:
            return "current"
        else:
            return "available"

# Sidebar navigation
with st.sidebar:
    st.title("📋 EPCIS Generator")
    
    st.markdown("---")
    
    # Navigation steps
    for step_id, step_info in WORKFLOW_STEPS.items():
        status = get_step_status(step_id)
        
        # Determine styling and functionality
        if status == "completed":
            icon = "✅"
            css_class = "step-completed"
            disabled = False
        elif status == "current":
            icon = "👉"
            css_class = "step-current"
            disabled = False
        elif status == "available":
            icon = "⭕"
            css_class = ""
            disabled = False
        else:  # locked
            icon = "🔒"
            css_class = "step-locked"
            disabled = True
        
        # Create navigation button
        button_label = f"{icon} {step_info['title']}"
        
        if not disabled:
            if st.button(
                button_label,
                key=f"nav_{step_id}",
                use_container_width=True,
                disabled=disabled,
                help=step_info['description']
            ):
                st.session_state.current_step = step_id
                st.rerun()
        else:
            # Show locked step
            st.markdown(f'<div class="{css_class}">{button_label}</div>', unsafe_allow_html=True)
            st.caption(step_info['description'])
        
        # Small spacing
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show collected basic data summary if available
    if st.session_state.basic_data_completed:
        st.subheader("📋 Basic Data Summary")
        for key, value in st.session_state.basic_data.items():
            st.caption(f"**{key}:** {value}")
        
        # Data overview for each module
        st.subheader("📊 Module Data Status")
        
        # SNI Status
        sni_enabled = any([
            st.session_state.SNI_data.get('commissioning'),
            st.session_state.SNI_data.get('aggregation'),
            st.session_state.SNI_data.get('disaggregation'),
            st.session_state.SNI_data.get('update')
        ])
        status_icon = "✅" if sni_enabled else "⭕"
        st.caption(f"{status_icon} **SNI:** {'Data Present' if sni_enabled else 'No Data'}")
        
        # SPO Status  
        spo_enabled = any([
            st.session_state.SPO_data.get('decommissioning'),
            st.session_state.SPO_data.get('destruction'),
            st.session_state.SPO_data.get('sampling'),
            st.session_state.SPO_data.get('status_update')
        ])
        status_icon = "✅" if spo_enabled else "⭕"
        st.caption(f"{status_icon} **SPO:** {'Data Present' if spo_enabled else 'No Data'}")
        
        # WHD Status
        whd_enabled = any([
            st.session_state.WHD_data.get('inbound'),
            st.session_state.WHD_data.get('outbound')
        ])
        status_icon = "✅" if whd_enabled else "⭕"
        st.caption(f"{status_icon} **WHD:** {'Data Present' if whd_enabled else 'No Data'}")
        
        # BPM Status
        bmp_enabled = any([
            st.session_state.BPM_data.get('reopen_lot'),
            st.session_state.BPM_data.get('end_of_lot')
        ]) if 'BPM_data' in st.session_state else False
        status_icon = "✅" if bmp_enabled else "⭕"
        st.caption(f"{status_icon} **BPM:** {'Data Present' if bmp_enabled else 'No Data'}")
        
        if st.button("🔄 Reset Workflow", type="secondary"):
            # Reset all data
            st.session_state.basic_data_completed = False
            st.session_state.completed_modules = set()
            st.session_state.basic_data = {}
            st.session_state.SNI_data = {'enabled': False, 'commissioning': {}, 'aggregation': [], 'disaggregation': [], 'update': {}}
            st.session_state.SPO_data = {'enabled': False, 'decommissioning': {}, 'destruction': {}, 'sampling': {}, 'status_update': {}}
            st.session_state.WHD_data = {'enabled': False, 'inbound': {}, 'outbound': {}}
            st.session_state.BPM_data = {'enabled': False, 'reopen_lot': {}, 'end_of_lot': {}}
            st.session_state.current_step = "basic_info"
            st.rerun()

# Utility functions
def clear_module_data(module_name):
    """Clear data for a specific module"""
    if module_name == "SNI":
        st.session_state.SNI_data = {
            'enabled': False,
            'commissioning': {},
            'aggregation': [],
            'disaggregation': [],
            'update': {}
        }
        if "SNI" in st.session_state.completed_modules:
            st.session_state.completed_modules.remove("SNI")
    elif module_name == "SPO":
        st.session_state.SPO_data = {
            'enabled': False,
            'decommissioning': {},
            'destruction': {},
            'sampling': {},
            'status_update': {}
        }
        if "SPO" in st.session_state.completed_modules:
            st.session_state.completed_modules.remove("SPO")
    elif module_name == "WHD":
        st.session_state.WHD_data = {
            'enabled': False,
            'inbound': {},
            'outbound': {}
        }
        if "WHD" in st.session_state.completed_modules:
            st.session_state.completed_modules.remove("WHD")
    elif module_name == "BPM":
        if hasattr(st.session_state, 'BPM_data'):
            st.session_state.BPM_data = {}
        if "BPM" in st.session_state.completed_modules:
            st.session_state.completed_modules.remove("BPM")

def save_uploaded_file(uploaded_file, module_name):
    """Save uploaded file and return file path"""
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def file_upload_section(module_key, operation_key, title, description, gcp, file_types=['xlsx']):
    """Consistent file upload section for all modules"""
    st.subheader(title)
    st.write(description)
    
    uploaded_file = st.file_uploader(
        f"Choose file for {title.lower()}",
        type=file_types,
        key=f"file_{module_key}_{operation_key}",
        help=f"Upload data file for {title.lower()}"
    )
    
    file_info = {}
    if uploaded_file is not None:
        file_path = save_uploaded_file(uploaded_file, module_key)
        file_info = {
            'name': uploaded_file.name,
            'file_path': file_path,
            'uploaded_at': datetime.now().isoformat()
        }
        
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Preview button
        if st.button(f"📋 Preview {title}", key=f"preview_{module_key}_{operation_key}"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df.head(), use_container_width=True)
                elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                    st.dataframe(df.head(), use_container_width=True)
                else:
                    st.info("File preview available for CSV and Excel files")
            except Exception as e:
                st.error(f"Could not preview file: {str(e)}")
    
    return file_info

# Main content area
def show_basic_info():
    st.title("📋 Basic Information Collection")
    st.write("Please provide the essential information needed for all modules.")

    with st.form("basic_info_form"):
        st.subheader("Basic Information")

        col1, col2 = st.columns(2)
        today = datetime.now().date()
        
        with col1:
            sender_sgln = st.text_input("🏭 Sender SGLN*", value=st.session_state.basic_data.get("sender_sgln", ""))
            manufacturing_date = st.date_input(
                "🏗️ Manufacturing Date*", 
                value=pd.to_datetime(st.session_state.basic_data.get("manufacturing_date", today)),
                min_value=today
            )
            gcp = st.text_input("🔑 GCP (Global Company Prefix)*", value=st.session_state.basic_data.get("gcp", ""))
            lot_number = st.text_input("📦 Lot Number*", value=st.session_state.basic_data.get("lot_number", ""))
            
        with col2:
            receiver_sgln = st.text_input("🏢 Receiver SGLN*", value=st.session_state.basic_data.get("receiver_sgln", ""))
            expiration_date = st.date_input(
                "📅 Expiration Date*", 
                value=pd.to_datetime(st.session_state.basic_data.get("expiration_date", today)),
                min_value=today
            )
            internal_material_code = st.text_input("🆔 Internal Material Code*", value=st.session_state.basic_data.get("internal_material_code", ""))
            extension_digit = st.number_input("➕ Extension Digit*", min_value=0, max_value=9, step=1,
                                              value=st.session_state.basic_data.get("extension_digit", 0))

        submitted = st.form_submit_button("💾 Save & Continue", type="primary")
        
        if submitted:
            # Validate required fields
            required_fields = {
                "Sender SGLN": sender_sgln,
                "Receiver SGLN": receiver_sgln,
                "Expiration Date": expiration_date,
                "Manufacturing Date": manufacturing_date,
                "GCP": gcp,
                "Internal Material Code": internal_material_code,
                "Lot Number": lot_number,
                "Extension Digit": extension_digit,
            }

            missing_fields = [field for field, value in required_fields.items() if not str(value).strip()]
            if missing_fields:
                st.error(f"❌ Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                # Save data
                st.session_state.basic_data = {
                    "sender_sgln": sender_sgln,
                    "receiver_sgln": receiver_sgln,
                    "expiration_date": str(expiration_date),
                    "manufacturing_date": str(manufacturing_date),
                    "gcp": gcp,
                    "internal_material_code": internal_material_code,
                    "lot_number": lot_number,
                    "extension_digit": extension_digit,
                }
                st.session_state.basic_data_completed = True
                st.success("✅ Basic information saved! You can now access all modules.")
                st.balloons()

                # Auto-navigate to first module
                st.session_state.current_step = "SNI"
                st.rerun()

def show_SNI():
    st.title("🔄 Serial Number Interchange")
    st.write("Manage serial number operations and file uploads.")
    
    # Add clear button for this module
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear SNI Data", type="secondary", help="Clear all SNI module data"):
            clear_module_data("SNI")
            st.success("SNI data cleared!")
            st.rerun()
    
    # Get GCP from basic data
    gcp = st.session_state.basic_data.get("gcp", "")
    
    # ...existing code...
    st.markdown("---")
    
    # Operation selection
    st.subheader("Select Operations")
    col1, col2 = st.columns(2)

    with col1:
        commissioning_enabled = st.checkbox(
            "🏗️ Commissioning and Aggregation", 
            value=any(st.session_state.SNI_data['commissioning'].values()),
            help="Commission new serial numbers into the system and aggregate them"
        )

    with col2:
        disaggregation_enabled = st.checkbox(
            "📂 Disaggregation", 
            value=bool(st.session_state.SNI_data.get('disaggregation', [])),
            help="Break down packages into individual items"
        )
        update_enabled = st.checkbox(
            "🔄 Update", 
            value=bool(st.session_state.SNI_data.get('update', {})),
            help="Update existing serial number information"
        )

    st.markdown("---")

    # Commissioning section
    if commissioning_enabled:
        st.header("🏗️ Commissioning")
        levels = ["each", "inner", "case", "pallet"]

        if not gcp:
            st.warning("GCP is required to convert serials to URNs. Please enter GCP above.")

        for level in levels:
            level_enabled = st.checkbox(
                f"Enable {level.title()} Level",
                key=f"commissioning_{level}_enabled",
                value=level in st.session_state.SNI_data['commissioning']
            )

            if level_enabled:
                if not gcp:
                    st.info("Please provide GCP above to enable file upload for commissioning.")
                else:
                    file_info = file_upload_section(
                        "SNI", f"commissioning_{level}",
                        f"Commissioning - {level.title()} Level",
                        f"Upload file for commissioning {level} level",
                        gcp
                    )

                    # Add pack_size for all levels except 'each'
                    if level != "each":
                        pack_size = st.number_input(
                            f"Pack Size for {level.title()} Level",
                            min_value=1,
                            value=st.session_state.SNI_data['commissioning'].get(level, {}).get('pack_size', 1),
                            step=1,
                            key=f"commissioning_pack_size_{level}"
                        )
                        if file_info:
                            file_info['pack_size'] = pack_size
                    
                    # File type selection for each level
                    file_type = st.radio(
                        f"File Type for {level.title()} Level",
                        options=["REAL_TIME", "CONSOLIDATED_TIME"],
                        index=0 if st.session_state.SNI_data['commissioning'].get(level, {}).get('file_type', 'REAL_TIME') == 'REAL_TIME' else 1,
                        key=f"commissioning_file_type_{level}",
                        help="Choose whether this is real-time data or consolidated time data"
                    )
                    
                    if file_info:
                        file_info['file_type'] = file_type
                        st.session_state.SNI_data['commissioning'][level] = file_info
                    elif level in st.session_state.SNI_data['commissioning']:
                        st.info(f"Previously uploaded: {st.session_state.SNI_data['commissioning'][level].get('name', '')}")
            else:
                # Remove if disabled
                st.session_state.SNI_data['commissioning'].pop(level, None)
    
    # Disaggregation section (similar to aggregation)
    if disaggregation_enabled:
        st.header("📂 Disaggregation")
        
        if 'disaggregation' not in st.session_state.SNI_data:
            st.session_state.SNI_data['disaggregation'] = []
            
        if st.button("➕ Add Disaggregation Mapping", key="add_disaggregation"):
            st.session_state.SNI_data['disaggregation'].append({
                "parent_file": {},
                "child_file": {},
                "pack_size": 1
            })
            
        for idx, disagg in enumerate(st.session_state.SNI_data['disaggregation']):
            st.subheader(f"Disaggregation Mapping #{idx+1}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Parent File**")
                parent_file = st.file_uploader(
                    f"Disagg Parent File #{idx+1}",
                    type=['xlsx'],
                    key=f"disagg_parent_{idx}",
                    help="Upload file with parent serial numbers for disaggregation"
                )
                
                if parent_file:
                    file_path = save_uploaded_file(parent_file, "SNI")
                    
                    disagg['parent_file'] = {
                        'name': parent_file.name,
                        'file_path': file_path
                    }
                    
                    st.success(f"✅ Parent file uploaded: {parent_file.name}")
            
            with col2:
                st.write("**Child File**")
                child_file = st.file_uploader(
                    f"Disagg Child File #{idx+1}",
                    type=['xlsx'],
                    key=f"disagg_child_{idx}",
                    help="Upload file with child serial numbers for disaggregation"
                )
                
                if child_file:
                    file_path = save_uploaded_file(child_file, "SNI")
                    
                    disagg['child_file'] = {
                        'name': child_file.name,
                        'file_path': file_path
                    }
                    
                    st.success(f"✅ Child file uploaded: {child_file.name}")
            
            disagg['pack_size'] = st.number_input(
                f"Pack Size (Disagg #{idx+1})",
                min_value=1,
                value=disagg.get('pack_size', 1),
                step=1,
                key=f"disagg_pack_size_{idx}"
            )
            
            if st.button("❌ Remove This Mapping", key=f"remove_disagg_{idx}"):
                st.session_state.SNI_data['disaggregation'].pop(idx)
                st.rerun()
                
            st.markdown("---")
    
    # Update section
    if update_enabled:
        st.header("🔄 Update")
        
        # Packaging level selection
        level_options = ["Each", "Inner", "Case", "Pallet"]
        packaging_level = st.selectbox(
            "Select Packaging Level",
            level_options,
            index=level_options.index(st.session_state.SNI_data['update'].get('packaging_level', level_options[0])) 
            if st.session_state.SNI_data['update'].get('packaging_level') in level_options else 0,
            help="Select the packaging level for the update operation"
        )
        
        # Update type selection
        update_type_options = ("DEACTIVATED", "DECOMMISSIONED", "DESTROYED")
        update_type = st.selectbox(
            "Select Update Type",
            update_type_options,
            index=update_type_options.index(st.session_state.SNI_data['update'].get('update_type', update_type_options[0])) 
            if st.session_state.SNI_data['update'].get('update_type') in update_type_options else 0
        )
        
        # Action selection based on update type
        action = ""
        if update_type == "DECOMMISSIONED":
            action_options = ("Dispensed", "Disposed", "Illegitimate", "Damaged", "Expired", "Recalled", "Sampled", "Misplaced", "Stolen", "Quality Released", "Repackaged", "Withdrawn/Sampled", "Sampled by Authorities")
            action = st.selectbox(
                "Select Decommissioning Action",
                action_options,
                index=action_options.index(st.session_state.SNI_data['update'].get('action', action_options[0])) 
                if st.session_state.SNI_data['update'].get('action') in action_options else 0
            )
        elif update_type == "DESTROYED":
            action_options = ("Destroyed", "Damaged", "Disposed", "Expired", "Illegitimate", "Recalled", "Sampled", "Misplaced", "Stolen")
            action = st.selectbox(
                "Select Destroying Action",
                action_options,
                index=action_options.index(st.session_state.SNI_data['update'].get('action', action_options[0])) 
                if st.session_state.SNI_data['update'].get('action') in action_options else 0
            )
        
        # File upload for update
        update_file = st.file_uploader(
            "Choose file for update",
            type=['xlsx'],
            key="file_update_SNI",
            help="Upload data file for update operation"
        )
        
        if update_file:
            file_path = save_uploaded_file(update_file, "SNI")
            
            st.session_state.SNI_data['update'] = {
                'name': update_file.name,
                'file_path': file_path,
                'uom_type': packaging_level,
                'update_type': update_type,
                'action': action
            }
            
            st.success(f"✅ Update file uploaded: {update_file.name}")
        elif st.session_state.SNI_data['update'].get('name'):
            st.info(f"Previously uploaded: {st.session_state.SNI_data['update'].get('name')}")

def show_SPO():
    st.title("🛠️ Serial Product Operations")
    st.write("Manage product-related serial operations and upload supporting files.")
    
    # Add clear button for this module
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear SPO Data", type="secondary", help="Clear all SPO module data"):
            clear_module_data("SPO")
            st.success("SPO data cleared!")
            st.rerun()
    
    # Get GCP from basic data
    gcp = st.session_state.basic_data.get("gcp", "")
    
    # ...existing code...
    st.markdown("---")
    
    # Operation selection
    st.subheader("Select Operations")
    col1, col2 = st.columns(2)
    
    with col1:
        decommissioning_enabled = st.checkbox(
            "🗑️ Decommissioning",
            value=bool(st.session_state.SPO_data.get('decommissioning', {})),
            help="Remove serial numbers/products from active use"
        )
        destruction_enabled = st.checkbox(
            "🔥 Product Destruction",
            value=bool(st.session_state.SPO_data.get('destruction', {})),
            help="Destroy products with proper record keeping"
        )
        
    with col2:
        sampling_enabled = st.checkbox(
            "🧪 Product Sampling",
            value=bool(st.session_state.SPO_data.get('sampling', {})),
            help="Take product samples for testing or QA"
        )
        status_update_enabled = st.checkbox(
            "♻️ Status Update",
            value=bool(st.session_state.SPO_data.get('status_update', {})),
            help="Update status of existing serial products"
        )
    
    st.markdown("---")
    
    # Decommissioning section
    if decommissioning_enabled:
        st.header("🗑️ Decommissioning")
        
        # Decommissioning reason dropdown
        DECOM_REASON_CHOICES = [
            "DAMAGED", "DISPOSED", "DISPENSED", "EXPIRED", "MISPLACED", "RECALLED", 
            "ILLEGITIMATE", "QUALITY_RELEASED", "SAMPLED", "SAMPLED_BY_AUTHORITIES", 
            "WITHDRAWN_SAMPLED", "STOLEN", "WITHDRAWN", "REPACKAGED", "INACTIVE", 
            "DESTROYED", "UAE_BROKEN", "UAE_UNFOLDED", "UAE_TORN", "UAE_2D_MATRIX_NOT_READABLE", 
            "UAE_SMASHED", "UAE_DAMAGE_DUE_TO_LIQUID_SPILL", "UAE_OTHER", "CHECKED_OUT", 
            "UZ_DEFECT", "UZ_QA_SAMPLES", "UZ_DEMO_SAMPLES", "UZ_COMPLAINTS", "UZ_PRODUCT_TESTING", 
            "OTHER", "KZ_DEFECT", "KZ_QA_SAMPLES", "KZ_DEMO_SAMPLES", "KZ_COMPLAINTS", "KZ_PRODUCT_TESTING"
        ]
        
        decommissioning_reason = st.selectbox(
            "Decommissioning Reason",
            DECOM_REASON_CHOICES,
            index=DECOM_REASON_CHOICES.index(st.session_state.SPO_data['decommissioning'].get('reason', DECOM_REASON_CHOICES[0]))
            if st.session_state.SPO_data['decommissioning'].get('reason') in DECOM_REASON_CHOICES else 0,
            key="decommissioning_reason"
        )
        
        # File upload
        file_info = file_upload_section(
            "SPO", "decommissioning", 
            "Decommissioning File",
            "Upload file with serial numbers to decommission",
            gcp,
            ['csv', 'xlsx', 'txt', 'json']
        )
        
        if file_info:
            st.session_state.SPO_data['decommissioning'] = {
                'reason': decommissioning_reason,
                **file_info
            }
        elif st.session_state.SPO_data['decommissioning'].get('name'):
            st.info(f"Previously uploaded: {st.session_state.SPO_data['decommissioning'].get('name')}")
    
    # Destruction section
    if destruction_enabled:
        st.header("🔥 Product Destruction")
        
        # Destruction reason and method
        destruction_reasons = [
            "DESTROYED", "DAMAGED", "EXPIRED", "RECALLED", "DISPOSED", "ILLEGITIMATE",
            "MISPLACED", "SAMPLED", "STOLEN", "INACTIVE",
            "UAE_IMPROPER_STORAGE", "UAE_EXCEEDED_ENVIRONMENT_CONDITIONS",
            "UAE_CONTAMINATED", "UAE_ITEM_EXPIRED",
            "UZ_DEFECT", "UZ_QA_SAMPLES", "UZ_DEMO_SAMPLES", "UZ_COMPLAINTS",
            "UZ_PRODUCT_TESTING", "OTHER",
            "KZ_DEFECT", "KZ_QA_SAMPLES", "KZ_DEMO_SAMPLES",
            "KZ_COMPLAINTS", "KZ_PRODUCT_TESTING"
        ]

        destruction_methods = [
            "INCINERATION",
            "DILUTION_DRAINAGE_LIQUID",
            "DILUTION_DRAINAGE_SOLID"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            destruction_reason = st.selectbox(
                "Reason for Destruction",
                destruction_reasons,
                index=destruction_reasons.index(st.session_state.SPO_data['destruction'].get('reason', destruction_reasons[0]))
                if st.session_state.SPO_data['destruction'].get('reason') in destruction_reasons else 0,
                key="destruction_reason"
            )
            
        with col2:
            destruction_method = st.selectbox(
                "Method of Destruction",
                destruction_methods,
                index=destruction_methods.index(st.session_state.SPO_data['destruction'].get('method', destruction_methods[0]))
                if st.session_state.SPO_data['destruction'].get('method') in destruction_methods else 0,
                key="destruction_method"
            )
        
        # File upload
        file_info = file_upload_section(
            "SPO", "destruction", 
            "Destruction File",
            "Upload file with products marked for destruction",
            gcp,
            ['csv', 'xlsx', 'txt', 'json']
        )
        
        if file_info:
            st.session_state.SPO_data['destruction'] = {
                'reason': destruction_reason,
                'method': destruction_method,
                **file_info
            }
        elif st.session_state.SPO_data['destruction'].get('name'):
            st.info(f"Previously uploaded: {st.session_state.SPO_data['destruction'].get('name')}")
    
    # Sampling section
    if sampling_enabled:
        st.header("🧪 Product Sampling")

        # New fields for sampling event
        col1, col2, col3 = st.columns(3)
        with col1:
            inspection_country = st.selectbox(
                "Inspection Country",
                list(countries.keys()),
                index=list(countries.keys()).index(st.session_state.SPO_data['sampling'].get('inspection_country', list(countries.keys())[0]))
                if st.session_state.SPO_data['sampling'].get('inspection_country') in list(countries.keys()) else 0
            )
        with col2:
            sampling_entity = st.text_input(
                "Sampling Entity",
                value=st.session_state.SPO_data['sampling'].get('sampling_entity', "")
            )
        with col3:
            # Display options and their corresponding backend values
            sampling_reason_mapping = {
                "Archival Sample": "ARCHIVAL_SAMPLE",
                "Conformity Control": "CONFORMITY_CONTROL", 
                "Selective Control": "SELECTIVE_CONTROL"
            }
            sampling_reason_options = list(sampling_reason_mapping.keys())
            
            # Get current value to display
            current_backend_value = st.session_state.SPO_data['sampling'].get('sampling_reason', 'ARCHIVAL_SAMPLE')
            # Find display value for current backend value
            current_display_value = None
            for display, backend in sampling_reason_mapping.items():
                if backend == current_backend_value:
                    current_display_value = display
                    break
            if current_display_value is None:
                current_display_value = sampling_reason_options[0]
            
            sampling_reason_display = st.selectbox(
                "Sampling Reason",
                sampling_reason_options,
                index=sampling_reason_options.index(current_display_value)
            )
            sampling_reason = sampling_reason_mapping[sampling_reason_display]

        # File upload
        file_info = file_upload_section(
            "SPO", "sampling", 
            "Sampling File",
            "Upload file with sample selection data",
            gcp,
            ['csv', 'xlsx', 'txt', 'json']
        )

        if file_info:
            st.session_state.SPO_data['sampling'] = {
                **file_info,
                'inspection_country': countries.get(inspection_country, inspection_country),  # Save only country code
                'sampling_entity': sampling_entity,
                'sampling_reason': sampling_reason
            }
        elif st.session_state.SPO_data['sampling'].get('name'):
            st.info(f"Previously uploaded: {st.session_state.SPO_data['sampling'].get('name')}")
    
    # Status Update section (multi-scenario)
    if status_update_enabled:
        st.header("♻️ Status Update")

        # State transitions
        state_options = ["ENCODED", "COMMISSIONED", "DECOMMISSIONED"]
        state_transitions = {
            "ENCODED": ["COMMISSIONED"],
            "COMMISSIONED": ["DESTROYED", "DECOMMISSIONED"],
            "DECOMMISSIONED": ["COMMISSIONED"],
        }
        reason_choices = [
            "Not Applicable", "Damaged", "Expired", "Misplaced", "Recalled", "Stolen", "Blocked", "Under Investigation", "Withdrawn",
            "Disposed", "Illegitimate", "Sampled", "Other", "UAE - Broken", "UAE - Unfolded", "UAE - Torn", "UAE - 2D Matrix not readable",
            "UAE - Smashed", "UAE - Damage due to liquid spill", "UZ - Defect", "UZ - QA Samples", "UZ - Complaints", "UZ - Product Testing",
            "UZ - Demo Samples", "KZ - Defect", "KZ - QA Samples", "KZ - Compliants", "KZ - Product Testing", "KZ - Demo Samples", "EU - Checked Out"
        ]

        if 'scenarios' not in st.session_state.SPO_data['status_update']:
            st.session_state.SPO_data['status_update']['scenarios'] = []

        if st.button("➕ Add Status Update Scenario"):
            st.session_state.SPO_data['status_update']['scenarios'].append({
                "update_type": "Update of Product Status",
                "current_state": state_options[0],
                "target_state": state_transitions[state_options[0]][0],
                "current_logistic": "",
                "target_logistic": "",
                "reason": reason_choices[0]
            })

        # Define possible logistic statuses
        logistic_status_options = [
            "Available", "Picked", "Holding", "Pending Receipt", "Shipped", "Received"
        ]
        for idx, scenario in enumerate(st.session_state.SPO_data['status_update']['scenarios']):
            st.markdown(f"**Scenario {idx+1}**")
            # File upload for URNs
            urn_file = st.file_uploader(
                f"Upload file for Scenario {idx+1} URNs",
                type=['csv', 'xlsx', 'txt', 'json'],
                key=f"spo_status_update_file_{idx}"
            )
            gcp = st.session_state.basic_data.get("gcp", "")
            if urn_file:
                file_path = save_uploaded_file(urn_file, "SPO")
                scenario["file_path"] = file_path
                st.success(f"✅ File uploaded: {urn_file.name}")
            elif scenario.get("file_path"):
                st.info(f"Previously uploaded file for this scenario.")

            # Type of Update selection
            update_type_options = ["Update of Product Status", "Correction of incorrect product status"]
            scenario["update_type"] = st.selectbox(
                f"Type of Update for Scenario {idx+1}",
                update_type_options,
                index=update_type_options.index(scenario.get("update_type", update_type_options[0])) 
                if scenario.get("update_type") in update_type_options else 0,
                key=f"update_type_{idx}",
                help="Select the type of status update being performed"
            )

            scenario["current_state"] = st.selectbox(f"Current State for Scenario {idx+1}", state_options, index=state_options.index(scenario.get("current_state", state_options[0])), key=f"cur_state_{idx}")
            allowed_targets = state_transitions.get(scenario["current_state"], [])
            scenario["target_state"] = st.selectbox(f"Target State for Scenario {idx+1}", allowed_targets, index=allowed_targets.index(scenario.get("target_state", allowed_targets[0])) if scenario.get("target_state") in allowed_targets else 0, key=f"tgt_state_{idx}")

            # Contextual logistic status options
            # For ENCODED/DECOMMISSIONED -> COMMISSIONED, only None or Available/Picked/Holding
            if scenario["current_state"] in ["ENCODED", "DECOMMISSIONED"] and scenario["target_state"] == "COMMISSIONED":
                cur_logistic_opts = ["None"]
                tgt_logistic_opts = ["Available", "Picked", "Holding"]
            # For COMMISSIONED -> COMMISSIONED, allow all transitions
            elif scenario["current_state"] == "COMMISSIONED" and scenario["target_state"] == "COMMISSIONED":
                cur_logistic_opts = logistic_status_options
                tgt_logistic_opts = logistic_status_options
            # For COMMISSIONED -> DESTROYED/DECOMMISSIONED, only None
            elif scenario["current_state"] == "COMMISSIONED" and scenario["target_state"] in ["DESTROYED", "DECOMMISSIONED"]:
                cur_logistic_opts = ["None"]
                tgt_logistic_opts = ["None"]
            else:
                cur_logistic_opts = logistic_status_options
                tgt_logistic_opts = logistic_status_options

            # Only show logistic status dropdowns if options contain more than just "None"
            if len(cur_logistic_opts) > 1 or (len(cur_logistic_opts) == 1 and cur_logistic_opts[0] != "None"):
                scenario["current_logistic"] = st.selectbox(f"Current Logistic Status for Scenario {idx+1}", cur_logistic_opts, index=cur_logistic_opts.index(scenario.get("current_logistic", cur_logistic_opts[0])) if scenario.get("current_logistic") in cur_logistic_opts else 0, key=f"cur_log_{idx}")
            else:
                scenario["current_logistic"] = "None"
                
            if len(tgt_logistic_opts) > 1 or (len(tgt_logistic_opts) == 1 and tgt_logistic_opts[0] != "None"):
                scenario["target_logistic"] = st.selectbox(f"Target Logistic Status for Scenario {idx+1}", tgt_logistic_opts, index=tgt_logistic_opts.index(scenario.get("target_logistic", tgt_logistic_opts[0])) if scenario.get("target_logistic") in tgt_logistic_opts else 0, key=f"tgt_log_{idx}")
            else:
                scenario["target_logistic"] = "None"
            scenario["reason"] = st.selectbox(f"Reason for Scenario {idx+1}", reason_choices, index=reason_choices.index(scenario.get("reason", reason_choices[0])), key=f"reason_{idx}")
            if st.button(f"❌ Remove Scenario {idx+1}"):
                st.session_state.SPO_data['status_update']['scenarios'].pop(idx)
                st.rerun()

def show_WHD():

    st.title("🏭 Warehouse Delivery")
    st.write("Manage inbound and outbound deliveries with supporting files.")
    
    # Add clear button for this module
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear WHD Data", type="secondary", help="Clear all WHD module data"):
            clear_module_data("WHD")
            st.success("WHD data cleared!")
            st.rerun()
    
    # Get GCP from basic data
    gcp = st.session_state.basic_data.get("gcp", "")
    
    # ...existing code...
    st.markdown("---")
    
    # Operation selection
    st.subheader("Select Operations")
    col1, col2 = st.columns(2)

    with col1:
        outbound_enabled = st.checkbox(
            "📦 Outbound Delivery",
            value=bool(st.session_state.WHD_data.get('outbound', {})),
            help="Ship goods out from the warehouse",
            key="whd_outbound_checkbox"
        )

    with col2:
        inbound_enabled = st.checkbox(
            "📥 Inbound Delivery",
            value=bool(st.session_state.WHD_data.get('inbound', {})),
            help="Receive goods into the warehouse",
            key="whd_inbound_checkbox"
        )

    st.markdown("---")
    
    # Common delivery details function
    def delivery_section(op_key, op_title, sale_type_options, identifier_options):
        st.header(op_title)
        
        # Initialize if not exists
        if op_key not in st.session_state.WHD_data:
            st.session_state.WHD_data[op_key] = {}
            
        # Ensure all required keys exist
        if 'delivery_details' not in st.session_state.WHD_data[op_key]:
            st.session_state.WHD_data[op_key]['delivery_details'] = {}
        if 'transaction_identifiers' not in st.session_state.WHD_data[op_key]:
            st.session_state.WHD_data[op_key]['transaction_identifiers'] = []
        if 'file' not in st.session_state.WHD_data[op_key]:
            st.session_state.WHD_data[op_key]['file'] = {}
        
        # Delivery Details
        colA, colB = st.columns(2)
        with colA:
            delivery_status = st.selectbox(
                f"{op_title} - Delivery Status",
                ["SUBMITTED", "DRAFT", "VOIDED", "CANCELLED"],
                key=f"whd_{op_key}_delivery_status",
                index=["SUBMITTED", "DRAFT", "VOIDED", "CANCELLED"].index(
                    st.session_state.WHD_data[op_key].get('delivery_status', 'SUBMITTED')
                ) if st.session_state.WHD_data[op_key].get('delivery_status') in ["SUBMITTED", "DRAFT", "VOIDED", "CANCELLED"] else 0
            )
        with colB:
            sale_type = st.selectbox(
                f"{op_title} - Sale Type",
                sale_type_options,
                key=f"whd_{op_key}_sale_type",
                index=sale_type_options.index(
                    st.session_state.WHD_data[op_key].get('sale_type', sale_type_options[0])
                ) if st.session_state.WHD_data[op_key].get('sale_type') in sale_type_options else 0
            )

        colG, colH = st.columns(2)
        with colG:
            delivery_number = st.text_input(
                f"{op_title} - Delivery Number", 
                key=f"whd_{op_key}_delivery_number",
                value=st.session_state.WHD_data[op_key].get('delivery_number', '')
            )
        with colH:
            shipment_date = st.date_input(
                f"{op_title} - Shipment Date", 
                key=f"whd_{op_key}_shipment_date",
                value=pd.to_datetime(st.session_state.WHD_data[op_key].get('shipment_date', datetime.now().date())) if st.session_state.WHD_data[op_key].get('shipment_date') else datetime.now().date()
            )

        # Shipping From
        st.markdown("#### 🚚 Shipping From")
        colC, colD = st.columns(2)
        with colC:
            shipping_from_country = st.selectbox(
                f"{op_title} - Shipping From Country",
                list(countries.keys()),
                key=f"whd_{op_key}_shipping_from_country",
                index=list(countries.keys()).index(
                    st.session_state.WHD_data[op_key].get('shipping_from_country', list(countries.keys())[0])
                ) if st.session_state.WHD_data[op_key].get('shipping_from_country') in list(countries.keys()) else 0
            )
            shipping_from_location = st.text_input(
                f"{op_title} - Shipping From Location", 
                key=f"whd_{op_key}_shipping_from_location",
                value=st.session_state.WHD_data[op_key].get('shipping_from_location', '')
            )
        with colD:
            shipping_from_business = st.text_input(
                f"{op_title} - Shipping From Business", 
                key=f"whd_{op_key}_shipping_from_business",
                value=st.session_state.WHD_data[op_key].get('shipping_from_business', '')
            )

        # Shipping To
        st.markdown("#### 📦 Shipping To")
        colE, colF = st.columns(2)
        with colE:
            shipping_to_country = st.selectbox(
                f"{op_title} - Shipping To Country",
                list(countries.keys()),
                key=f"whd_{op_key}_shipping_to_country",
                index=list(countries.keys()).index(
                    st.session_state.WHD_data[op_key].get('shipping_to_country', list(countries.keys())[0])
                ) if st.session_state.WHD_data[op_key].get('shipping_to_country') in list(countries.keys()) else 0
            )
            shipping_to_location = st.text_input(
                f"{op_title} - Shipping To Location", 
                key=f"whd_{op_key}_shipping_to_location",
                value=st.session_state.WHD_data[op_key].get('shipping_to_location', '')
            )
        with colF:
            shipping_to_business = st.text_input(
                f"{op_title} - Shipping To Business", 
                key=f"whd_{op_key}_shipping_to_business",
                value=st.session_state.WHD_data[op_key].get('shipping_to_business', '')
            )

        # Transaction Identifiers - Simplified single identifier
        st.markdown("#### 🔑 Transaction Identifier")
        
        # Initialize if not exists
        if 'transaction_identifiers' not in st.session_state.WHD_data[op_key]:
            st.session_state.WHD_data[op_key]['transaction_identifiers'] = []
            
        cols = st.columns([2, 3])
        with cols[0]:
            # Get current transaction identifier if it exists
            current_identifiers = st.session_state.WHD_data[op_key]['transaction_identifiers']
            current_type = current_identifiers[0]['type'] if current_identifiers else identifier_options[0]
            
            id_type = st.selectbox(
                f"{op_title} - Type",
                identifier_options,
                key=f"whd_{op_key}_id_type",
                index=identifier_options.index(current_type) if current_type in identifier_options else 0
            )
        with cols[1]:
            # Get current transaction identifier value if it exists
            current_value = current_identifiers[0]['value'] if current_identifiers else ""
            
            id_value = st.text_input(
                f"{op_title} - Value",
                key=f"whd_{op_key}_id_value",
                value=current_value,
                placeholder="Enter transaction identifier value"
            )
        
        # Automatically save the transaction identifier when both type and value are provided
        if id_type and id_value and id_value.strip():
            # Always keep only one transaction identifier
            st.session_state.WHD_data[op_key]['transaction_identifiers'] = [{
                "type": id_type,
                "value": id_value.strip()
            }]
            st.success(f"Transaction identifier saved: {id_type} = {id_value.strip()}")
        elif id_value and not id_value.strip():
            # Clear if value is empty
            st.session_state.WHD_data[op_key]['transaction_identifiers'] = []
        else:
            # Show current state
            current_identifiers = st.session_state.WHD_data[op_key]['transaction_identifiers']
            if current_identifiers:
                st.info(f"Current: {current_identifiers[0]['type']} = {current_identifiers[0]['value']}")
        
        # Debug information
        if st.checkbox("Show Debug Info", key=f"debug_{op_key}"):
            st.write("**Session State WHD Data:**")
            st.json(st.session_state.WHD_data.get(op_key, {}))

        # Item details
        st.markdown("#### 📦 Item Details")
        colI, colJ = st.columns(2)
        with colI:
            item_code = st.text_input(
                f"{op_title} - Item Code", 
                key=f"whd_{op_key}_item_code",
                value=st.session_state.WHD_data[op_key].get('item_code', '')
            )
            gcp_value = st.text_input(
                f"{op_title} - GCP", 
                key=f"whd_{op_key}_gcp",
                value=st.session_state.WHD_data[op_key].get('gcp', gcp)
            )
        with colJ:
            lot_number = st.text_input(
                f"{op_title} - Lot Number", 
                key=f"whd_{op_key}_lot_number",
                value=st.session_state.WHD_data[op_key].get('lot_number', '')
            )

        # Save delivery details - this is what the EPCIS generator expects
        st.session_state.WHD_data[op_key].update({
            'delivery_type': op_key.upper(),  # INBOUND or OUTBOUND
            'delivery_status': delivery_status,
            'delivery_number': delivery_number,
            'shipment_date': str(shipment_date),
            'sale_type': sale_type,
            'shipping_from_country': countries.get(shipping_from_country, shipping_from_country),  # Save only country code
            'shipping_from_business': shipping_from_business,
            'shipping_from_location': shipping_from_location,
            'shipping_to_country': countries.get(shipping_to_country, shipping_to_country),  # Save only country code
            'shipping_to_business': shipping_to_business,
            'shipping_to_location': shipping_to_location,
            'item_code': item_code,
            'lot_number': lot_number,
            'gcp': gcp_value,
        })
        
        # File upload
        st.markdown("#### 📂 Upload Shipment File")
        file_info = file_upload_section(
            "WHD", op_key, 
            f"{op_title} File",
            f"Upload data file for {op_title.lower()} operation",
            gcp_value or gcp,
            ['csv', 'xlsx', 'txt', 'json', 'xls', 'xlsm']
        )
        
        if file_info:
            st.session_state.WHD_data[op_key]['file'] = file_info
            # Also store URNs at the top level for easy access
            st.session_state.WHD_data[op_key]['urns'] = file_info.get('urns', [])
        elif st.session_state.WHD_data[op_key].get('file', {}).get('name'):
            st.info(f"Previously uploaded: {st.session_state.WHD_data[op_key]['file'].get('name')}")
    
    # Inbound section
    if inbound_enabled:
        inbound_sale_types = [
            "Return Import", "Return in Country", "Purchase Import", 
            "Purchase in Country", "Transfer Import", "Transfer in Country"
        ]
        inbound_identifier_types = [
            "Bill of Lading", "Destruction Order", "E-Way Bill Number", "Import Permit", 
            "Invoice Number", "Nota Fiscal Electronica", "Packing Slip Number", "PO Number",
            "PRO Number", "Return", "Sales Order Number", "Sales Permit", "Shipment Number",
            "Shipment Permit", "Local Sales Permit", "Transfer Number", "Other"
        ]
        
        delivery_section("inbound", "📥 Inbound Delivery", inbound_sale_types, inbound_identifier_types)
    
    # Outbound section
    if outbound_enabled:
        outbound_sale_types = [
            "Sale Export", "Sale in Country", "Return Export", 
            "Return in Country", "Transfer Export", "Transfer in Country"
        ]
        outbound_identifier_types = [
            "Bill of Lading", "Destruction Order", "E-Way Bill Number", "Import Permit",
            "Invoice Number", "Nota Fiscal Electronica", "Packing Slip Number", "PO Number",
            "PRO Number", "Return", "Sales Order Number", "Sales Permit", "Shipment Number",
            "Shipment Permit", "Local Sales Permit", "Transfer Number", "Other"
        ]
        
        delivery_section("outbound", "📦 Outbound Delivery", outbound_sale_types, outbound_identifier_types)

# Batch Production Management module
def show_BPM():

    st.title("🏭 Batch Production Management")
    st.write("Manage batch production operations: Re-open Lot and End of Lot.")

    # Add clear button for this module
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear BPM Data", type="secondary", help="Clear all BPM module data"):
            clear_module_data("BPM")
            st.success("BPM data cleared!")
            st.rerun()

    if 'BPM_data' not in st.session_state:
        st.session_state.BPM_data = {
            'reopen_lot': {},
            'end_of_lot': {}
        }

    option = st.radio("Select Operation", ["Re-open Lot", "End of Lot"], key="bpm_operation")

    col1, col2 = st.columns(2)
    with col1:
        item_code_type = st.selectbox(
            "Enter Item Code Type",
            item_code_types,
            index=list(item_code_types).index(
                st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('item_code_type', item_code_types[0])
            ) if st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('item_code_type') in item_code_types else 0
        )
        item_code_value = st.text_input("Enter Item Code Value", value=st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('item_code_value', ""))
    with col2:
        country_code = st.selectbox("Select Country Code", list(countries.keys()), index=list(countries.keys()).index(st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('country_code', list(countries.keys())[0])) if st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('country_code') in list(countries.keys()) else 0)
        lot_number = st.text_input("Enter Lot Number", value=st.session_state.BPM_data.get(option.lower().replace('-', '').replace(' ', '_'), {}).get('lot_number', ""))

    op_key = option.lower().replace('-', '').replace(' ', '_')

    # Store the current form values back to session state
    if op_key not in st.session_state.BPM_data:
        st.session_state.BPM_data[op_key] = {}
    
    st.session_state.BPM_data[op_key].update({
        'item_code_type': item_code_type,
        'item_code_value': item_code_value,
        'country_code': country_code,
        'lot_number': lot_number
    })

    # End of Lot extra fields
    if option == "End of Lot":
        if 'packaging' not in st.session_state.BPM_data[op_key]:
            st.session_state.BPM_data[op_key]['packaging'] = []
        st.markdown("---")
        st.subheader("Packaging Details")
        uom_levels = ["Each", "Inner Pack/Bundle", "Case/Shipper", "Pallet"]
        with st.form(key="bpm_packaging_form"):
            colA, colB, colC, colD = st.columns([3, 3, 2, 2])
            with colA:
                packaging_code = st.text_input("Packaging Code")
            with colB:
                uom_level = st.selectbox("Level of UOM", uom_levels)
            with colC:
                quantity = st.number_input("Quantity", min_value=1, step=1)
            with colD:
                add_packaging = st.form_submit_button("+ Add Packaging")
            if add_packaging:
                st.session_state.BPM_data[op_key]['packaging'].append({
                    'packaging_code': packaging_code,
                    'uom_level': uom_level,
                    'quantity': quantity
                })
        # Show current packaging entries
        for idx, pkg in enumerate(st.session_state.BPM_data[op_key]['packaging']):
            st.write(f"{idx+1}. Code: {pkg['packaging_code']}, UOM: {pkg['uom_level']}, Qty: {pkg['quantity']}")
            if st.button(f"Remove Packaging #{idx+1}"):
                st.session_state.BPM_data[op_key]['packaging'].pop(idx)
                st.rerun()



    st.markdown("---")
    # Place Save All Input Data to JSON and Generate EPCIS XML buttons at the bottom, like other modules
    if st.button("💾 Save All Input Data to JSON", key="bpm_save_all_json"):
        session_data = build_full_input_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = "inputs"
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = os.path.join(folder, f"input_data_{timestamp}.json")
        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=4, default=str)
        st.session_state.input_json_saved = True
        st.session_state.last_input_json_path = file_path
        st.success(f"All input data saved to {file_path}!")

    if st.session_state.get('input_json_saved', False):
        import sys
        sys.path.append('.')  # Ensure current dir is in path for imports
        from epcis_generate_util import generate_epcis_xml_from_json
        if st.button("⚡ Generate EPCIS XML", key="bpm_generate_xml"):
            json_path = st.session_state.get('last_input_json_path')
            if not json_path or not os.path.exists(json_path):
                st.error("No valid input JSON file found. Please save your data first.")
            else:
                try:
                    xml_path = generate_epcis_xml_from_json(st.session_state.basic_data, json_path)
                    st.success(f"EPCIS XML generated and saved to: {xml_path}")
                    with open(xml_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    st.download_button(
                        "📥 Download XML", 
                        data=xml_content, 
                        file_name=os.path.basename(xml_path), 
                        mime="application/xml"
                    )
                except Exception as e:
                    st.error(f"Error during XML generation: {e}")


def build_full_input_json():
    """Build a consistent JSON structure from all module data"""
    basic_data = st.session_state.get("basic_data", {})
    # Copy all basic_data fields to the top level
    # Flatten the selected BPM operation's data into the top level if on BPM page
    modules = {
        "SNI": st.session_state.get("SNI_data", {}),
        "SPO": st.session_state.get("SPO_data", {}),
        "WHD": st.session_state.get("WHD_data", {}),
        "BPM": st.session_state.get("BPM_data", {}),
    }
    
    data = {**basic_data, "modules": modules, "generated_at": datetime.now().isoformat()}

    # If on BPM page, flatten the selected operation's data to top level
    if st.session_state.get("current_step") == "BPM":
        option = st.session_state.get("bpm_operation", "Re-open Lot")
        op_key = option.lower().replace('-', '').replace(' ', '_')
        bpm_data = st.session_state.get("BPM_data", {})
        op_data = bpm_data.get(op_key, {})
        if op_data:
            data = {**data, **op_data, "operation_type": option}
            if option == "End of Lot" and "packaging" in op_data:
                # Map UI UOM labels to standard codes for generator.py
                uom_map = {
                    "Each": ("each", "EA"),
                    "Inner Pack/Bundle": ("inner", "BU"),
                    "Case/Shipper": ("case", "CA"),
                    "Pallet": ("pallet", "PA")
                }
                packaging_codes = []
                for pkg in op_data["packaging"]:
                    uom_label = pkg.get("uom_level", "Each")
                    level, uom_code = uom_map.get(uom_label, ("each", "EA"))
                    packaging_codes.append({
                        **pkg,
                        "level": level,
                        "uom_level": uom_code
                    })
                data["packaging_codes"] = packaging_codes
    return data

# Main content routing
current_step = st.session_state.current_step

if current_step == "basic_info":
    show_basic_info()
elif current_step == "SNI":
    show_SNI()
elif current_step == "SPO":
    show_SPO()
elif current_step == "WHD":
    show_WHD()
elif current_step == "BPM":
    show_BPM()

# Save All Input Data to JSON
st.markdown("---")

if st.session_state.basic_data_completed:
    if st.button("💾 Save All Input Data to JSON", type="primary"):
        # Save session data as a single object to a new file with timestamp in 'inputs' folder
        session_data = build_full_input_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = "inputs"
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = os.path.join(folder, f"input_data_{timestamp}.json")
        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=4, default=str)
        st.session_state.input_json_saved = True
        st.session_state.last_input_json_path = file_path
        st.success(f"All input data saved to {file_path}!")

    if st.session_state.get('input_json_saved', False):
        import sys
        sys.path.append('.')  # Ensure current dir is in path for imports
        from epcis_generate_util import generate_epcis_xml_from_json
        if st.button("⚡ Generate EPCIS XML", type="primary"):
            json_path = st.session_state.get('last_input_json_path')
            if not json_path or not os.path.exists(json_path):
                st.error("No valid input JSON file found. Please save your data first.")
            else:
                try:
                    xml_path = generate_epcis_xml_from_json(st.session_state.basic_data, json_path)
                    st.success(f"EPCIS XML generated and saved to: {xml_path}")
                    with open(xml_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    st.download_button(
                        "📥 Download XML", 
                        data=xml_content, 
                        file_name=os.path.basename(xml_path), 
                        mime="application/xml"
                    )
                except Exception as e:
                    st.error(f"Error during XML generation: {e}")