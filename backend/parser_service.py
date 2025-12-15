import os
import fitz
import docx2txt
import pytesseract
import pandas as pd
import requests
import json
import threading
from queue import Queue
import time
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    Retry = None

# Optional import for OCR (requires poppler)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None

# Import configuration
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import (
    PROMPT, GROK_API_KEY, GROK_API_KEYS, GROK_URL, GROK_MODEL,
    MAX_RETRIES, REQUEST_TIMEOUT, RETRY_DELAY
)

# ---- TESSERACT PATH CONFIGURATION ----
def find_tesseract_executable():
    """Try to find Tesseract executable on Windows"""
    import platform
    if platform.system() != "Windows":
        return None
    
    # Common installation paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe"),
    ]
    
    # Also check Downloads folder for any tesseract folder (recursively)
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(downloads_path):
        for item in os.listdir(downloads_path):
            item_path = os.path.join(downloads_path, item)
            if os.path.isdir(item_path) and "tesseract" in item.lower():
                has_source_files = any(
                    os.path.exists(os.path.join(item_path, f)) 
                    for f in [".git", "Makefile", "CMakeLists.txt", "autogen.sh"]
                )
                if has_source_files:
                    continue
                
                tesseract_exe = os.path.join(item_path, "tesseract.exe")
                if os.path.exists(tesseract_exe):
                    possible_paths.append(tesseract_exe)
                
                for root, dirs, files in os.walk(item_path):
                    depth = root[len(item_path):].count(os.sep)
                    if depth > 5:
                        dirs[:] = []
                        continue
                    if "tesseract.exe" in files:
                        tesseract_exe = os.path.join(root, "tesseract.exe")
                        possible_paths.append(tesseract_exe)
                        break
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

# Try to set Tesseract path automatically
tesseract_path = find_tesseract_executable()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"[INFO] Found Tesseract at: {tesseract_path}")
else:
    try:
        pytesseract.get_tesseract_version()
        print("[INFO] Tesseract found in PATH")
    except Exception:
        print("[WARNING] Tesseract not found. OCR functionality may not work.")


# ---- TEXT EXTRACTION ----
def extract_pdf_text(path):
    text = ""
    try:
        doc = fitz.open(path)
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
            
            if len(page_text.strip()) < 50:
                blocks = page.get_text("blocks")
                for block in blocks:
                    if len(block) >= 5:
                        block_text = block[4] if len(block) > 4 else ""
                        if block_text and len(block_text.strip()) > 0:
                            text += block_text + " "
        
        text = text.strip()
    except Exception as e:
        text = ""
        print(f"[DEBUG] PDF extraction error: {str(e)}")

    if text.strip() == "" or len(text) < 30:
        try:
            text = ocr_pdf(path)
        except Exception as e:
            print(f"[DEBUG] OCR fallback failed: {str(e)}")
            pass

    return text

