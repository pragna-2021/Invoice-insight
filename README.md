# Invoice Insight

Invoice Insight is an AI-powered invoice processing and analytics platform built using FastAPI, Tesseract OCR, OpenCV, and Bootstrap 5.

The system extracts structured data from invoice images and PDF files, supports multilingual OCR (English and Russian), stores invoice analytics in a database, and provides a dashboard for visualization, export, and inspection.

---

# Features

- JWT Authentication System
- Invoice Upload (PNG / JPG / PDF)
- OCR Extraction using Tesseract
- Multi-language Support (English + Russian)
- Automatic Translation (Russian → English)
- Structured Invoice Parsing
- Analytics Dashboard
- OCR Accuracy Tracking
- Export Analytics as CSV/JSON

---

# System Architecture

```text
+----------------------+       +--------------------------+       +------------------------+
|   Front-end (SPA)    | <---> |  FastAPI Backend (API)   | <---> |  PostgreSQL / MySQL   |
|   (HTML + Bootstrap) |       |  • Auth (JWT)            |       |  (via SQLAlchemy)     |
|   • Vanilla JS       |       |  • OCR Pipeline          |       +------------------------+
|   • Chart.js         |       |  • Analytics             |
+----------------------+       +--------------------------+
                                   |
                                   v
                         +------------------------------+
                         |  Tesseract OCR + OpenCV      |
                         |  Translation Service         |
                         +------------------------------+
```

---

# Technology Stack

## Frontend
- HTML5
- CSS3
- Bootstrap 5
- Vanilla JavaScript
- Chart.js

## Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- Uvicorn
- JWT Authentication

## OCR & Processing
- Tesseract OCR 5.x
- pytesseract
- OpenCV
- PyMuPDF
- deep-translator

## Database
- SQLite (Development)
- MySQL / PostgreSQL (Production)

## Security
- passlib (bcrypt)
- JWT (HS256)

---

# Project Structure

```text
invoice-insight/
│
├── backend/
│   ├── __pycache__/
│   ├── routers/
│   ├── services/
│   ├── tessdata/
│
├── docs/
│   └── screenshots/
│       ├── Analytics.png
│       ├── Export.png
│       ├── History.png
│       ├── Login.png
│       ├── Structure.png
│       └── Upload.png
│
├── frontend/
│   ├── __pycache__/
│   ├── pages/
│   └── static/
│
├── start_backend.bat
└── README.md
```

---

# Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/invoice-insight.git
cd invoice-insight
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Install Tesseract OCR

## Windows

1. Download and install Tesseract OCR
2. Add Tesseract to PATH

Example:

```text
C:\Program Files\Tesseract-OCR\
```

---

## Linux

```bash
sudo apt install tesseract-ocr
```

---

# Run the Project

## Start Backend

```bash
uvicorn backend.main:app --reload
```

OR

```bash
.\start_backend.bat
```

---

# Open Application

```text
http://127.0.0.1:8000
```

---

# Authentication Flow

## Register

```http
POST /api/auth/register
```

## Login

```http
POST /api/auth/login
```

Response:

```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

---

# Invoice Processing Workflow

1. User uploads invoice image or PDF
2. PDF files are converted into images using PyMuPDF
3. OpenCV preprocesses the image
4. Tesseract extracts text from the document
5. Language detection checks for Cyrillic characters
6. Russian text is translated into English
7. Structured data is extracted:
   - Vendor Name
   - Invoice Number
   - Date
   - Total Amount
   - Line Items
8. Data is stored in the database
9. Analytics and metrics are generated

---

# Analytics Features

- OCR Accuracy Tracking
- Success / Failure Rate Analysis
- Invoice Processing Metrics
- Language Distribution
- CSV / JSON Export
- Interactive Charts using Chart.js

---

# Security Features

- Password hashing using bcrypt
- JWT-based authentication
- Protected API routes
- CORS configuration
- Stateless authentication

---

# OCR Engine Features

## Supported Languages

- English (`eng`)
- Russian (`rus`)

## OCR Pipeline

- Grayscale conversion
- Image threshold preprocessing
- OCR confidence score calculation
- Translation support

---

# Database Configuration

Default Database:

```python
SQLite
```

Production Database Example:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
```

---

# Deployment

## Recommended Production Stack

- FastAPI + Gunicorn
- NGINX Reverse Proxy
- MySQL/PostgreSQL
- Docker
- HTTPS via Let's Encrypt

---

# Future Improvements

- React / TypeScript Frontend
- Docker Compose Setup
- Kubernetes Deployment
- AI-based Invoice Classification
- Additional Language Support
- Email Invoice Parsing
- Cloud Storage Integration

---

# Application Screenshots

## Login Page

<p align="center">
  <img src="docs/screenshots/Login.png" width="900">
</p>

---

## Upload Interface

<p align="center">
  <img src="docs/screenshots/Upload.png" width="900">
</p>

---

## Structured Invoice Output

<p align="center">
  <img src="docs/screenshots/Structure.png" width="900">
</p>

---

## Invoice History

<p align="center">
  <img src="docs/screenshots/History.png" width="900">
</p>

---

## Analytics Dashboard

<p align="center">
  <img src="docs/screenshots/Analytics.png" width="900">
</p>

---

## Export Functionality

<p align="center">
  <img src="docs/screenshots/Export.png" width="900">
</p>

---


