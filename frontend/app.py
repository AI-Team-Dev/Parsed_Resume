import streamlit as st
import requests
import os
import time
import html

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

def browse_folder():
    """Open folder dialog and return selected folder path"""
    if not TKINTER_AVAILABLE:
        st.error("tkinter is not available. Please install it or use manual path entry.")
        return None
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front
        # Use askdirectory to select a folder (not a file)
        folder_path = filedialog.askdirectory(
            title="Select Folder",
            mustexist=True
        )
        root.destroy()
        return folder_path if folder_path else None
    except Exception as e:
        st.error(f"Error opening folder dialog: {str(e)}")
        return None

def browse_file(title="Select File", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]):
    """Open file dialog and return selected file path"""
    if not TKINTER_AVAILABLE:
        st.error("tkinter is not available. Please install it or use manual path entry.")
        return None
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        return file_path if file_path else None
    except Exception as e:
        st.error(f"Error opening file dialog: {str(e)}")
        return None

def browse_save_file(title="Save File As", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")], initialfile="output.xlsx"):
    """Open save file dialog and return selected file path"""
    if not TKINTER_AVAILABLE:
        st.error("tkinter is not available. Please install it or use manual path entry.")
        return None
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front
        file_path = filedialog.asksaveasfilename(title=title, filetypes=filetypes, defaultextension=".xlsx", initialfile=initialfile)
        root.destroy()
        return file_path if file_path else None
    except Exception as e:
        st.error(f"Error opening save file dialog: {str(e)}")
        return None

st.set_page_config(page_title="Resume Parser", layout="wide")

# Center the title
st.markdown("""
    <style>
    h1 {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)
st.title("Resume Parser")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    backend_url = st.text_input("Backend URL", value=BACKEND_URL)
    if backend_url != BACKEND_URL:
        BACKEND_URL = backend_url
    
    # Timeout configuration
    st.subheader("Timeout Settings")
    default_timeout_minutes = 60  # 1 hour default
    if "request_timeout_minutes" not in st.session_state:
        st.session_state.request_timeout_minutes = default_timeout_minutes
    
    timeout_minutes = st.number_input(
        "Request Timeout (minutes)",
        min_value=10,
        max_value=180,
        value=st.session_state.request_timeout_minutes,
        step=10,
        help="Maximum time to wait for processing to complete. Increase for large batches."
    )
    st.session_state.request_timeout_minutes = timeout_minutes
    st.caption(f"Timeout: {timeout_minutes} minutes ({timeout_minutes * 60} seconds)")
    
    # Health check
    st.subheader("Backend Status")
    try:
        health_response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            st.success("Backend is running")
        else:
            st.warning("Backend responded but with an error")
    except:
        st.error("Backend is not reachable")
        st.info(f"Backend URL: {BACKEND_URL}")

# Main content - Center the header
st.markdown("""
    <style>
    h2 {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)
st.header("Select Folders")

# Create columns with equal alignment
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Folder")
    st.caption("Enter path to folder containing resumes")
    
    # Get the value to use - prioritize browse result, then existing session state
    input_value = ""
    if "_browse_input_result" in st.session_state:
        # We have a new browse result - use it and clear temp key
        input_value = st.session_state._browse_input_result
        # Only set session state if key doesn't exist yet (to avoid modification error)
        if "input_folder" not in st.session_state:
            st.session_state.input_folder = input_value
        del st.session_state._browse_input_result
    elif "input_folder" in st.session_state:
        input_value = st.session_state.input_folder
    
    col_input1, col_input2 = st.columns([4, 1])
    with col_input1:
        input_folder = st.text_input(
            "Input folder path",
            value=input_value,
            placeholder="C:\\Users\\YourName\\Documents\\resumes",
            help="Enter the full path to the folder containing your resume files (PDF, DOCX, DOC)",
            key="input_folder",
            label_visibility="collapsed"
        )
    with col_input2:
        st.write("")  # Spacing for alignment
        if st.button("Browse", key="browse_input", use_container_width=True):
            selected_folder = browse_folder()
            if selected_folder:
                st.session_state._browse_input_result = selected_folder
                st.rerun()
    
    if input_folder and os.path.exists(input_folder):
        st.success(f"Folder found: {input_folder}")
        try:
            files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
            st.info(f"Found {len(files)} file(s) in folder")
            if st.checkbox("Show files", key="show_input_files"):
                for f in files[:10]:
                    st.text(f"  • {f}")
                if len(files) > 10:
                    st.text(f"  ... and {len(files) - 10} more")
        except Exception as e:
            st.warning(f"Could not list files: {str(e)}")
    elif input_folder:
        st.error(f"Folder not found: {input_folder}")

with col2:
    st.subheader("Output Location")
    output_option = st.radio(
        "Output type",
        ["File Path", "Folder Path"],
        help="Choose to specify exact file path or just folder (filename will be auto-generated)",
        key="output_option"
    )
    
    if output_option == "File Path":
        st.caption("Enter output Excel file path. If file exists, data will be appended.")
        
        # Handle browse results - check before creating widget
        browse_file_result = None
        
        if "_browse_output_file_result" in st.session_state:
            browse_file_result = st.session_state._browse_output_file_result
            del st.session_state._browse_output_file_result
        
        # Determine the value to use and update session state if we have a browse result
        if browse_file_result:
            # File was selected - force update session state
            output_file_value = browse_file_result
            # Clear and set to force update (before widget creation, so this is safe)
            if "output_file_path" in st.session_state:
                del st.session_state.output_file_path
            st.session_state.output_file_path = output_file_value
        else:
            # Use existing session state value
            output_file_value = st.session_state.get("output_file_path", "")
        
        col_input, col_file = st.columns([5, 1])
        with col_input:
            output_path_input = st.text_input(
                "Output file or folder path",
                value=output_file_value,
                placeholder="C:\\Users\\YourName\\Documents\\output.xlsx or C:\\Users\\YourName\\Documents",
                help="Enter file path (to append) or folder path (to create new file). You can also use the browse button.",
                key="output_file_path",
                label_visibility="collapsed"
            )
            # Set output_path for processing
            output_path = output_path_input
        with col_file:
            st.write("")  # Spacing
            st.write("")  # Spacing
            # Browse for file button
            if st.button("File", key="browse_output_file", use_container_width=True, help="Select an existing Excel file to append data"):
                # Use browse_file to select existing files for appending
                selected_file = browse_file(title="Select Excel File to Append Data", filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")])
                if selected_file:
                    # Store result and update session state
                    st.session_state._browse_output_file_result = selected_file
                    # Update the widget value by setting session state before rerun
                    if "output_file_path" not in st.session_state:
                        st.session_state.output_file_path = selected_file
                    st.rerun()
    else:
        st.caption("Enter output folder path (a new file 'Parsed_Resumes.xlsx' will be created)")
        
        # Handle browse result - check before creating widget
        browse_folder_result = None
        if "_browse_output_folder_result" in st.session_state:
            browse_folder_result = st.session_state._browse_output_folder_result
            del st.session_state._browse_output_folder_result
        
        # Determine the value to use and update session state if we have a browse result
        if browse_folder_result:
            # Folder was selected - force update session state
            output_folder_value = browse_folder_result
            # Clear and set to force update (before widget creation, so this is safe)
            if "output_folder_path" in st.session_state:
                del st.session_state.output_folder_path
            st.session_state.output_folder_path = output_folder_value
        else:
            # Use existing session state value
            output_folder_value = st.session_state.get("output_folder_path", "")
        
        col_output1, col_output2 = st.columns([4, 1])
        with col_output1:
            output_folder = st.text_input(
                "Output folder path",
                value=output_folder_value,
                placeholder="C:\\Users\\YourName\\Documents",
                help="Enter folder path (filename will be 'Parsed_Resumes.xlsx'). A new file will be created.",
                key="output_folder_path",
                label_visibility="collapsed"
            )
        with col_output2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            # Handle browse button click - placed next to input field
            if st.button("Browse", key="browse_output_folder", use_container_width=True):
                selected_folder = browse_folder()
                if selected_folder:
                    st.session_state._browse_output_folder_result = selected_folder
                    st.rerun()
        if output_folder:
            output_path = os.path.join(output_folder, "Parsed_Resumes.xlsx")
        else:
            output_path = None

# Process button
st.divider()

# Check if we're polling for progress
if "current_job_id" in st.session_state and st.session_state.current_job_id:
    job_id = st.session_state.current_job_id
    output_path = st.session_state.get("job_output_path", "")
    
    try:
        progress_response = requests.get(
            f"{BACKEND_URL}/api/progress/{job_id}",
            timeout=5
        )
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            status = progress_data.get("status", "processing")
            total_files = progress_data.get("total_files", 0)
            processed_files = progress_data.get("processed_files", 0)
            failed_files = progress_data.get("failed_files", 0)
            file_status = progress_data.get("file_status", {})
            current_file = progress_data.get("current_file", "")
            message = progress_data.get("message", "")
            
            # Update progress bar
            if total_files > 0:
                progress_percent = min(100, (processed_files + failed_files) / total_files * 100)
            else:
                progress_percent = 0
            
            st.progress(progress_percent / 100)
            st.caption(f"Progress: {processed_files + failed_files} / {total_files} files processed ({processed_files} successful, {failed_files} failed)")
            if current_file:
                st.info(f"🔄 Currently processing: {current_file}")
            if message:
                st.caption(f"Status: {message}")
            
            # Show file status list
            st.subheader("📋 File Processing Status")
            
            # Group files by status
            pending_files = [f for f, s in file_status.items() if s == "pending"]
            processing_files = [f for f, s in file_status.items() if s == "processing"]
            success_files = [f for f, s in file_status.items() if s == "success"]
            failed_files_list = [f for f, s in file_status.items() if s == "failed"]
            
            # Create two columns with scrollable containers
            col1, col2 = st.columns(2)
            
            # Left column: Processed files (scrollable)
            with col1:
                st.markdown(f"**✅ Processed ({len(success_files)}):**")
                # Create scrollable container using HTML/CSS
                if success_files:
                    # Build HTML content with all files - use explicit dark text color
                    files_list = "\n".join([f'<div style="padding: 4px 0; color: #000000 !important; font-family: sans-serif; font-size: 14px;">• ✅ {html.escape(f)}</div>' for f in success_files])
                    
                    st.markdown(
                        f"""
                        <div style="
                            max-height: 400px;
                            overflow-y: auto;
                            overflow-x: hidden;
                            padding: 12px;
                            border: 1px solid #e0e0e0;
                            border-radius: 5px;
                            background-color: #ffffff !important;
                            margin-top: 5px;
                        ">
                            {files_list}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.caption("No files processed yet")
            
            # Right column: Pending, Processing, and Failed files (scrollable)
            with col2:
                # Check if there are any files to show
                has_content = processing_files or failed_files_list or pending_files
                
                if has_content:
                    # Build HTML content
                    content_html = []
                    
                    if processing_files:
                        content_html.append(f'<div style="padding: 8px 0; font-weight: bold; color: #000000 !important; font-family: sans-serif; font-size: 14px;">🔄 Processing ({len(processing_files)}):</div>')
                        for f in processing_files:
                            content_html.append(f'<div style="padding: 4px 0; color: #000000 !important; font-family: sans-serif; font-size: 14px;">• 🔄 {html.escape(f)}</div>')
                        content_html.append('<div style="padding: 8px 0;"></div>')
                    
                    if failed_files_list:
                        content_html.append(f'<div style="padding: 8px 0; font-weight: bold; color: #000000 !important; font-family: sans-serif; font-size: 14px;">❌ Failed ({len(failed_files_list)}):</div>')
                        for f in failed_files_list:
                            content_html.append(f'<div style="padding: 4px 0; color: #000000 !important; font-family: sans-serif; font-size: 14px;">• ❌ {html.escape(f)}</div>')
                        content_html.append('<div style="padding: 8px 0;"></div>')
                    
                    if pending_files:
                        content_html.append(f'<div style="padding: 8px 0; font-weight: bold; color: #000000 !important; font-family: sans-serif; font-size: 14px;">⏳ Pending ({len(pending_files)}):</div>')
                        for f in pending_files:
                            content_html.append(f'<div style="padding: 4px 0; color: #000000 !important; font-family: sans-serif; font-size: 14px;">• ⏳ {html.escape(f)}</div>')
                    
                    files_html = "\n".join(content_html)
                    
                    st.markdown(
                        f"""
                        <div style="
                            max-height: 400px;
                            overflow-y: auto;
                            overflow-x: hidden;
                            padding: 12px;
                            border: 1px solid #e0e0e0;
                            border-radius: 5px;
                            background-color: #ffffff !important;
                            margin-top: 5px;
                        ">
                            {files_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.caption("All files processed!")
            
            # Check if processing is complete
            if status == "completed":
                # Clear job from session state
                del st.session_state.current_job_id
                if "job_output_path" in st.session_state:
                    del st.session_state.job_output_path
                
                if processed_files > 0:
                    st.success(f"✅ Processing Complete! {processed_files} files processed successfully.")
                    if failed_files > 0:
                        st.warning(f"⚠️ {failed_files} files failed to process.")
                    st.info(f"Output saved to: {output_path}")
                    
                    # Download button
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "Download Excel File",
                                data=f.read(),
                                file_name=os.path.basename(output_path),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error("No files were successfully processed.")
            else:
                # Continue polling - wait 2 seconds then rerun
                # This prevents excessive API calls while still providing real-time updates
                time.sleep(2)
                st.rerun()
        else:
            st.error(f"Failed to get progress: {progress_response.status_code}")
            # Clear job on error
            if "current_job_id" in st.session_state:
                del st.session_state.current_job_id
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch progress update: {str(e)}")
        # Retry after delay
        time.sleep(2)
        st.rerun()

if st.button("🚀 Process Resumes", type="primary", use_container_width=True):
    # Clear any existing job state when starting a new process
    if "current_job_id" in st.session_state:
        del st.session_state.current_job_id
    if "job_output_path" in st.session_state:
        del st.session_state.job_output_path
    
    if not input_folder or not os.path.exists(input_folder):
        st.error("Please enter a valid input folder path")
    elif not output_path:
        st.error("Please enter an output path")
    else:
        # Determine if we should append based on output option and whether path is a file or folder
        append_mode = False
        final_output_path = output_path
        
        if output_option == "File Path":
            # Check if the output_path is a file or folder
            if os.path.exists(output_path):
                if os.path.isfile(output_path):
                    # It's an existing file - append to it
                    append_mode = True
                    final_output_path = output_path
                elif os.path.isdir(output_path):
                    # It's a folder - create new file in it
                    final_output_path = os.path.join(output_path, "Parsed_Resume.xlsx")
                    append_mode = False
                else:
                    # Path exists but is neither file nor folder (unlikely)
                    append_mode = False
                    final_output_path = output_path
            else:
                # Path doesn't exist - check if it looks like a file (has extension) or folder
                if output_path.lower().endswith(('.xlsx', '.xls')):
                    # Normalize the path to handle any path issues
                    normalized_path = os.path.normpath(output_path)
                    # Check if file actually exists
                    if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                        # File exists - append to it
                        append_mode = True
                        final_output_path = normalized_path
                    else:
                        # File doesn't exist yet - will create new
                        append_mode = False
                        final_output_path = normalized_path
                else:
                    # Looks like a folder path - create new file
                    final_output_path = os.path.join(output_path, "Parsed_Resume.xlsx")
                    append_mode = False
        else:
            # Folder Path mode - always create new
            append_mode = False
            final_output_path = output_path
        
        # Update output_path for validation and API call
        output_path = final_output_path
        
        # Show info about append mode
        if append_mode:
            st.info(f"Will append data to existing file: {os.path.basename(output_path)}")
        else:
            if os.path.exists(output_path) and os.path.isfile(output_path):
                st.warning(f"File exists but append mode is off. File will be overwritten: {os.path.basename(output_path)}")
        
        # Validate output directory exists
        output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else "."
        if output_dir and not os.path.exists(output_dir):
            st.warning(f"Output directory doesn't exist. Creating: {output_dir}")
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                st.error(f"Cannot create output directory: {str(e)}")
                st.stop()
        
        # Process
        # Use timeout from sidebar configuration
        timeout_seconds = st.session_state.get("request_timeout_minutes", 60) * 60
        
        # Calculate estimated processing time based on number of files
        try:
            num_files = len([f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))])
            estimated_minutes = max(5, num_files * 2)  # Rough estimate: 2 minutes per file, minimum 5 minutes
        except:
            estimated_minutes = 30  # Default estimate if we can't count files
        
        try:
            # Start processing
            response = requests.post(
                f"{BACKEND_URL}/api/process",
                params={
                    "input_folder": input_folder,
                    "output_path": output_path,
                    "append": append_mode
                },
                timeout=30  # Short timeout for initial request
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id")
                
                if job_id:
                    # Store job_id in session state for polling
                    st.session_state.current_job_id = job_id
                    st.session_state.job_output_path = output_path
                    st.rerun()
                else:
                    # Fallback to old behavior if no job_id
                    st.success("✅ " + result.get("message", "Processing started"))
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"❌ Error: {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
            st.info("Make sure the backend server is running!")
            st.code("cd backend\npython -m uvicorn main:app --reload", language="bash")
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. Please try again.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Instructions section
st.divider()
with st.expander("ℹ️ Instructions"):
    st.markdown("""
    ### How to Use:
    
    1. **Input Folder**: Enter the full path to the folder containing your resume files (PDF, DOCX, DOC)
    2. **Output Location**: 
       - **File Path**: Enter exact path including filename (e.g., `C:\\output\\results.xlsx`)
       - **Folder Path**: Enter just the folder path (file will be named `Parsed_Resumes.xlsx`)
    3. Click **Process Resumes** to start processing
    4. Download the Excel file when processing is complete
    
    ### Requirements:
    - Backend server must be running on the specified URL
    - Input folder must exist and contain resume files
    - Output directory will be created if it doesn't exist
    
    ### Notes:
    - Processing time depends on the number of files and API response time
    - Large files may take longer to process
    - The system supports parallel processing with multiple API keys
    """)