def ocr_pdf(path):
    """OCR PDF without poppler using PyMuPDF built-in rasterizer + tesseract."""
    try:
        from PIL import Image
        import io
        
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            tesseract_path = find_tesseract_executable()
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            else:
                raise Exception("Tesseract OCR is not installed or not in PATH. Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        
        doc = fitz.open(path)
        text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(img, lang="eng")
            text += page_text + "\n"
        return text.strip()
    except Exception as e:
        error_msg = str(e)
        if "tesseract" in error_msg.lower() and "not installed" in error_msg.lower():
            raise Exception(f"Tesseract OCR not found. If you have Tesseract installed, please add it to PATH or set pytesseract.pytesseract.tesseract_cmd to the executable path. Error: {error_msg}")
        raise Exception(f"OCR failed (PyMuPDF method): {error_msg}")

def extract_docx_text(path):
    return docx2txt.process(path)

def extract_doc_text(path):
    """
    Extract text from .doc files (old Microsoft Word format).
    Note: .doc file support requires textract which has dependency issues.
    Users should convert .doc files to .docx or .pdf for best results.
    """
    # .doc files (old Word format) are not directly supported without textract
    # Return empty string with warning - users should convert to .docx or .pdf
    print(f"[WARNING] .doc file format not supported: {os.path.basename(path)}. Please convert to .docx or .pdf format.")
    return ""

def extract_text(path):
    ext = path.lower().split(".")[-1]
    if ext == "pdf":
        return extract_pdf_text(path)
    elif ext == "docx":
        return extract_docx_text(path)
    elif ext == "doc":
        return extract_doc_text(path)
    else:
        return ""


# ---- GROK API CALL ----
def parse_with_grok(text, filename, api_key=None, prompt=None, retry_count=0):
    """Parse resume text using Grok API with retry logic."""
    if api_key is None:
        api_key = GROK_API_KEY
    
    if prompt is None:
        prompt = PROMPT
    
    payload = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "temperature": 0
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    session = requests.Session()
    if Retry is not None:
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

    last_exception = None
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait_time)
            
            response = session.post(
                GROK_URL, 
                headers=headers, 
                json=payload, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            result_data = response.json()
            if "choices" not in result_data or len(result_data["choices"]) == 0:
                raise Exception(f"Unexpected API response format: {result_data}")
            
            result = result_data["choices"][0]["message"]["content"]

            try:
                data = json.loads(result)
            except:
                start = result.find("{")
                end = result.rfind("}") + 1
                data = json.loads(result[start:end])

            data = convert_experience_to_decimal(data)
            data["Resume_File_Name"] = filename
            return data
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                continue
            else:
                raise Exception(f"Request timeout after {MAX_RETRIES + 1} attempts. The API may be slow or the resume is too large. Error: {str(e)}")
        
        except requests.exceptions.ConnectionError as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                continue
            else:
                raise Exception(f"Connection error after {MAX_RETRIES + 1} attempts. Please check your internet connection. Error: {str(e)}")
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code} Error"
            if response.status_code == 404:
                error_msg += ": API endpoint not found. Please verify the Grok API URL is correct."
            elif response.status_code == 401:
                error_msg += ": Invalid API key. Please check your Grok API key."
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    error_msg += f": API key lacks permissions. Error: {error_data}"
                except:
                    error_msg += ": Access forbidden. Please check your API key permissions at console.x.ai"
            elif response.status_code == 429:
                if attempt < MAX_RETRIES:
                    continue
                else:
                    error_msg += ": Rate limit exceeded. Please wait and try again later."
            else:
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
            raise Exception(error_msg) from e
        
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                continue
            else:
                raise Exception(f"Request failed after {MAX_RETRIES + 1} attempts: {str(e)}")
    
    raise Exception(f"Failed after {MAX_RETRIES + 1} attempts. Last error: {str(last_exception)}")


def convert_experience_to_decimal(data):
    """Convert Total_Experience_Years to a decimal number, handling date ranges."""
    import re
    from datetime import datetime
    
    if "Total_Experience_Years" not in data:
        data["Total_Experience_Years"] = 0.0
        return data
    
    exp = data["Total_Experience_Years"]
    
    if isinstance(exp, (int, float)):
        data["Total_Experience_Years"] = float(exp)
        return data
    
    if not exp or exp == "":
        data["Total_Experience_Years"] = 0.0
        return data
    
    exp_str = str(exp).strip()
    
    date_range_patterns = [
        r'(\w{3,9})\s+(\d{4})\s*-\s*(?:Present|Current|Now|Till\s+Date|PRESENT)',
        r'(\w+\s+)?(\d{4})\s*-\s*(?:Present|Current|Now|Till\s+Date|PRESENT)',
        r'(\w+\s+)?(\d{4})\s*-\s*(\w+\s+)?(\d{4})',
        r'(\d{1,2})[/-](\d{4})\s*-\s*(?:Present|Current|Now|PRESENT)',
        r'(\d{1,2})[/-](\d{4})\s*-\s*(\d{1,2})[/-](\d{4})',
    ]
    
    for pattern in date_range_patterns:
        match = re.search(pattern, exp_str, re.IGNORECASE)
        if match:
            try:
                current_date = datetime.now()
                
                if len(match.groups()) >= 2:
                    year_str = match.group(2) if match.group(2) else match.group(1)
                    start_year = int(year_str)
                    
                    month_name = match.group(1) if match.group(1) and len(match.group(1).strip()) > 0 else None
                    start_month = 1
                    if month_name:
                        month_map = {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4,
                            'may': 5, 'june': 6, 'july': 7, 'august': 8,
                            'september': 9, 'october': 10, 'november': 11, 'december': 12,
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month_lower = month_name.strip().lower()
                        if month_lower in month_map:
                            start_month = month_map[month_lower]
                        elif month_name.isdigit():
                            start_month = int(month_name)
                            if start_month < 1 or start_month > 12:
                                start_month = 1
                    
                    if 'present' in exp_str.lower() or 'current' in exp_str.lower() or 'now' in exp_str.lower():
                        end_date = current_date
                    elif len(match.groups()) >= 4 and match.group(4):
                        end_year = int(match.group(4))
                        end_month = int(match.group(3)) if match.group(3) and match.group(3).isdigit() else 12
                        end_date = datetime(end_year, end_month, 1)
                    else:
                        end_date = current_date
                    
                    start_date = datetime(start_year, start_month, 1)
                    delta = end_date - start_date
                    years = delta.days / 365.25
                    
                    data["Total_Experience_Years"] = round(years, 2)
                    return data
            except (ValueError, AttributeError):
                continue
    
    exp_str_lower = exp_str.lower()
    exp_str_clean = exp_str_lower.replace("years", "").replace("year", "").replace("yrs", "").replace("yr", "")
    exp_str_clean = exp_str_clean.replace("months", "").replace("month", "").replace("mos", "").replace("mo", "")
    exp_str_clean = exp_str_clean.replace("+", "").strip()
    
    years_match = re.search(r'(\d+(?:\.\d+)?)', exp_str_clean)
    if years_match:
        years = float(years_match.group(1))
        
        months_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:month|mo)', exp_str_lower, re.IGNORECASE)
        if months_match:
            months = float(months_match.group(1))
            years += months / 12.0
        
        data["Total_Experience_Years"] = round(years, 2)
        return data
    
    data["Total_Experience_Years"] = 0.0
    return data


