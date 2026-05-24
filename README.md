# Invoice Insight

Invoice Insight is an AI-powered invoice processing and analytics platform built using FastAPI, Tesseract OCR, OpenCV, and Bootstrap 5.  
The system extracts structured data from invoice images/PDFs, supports multilingual OCR (English + Russian), stores invoice analytics in a database, and provides a dashboard for visualization and inspection.

---

# Features

- JWT Authentication System
- Invoice Upload (PNG / JPG / PDF)
- OCR Extraction using Tesseract
- Multi-language Support (English + Russian)
- Automatic Translation (Russian → English)
- Performance Analytics Dashboard
- Structured Invoice Parsing
- Export Analytics as CSV/JSON
- Modern Dark UI with Glassmorphism
- Accuracy Tracking & Metrics

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
- MySQL (Production)

## Security
- passlib (bcrypt)
- JWT (HS256)

---

# Project Structure

```text
invoice-insight/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── security.py
│   ├── database.py
│   ├── models.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── upload.py
│   │   └── analytics.py
│   │
│   └── services/
│       ├── ocr_engine.py
│       ├── pdf_handler.py
│       └── structurer.py
│
├── frontend/
│   └── static/
│       ├── index.html
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
│
├── requirements.txt
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
1. Download Tesseract OCR
2. Install it
3. Add Tesseract to PATH

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

Returns:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

---

# Invoice Processing Flow

1. User uploads invoice image/PDF
2. PDF converted into images using PyMuPDF
3. OpenCV preprocesses images
4. Tesseract extracts text
5. Language detection checks for Cyrillic text
6. Russian text translated into English
7. Structurer extracts:
   - Vendor
   - Invoice Number
   - Date
   - Total Amount
   - Line Items
8. Structured data stored in database
9. Analytics generated from stored invoices

---

# Analytics Features

- OCR Accuracy Tracking
- Invoice Processing Metrics
- Success / Failure Rates
- Language Distribution
- Export CSV / JSON Reports
- Chart.js Visualizations

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
- Threshold preprocessing
- Confidence score calculation
- Translation support

---

# Database Configuration

Default:
```python
SQLite
```

Production:
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
- Multi-language Expansion
- Email Invoice Parsing
- Cloud Storage Integration

---

# Screenshots

Add screenshots here:

```text
/docs/screenshots/dashboard.png
/docs/screenshots/upload.png
/docs/screenshots/analytics.png
```

---

# Contributing

Pull requests are welcome.

Steps:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push branch
5. Open Pull Request

---

# License

MIT License

---

# Author

Developed by Your Name

---

# Support

If you found this project useful:

- Star the repository
- Fork the project
- Share feedback

---
