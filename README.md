# Resume Parser - Backend & Frontend

A web-based resume parsing application with FastAPI backend and Streamlit frontend.

## Project Structure

```
parsed resume/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI server
│   ├── parser_service.py    # Core parsing logic
│   └── config.py            # Configuration
├── frontend/
│   ├── __init__.py
│   └── app.py               # Streamlit UI
├── grok_resume_prompt.txt   # AI prompt configuration
├── requirements.txt
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `backend/config.py` and add your Grok API keys:

```python
GROK_API_KEYS = [
    "your-api-key-1",
    "your-api-key-2"
]
```

### 3. Run the Application

#### Option A: Run Separately (Recommended for Development)

**Terminal 1 - Backend (from project root):**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```

#### Option B: Run with Scripts

**Windows (`run.bat`):**
```batch
@echo off
start cmd /k "cd backend && python -m uvicorn main:app --reload --port 8000"
timeout /t 3
cd frontend
streamlit run app.py
```

**Linux/Mac (`run.sh`):**
```bash
#!/bin/bash
cd backend && python -m uvicorn main:app --reload --port 8000 &
sleep 3
cd ../frontend && streamlit run app.py
```

## Usage

1. **Start Backend**: Run the FastAPI server (default: http://localhost:8000)
2. **Start Frontend**: Run Streamlit app (default: http://localhost:8501)
3. **Open Browser**: Navigate to http://localhost:8501
4. **Select Input Folder**: Enter the path to folder containing resume files
5. **Select Output Location**: Enter output file path or folder
6. **Process**: Click "Process Resumes" button
7. **Download**: Download the generated Excel file

## API Endpoints

### POST `/api/process`
Process resumes from a folder.

**Parameters:**
- `input_folder` (query): Path to folder containing resume files
- `output_path` (query): Path where output Excel file should be saved

**Response:**
```json
{
    "status": "success",
    "message": "Parsing Complete! Saved 5 resumes to output.xlsx",
    "output_path": "C:\\output\\output.xlsx"
}
```

### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "Resume Parser API"
}
```

## Features

- ✅ PDF, DOCX, DOC file support
- ✅ OCR support for scanned documents
- ✅ Parallel processing with multiple API keys
- ✅ Excel output with structured data
- ✅ Web-based UI
- ✅ Local file storage

## Hosting

### Quick Start - Render.com (Recommended) 🚀

**Deploy to Render in 5 minutes!**

See **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)** for step-by-step Render deployment instructions.

Or check **[README_RENDER.md](README_RENDER.md)** for a quick reference.

### Other Options

See **[QUICK_START_HOSTING.md](QUICK_START_HOSTING.md)** for Railway and other platforms.

### Docker (Local)

```bash
# Create .env file with your API keys
echo "GROK_API_KEYS=your-key-1,your-key-2" > .env
echo "BACKEND_URL=http://localhost:8000" >> .env

# Run with Docker Compose
docker-compose up -d
```

### Cloud Hosting Options

- **Railway** - Easiest, auto-deploy from GitHub
- **Render** - Simple Docker hosting
- **Fly.io** - Global edge deployment
- **DigitalOcean** - App Platform or Droplets
- **AWS/GCP/Azure** - Enterprise solutions
- **VPS** - Full control (DigitalOcean, Linode, etc.)

See **[HOSTING_GUIDE.md](HOSTING_GUIDE.md)** for detailed instructions on all platforms.

## Troubleshooting

### Backend not connecting
- Check if backend is running on port 8000
- Verify BACKEND_URL in frontend matches backend URL
- Check firewall settings

### OCR not working
- Install Tesseract OCR
- For Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Ensure Tesseract is in PATH or configure path in code

### API errors
- Verify API keys are correct
- Check API key permissions at console.x.ai
- Ensure internet connection is active

## License

MIT