# ---- PARALLEL PROCESSING ----
def process_single_file(filename, folder, api_key, prompt, status_callback):
    """Process a single resume file and return the result."""
    path = os.path.join(folder, filename)
    text = extract_text(path)

    if len(text.strip()) == 0:
        if status_callback:
            status_callback(f"[INFO] No text extracted from {filename}. Attempting OCR (this may take a moment)...")
        
        if not PDF2IMAGE_AVAILABLE:
            if status_callback:
                status_callback(f"[ERROR] OCR not available for {filename}: pdf2image library not installed. Install with: pip install pdf2image")
            return None
        
        try:
            if status_callback:
                status_callback(f"[INFO] Converting PDF to images for OCR...")
            ocr_text = ocr_pdf(path)
            
            if ocr_text and len(ocr_text.strip()) > 10:
                text = ocr_text
                if status_callback:
                    status_callback(f"[SUCCESS] OCR extracted {len(ocr_text.strip())} characters from {filename}")
            else:
                if status_callback:
                    status_callback(f"[WARNING] OCR did not extract sufficient text from {filename} (got {len(ocr_text.strip()) if ocr_text else 0} chars). This PDF may be corrupted or unreadable.")
                return None
        except Exception as e:
            error_msg = str(e)
            if status_callback:
                if "poppler" in error_msg.lower() or "Unable to get page count" in error_msg:
                    status_callback(f"[ERROR] OCR failed for {filename}: Poppler not properly configured. Error: {error_msg}")
                    status_callback(f"[INFO] Install Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
                elif "TesseractNotFoundError" in error_msg or "tesseract" in error_msg.lower():
                    status_callback(f"[ERROR] OCR failed for {filename}: Tesseract OCR not found. Please install Tesseract OCR.")
                else:
                    status_callback(f"[ERROR] OCR failed for {filename}: {error_msg}")
            return None
    
    elif len(text.strip()) < 50:
        if status_callback:
            status_callback(f"[INFO] Text extraction returned very little text ({len(text.strip())} chars) for {filename}. Attempting OCR...")
        try:
            ocr_text = ocr_pdf(path)
            if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                if status_callback:
                    status_callback(f"[SUCCESS] OCR extracted better text from {filename}")
            else:
                if status_callback:
                    status_callback(f"[WARNING] OCR did not improve text extraction for {filename}")
        except Exception as e:
            if status_callback:
                status_callback(f"[WARNING] OCR attempt failed for {filename}: {str(e)}. Using extracted text.")

    try:
        result = parse_with_grok(text, filename, api_key=api_key, prompt=prompt)
        return result
    except Exception as e:
        if status_callback:
            status_callback(f"[ERROR] Failed to parse {filename}: {str(e)}")
        return None


def worker_thread(file_queue, result_list, folder, api_key, prompt, progress_callback, status_callback, total_files, lock):
    """Worker thread that processes files from the queue."""
    while True:
        item = file_queue.get()
        if item is None:
            break
        
        idx, filename = item
        
        if status_callback:
            status_callback(f"Processing: {filename} ({idx}/{total_files}) [Worker {threading.current_thread().name}]")
        
        try:
            result = process_single_file(filename, folder, api_key, prompt, status_callback)
            
            if result:
                with lock:
                    result_list.append(result)
                if status_callback:
                    status_callback(f"[SUCCESS] Parsed {filename}")
            else:
                if status_callback:
                    status_callback(f"[WARNING] Skipped {filename} (extraction or parsing failed)")
        except Exception as e:
            if status_callback:
                status_callback(f"[ERROR] Failed to process {filename}: {str(e)}")
        
        if progress_callback:
            progress_callback(idx, total_files)
        
        file_queue.task_done()


def process_parallel(files, folder, api_keys, prompt, progress_callback, status_callback, total_files):
    """Process files in parallel using multiple API keys."""
    file_queue = Queue()
    result_list = []
    lock = threading.Lock()
    threads = []
    
    for idx, f in enumerate(files, 1):
        file_queue.put((idx, f))
    
    for i, api_key in enumerate(api_keys):
        thread = threading.Thread(
            target=worker_thread,
            args=(file_queue, result_list, folder, api_key, prompt, progress_callback, status_callback, total_files, lock),
            name=f"Worker-{i+1}",
            daemon=True
        )
        thread.start()
        threads.append(thread)
    
    file_queue.join()
    
    for _ in threads:
        file_queue.put(None)
    
    for thread in threads:
        thread.join()
    
    return result_list


# ---- PROCESS FOLDER ----
def process_folder(folder, output_path=None, progress_callback=None, status_callback=None, api_key=None, prompt=None, append=False):
    """
    Process all resumes in a folder and save to output path.
    
    Args:
        folder: Path to folder containing resume files
        output_path: Path where output Excel file should be saved (default: "Parsed_Resumes.xlsx")
        progress_callback: Optional function to call with progress updates (current, total)
        status_callback: Optional function to call with status messages
        api_key: Grok API key (if None, uses global GROK_API_KEY)
        prompt: Custom prompt (if None, uses global PROMPT)
        append: If True, append to existing file. If False, create new file.
    """
    if output_path is None:
        output_path = "Parsed_Resumes.xlsx"
    
    if not os.path.exists(folder):
        msg = f"[ERROR] Folder '{folder}' does not exist."
        if status_callback:
            status_callback(msg)
        return False, msg
    
    if not os.path.isdir(folder):
        msg = f"[ERROR] '{folder}' is not a directory."
        if status_callback:
            status_callback(msg)
        return False, msg
    
    rows = []
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    
    if len(files) == 0:
        msg = "[INFO] No resume files found in the folder."
        if status_callback:
            status_callback(msg)
        return False, msg
    
    total_files = len(files)
    
    api_keys_to_use = GROK_API_KEYS if GROK_API_KEYS else ([api_key] if api_key else [GROK_API_KEY])
    num_workers = min(len(api_keys_to_use), total_files)
    
    if num_workers > 1:
        if status_callback:
            status_callback(f"[INFO] Using {num_workers} parallel workers for faster processing...")
        rows = process_parallel(files, folder, api_keys_to_use, prompt, progress_callback, status_callback, total_files)
    else:
        for idx, f in enumerate(files, 1):
            if progress_callback:
                progress_callback(idx, total_files)
            
            if status_callback:
                status_callback(f"Processing: {f} ({idx}/{total_files})")
            
            result = process_single_file(f, folder, api_keys_to_use[0] if api_keys_to_use else api_key, prompt, status_callback)
            if result:
                rows.append(result)

    if len(rows) == 0:
        msg = "[ERROR] No resumes were successfully parsed."
        if status_callback:
            status_callback(msg)
        return False, msg
    
    try:
        # If append is True and file exists, append to it
        if append and os.path.isfile(output_path) and output_path.lower().endswith(('.xlsx', '.xls')):
            if status_callback:
                status_callback(f"[INFO] Appending to existing Excel file: {os.path.basename(output_path)}")
            
            try:
                existing_df = pd.read_excel(output_path)
                if status_callback:
                    status_callback(f"[INFO] Found {len(existing_df)} existing records in file")
                
                new_df = pd.DataFrame(rows)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(output_path, index=False)
                msg = f"[SUCCESS] Parsing Complete! Appended {len(rows)} new resumes to existing file. Total records: {len(combined_df)}"
            except Exception as e:
                if status_callback:
                    status_callback(f"[WARNING] Could not read existing file: {str(e)}. Creating new file instead.")
                df = pd.DataFrame(rows)
                df.to_excel(output_path, index=False)
                msg = f"[SUCCESS] Parsing Complete! Saved {len(rows)} resumes to {output_path}"
        else:
            # Create new file (either append=False or file doesn't exist)
            if status_callback:
                if os.path.isfile(output_path):
                    status_callback(f"[INFO] Creating new Excel file (overwriting existing): {os.path.basename(output_path)}")
                else:
                    status_callback(f"[INFO] Creating new Excel file: {os.path.basename(output_path)}")
            df = pd.DataFrame(rows)
            df.to_excel(output_path, index=False)
            msg = f"[SUCCESS] Parsing Complete! Saved {len(rows)} resumes to {output_path}"
        
        if status_callback:
            status_callback(msg)
        return True, msg
    except Exception as e:
        msg = f"[ERROR] Failed to save output file: {str(e)}"
        if status_callback:
            status_callback(msg)
        return False, msg
