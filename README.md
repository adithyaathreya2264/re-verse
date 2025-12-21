#  RE-VERSE

**Transform PDF Documents into AI-Generated Podcasts**

RE-VERSE is an AI-powered web application that converts PDF documents into engaging, multi-speaker audio podcasts using advanced language models and text-to-speech technology.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## ✨ Features

### Core Functionality
- 📄 **PDF Processing** - Extract and analyze content from PDF documents
- 🤖 **AI Script Generation** - Generate natural dialogue using Groq's Llama 3.1 model
- 🎭 **Multiple Conversation Styles**:
  - Student-Professor
  - Critique
  - Debate
  - Interview
  - Casual Explainer
  - Storytelling
- 🎙️ **Multi-Speaker Audio** - Realistic text-to-speech with different voices
- ⏱️ **Flexible Duration** - Short (~3-5 min), Medium (~5-8 min), or Long (~8-12 min)
- 📚 **History Sidebar** - ChatGPT-style interface to access previous podcasts
- ☁️ **Cloud Storage** - Secure audio file storage on Google Cloud Storage

### Technical Features
- ⚡ **Asynchronous Processing** - Non-blocking job queue system
- 🔄 **Real-time Status Updates** - Live progress tracking with polling
- 🎨 **Modern UI** - Responsive design with gradient themes
- 🔐 **Secure** - Environment-based secrets management
- 📊 **MongoDB Integration** - Persistent job storage and history

---

## 🎬 Demo

![RE-VERSE Demo](docs/demo.gif)

**Live Demo:** [https://re-verse.onrender.com](https://re-verse.onrender.com) _(if deployed)_

---

## 🏗️ Architecture

```
┌─────────────────┐
│ Frontend │ HTML/CSS/JavaScript
│ (Static) │ User Interface
└────────┬────────┘
│
▼
┌─────────────────┐
│ FastAPI │ Python Backend
│ REST API │ Job Management
└────────┬────────┘
│
├──────────────┬──────────────┬──────────────┐
▼ ▼ ▼ ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ MongoDB │ │ Groq │ │ Google │ │ Google │
│ Atlas │ │ API │ │ Cloud │ │ Cloud │
│ (Jobs) │ │ (Script) │ │ TTS │ │ Storage │
└─────────────┘ └──────────┘ └──────────┘ └──────────┘
```

**Processing Flow:**
1. User uploads PDF + customization options
2. Backend extracts text from PDF
3. Groq AI generates podcast script
4. Google TTS creates multi-speaker audio
5. Audio uploaded to GCS
6. Download link returned to user

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI 0.104+
- **Language:** Python 3.11+
- **Server:** Uvicorn (ASGI)
- **PDF Processing:** PyPDF2
- **Audio Processing:** FFmpeg

### AI & Cloud Services
- **Script Generation:** Groq API (Llama 3.1-70B)
- **Text-to-Speech:** Google Cloud Text-to-Speech (Neural2 voices)
- **Storage:** Google Cloud Storage
- **Database:** MongoDB Atlas

### Frontend
- **HTML5/CSS3** with modern gradients
- **Vanilla JavaScript** (no framework dependencies)
- **Responsive Design** (mobile-friendly)

### DevOps
- **Environment Management:** python-dotenv
- **Logging:** Python logging module
- **Deployment:** Render/Railway/Fly.io compatible

---

## 📋 Prerequisites

Before installation, ensure you have:

### Required Accounts
- **Google Cloud Platform** account with:
  - Text-to-Speech API enabled
  - Cloud Storage API enabled
  - Service account with JSON credentials
- **Groq API** account and API key
- **MongoDB Atlas** account (free tier works)

### Required Software
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **FFmpeg** ([Installation Guide](https://ffmpeg.org/download.html))
- **Git** ([Download](https://git-scm.com/downloads))

---

## 🚀 Installation

### 1. Clone the Repository
```
git clone https://github.com/YOUR_USERNAME/re-verse.git
cd re-verse
```

### 2. Create Virtual Environment

- **Windows**
```
python -m venv .venv
.venv\Scripts\activate
```
- **macOS/Linux**
```
python3 -m venv .venv
source .venv/bin/activate
```


### 3. Install Dependencies
```
pip install -r requirements.txt
```


### 4. Install FFmpeg

**Windows (using Chocolatey):**
```
choco install ffmpeg
```


**Linux (Ubuntu/Debian):**
```
sudo apt update
sudo apt install ffmpeg
```

Verify installation:
```
ffmpeg -version
```


---

## ⚙️ Configuration

### 1. Create `.env` File

Copy the example and fill in your credentials:
```
cp .env.example .env
```


### 2. Environment Variables

Edit `.env` with your actual values:
```

### 2. Environment Variables

Edit `.env` with your actual values:
```


### 3. Google Cloud Setup

**Create Service Account:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (or select existing)
3. Enable **Text-to-Speech API** and **Cloud Storage API**
4. Create Service Account → Download JSON key
5. Save as `gcs-credentials.json` in project root
6. Create Cloud Storage bucket and set public access

**Set Permissions:**
Grant service account access to bucket
gsutil iam ch serviceAccount:YOUR-SERVICE-ACCOUNT@PROJECT.iam.gserviceaccount.com:objectAdmin gs://your-bucket-name


### 4. MongoDB Atlas Setup

1. Create free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create database user
3. Whitelist your IP (or use 0.0.0.0/0 for all IPs)
4. Copy connection string to `.env`

---

## 💻 Usage

### Running Locally
Activate virtual environment
```
.venv\Scripts\activate # Windows
source .venv/bin/activate # macOS/Linux
```

Start the server
```
python run.py
```

Server will start at: [**http://localhost:8000**](http://localhost:8000)

### Using the Application

1. **Upload PDF** - Select a PDF document (max 50MB)
2. **Set Focus** - Describe what the podcast should emphasize
3. **Choose Style** - Select conversation style (debate, interview, etc.)
4. **Select Duration** - Pick short, medium, or long format
5. **Generate** - Click "Generate Podcast" and wait
6. **Listen & Download** - Play audio in browser or download MP3

### API Usage

**Create Podcast:**
curl -X POST "http://localhost:8000/api/v1/generate-job"
-F "file=@document.pdf"
-F "prompt=Focus on key concepts"
-F "style=CASUAL_EXPLAINER"
-F "duration=MEDIUM"


**Check Status:**
curl "http://localhost:8000/api/v1/job/{job_id}"


---

## 📚 API Documentation

### Interactive Docs

Once running, visit:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Endpoints
```
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate-job` | Upload PDF and create generation job |
| `GET` | `/api/v1/job/{job_id}` | Get job status and result |
| `GET` | `/api/v1/history?job_ids=...` | Get multiple jobs by IDs |
| `GET` | `/health` | Health check endpoint |
```
### Response Codes
```
| Code | Meaning |
|------|---------|
| `202` | Job created successfully |
| `200` | Success |
| `400` | Invalid request |
| `404` | Job not found |
| `422` | Validation error |
| `500` | Server error |
```
---

## 📁 Project Structure
```
re-verse/
├── app/
│ ├── api/
│ │ └── v1/
│ │ └── routes/
│ │ └── job_routes.py # API endpoints
│ ├── core/
│ │ └── config.py # Configuration management
│ ├── db/
│ │ ├── mongodb.py # Database connection
│ │ └── operations/
│ │ └── job_operations.py # Database operations
│ ├── models/
│ │ ├── enums.py # Enums (status, style, etc.)
│ │ └── job_model.py # Pydantic models
│ ├── services/
│ │ ├── ai_worker.py # Background job processor
│ │ ├── gcs_service.py # Google Cloud Storage
│ │ ├── pdf_service.py # PDF text extraction
│ │ ├── script_generator.py # AI script generation
│ │ └── tts_service.py # Text-to-speech
│ ├── utils/
│ │ └── logger.py # Logging configuration
│ └── main.py # FastAPI application
├── static/
│ ├── index.html # Frontend UI
│ ├── style.css # Styling
│ └── app.js # Frontend logic
├── .env # Environment variables (not in repo)
├── .gitignore # Git ignore rules
├── requirements.txt # Python dependencies
├── run.py # Entry point
├── Procfile # Deployment config
└── README.md # This file
```


---

## 🚢 Deployment

### Deploy to Render

1. **Push to GitHub:**
```
git add .
git commit -m "Ready for deployment"
git push origin main
```


2. **Create Render Service:**
   - Go to [Render.com](https://render.com/)
   - New → Web Service
   - Connect GitHub repository
   - Configure:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables** in Render dashboard (same as `.env`)

4. **Deploy!**

### Deploy to Railway

Similar process - connect GitHub, set environment variables, deploy.

### Deploy to Fly.io
```
fly launch
fly secrets set MONGODB_URL=... GROQ_API_KEY=...
fly deploy
```


---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to functions
- Write tests for new features
- Update documentation

---

## 🐛 Troubleshooting

### Common Issues

**1. FFmpeg Not Found**
```
Error: [WinError 2] The system cannot find the file specified
```

**Solution:** Install FFmpeg and add to PATH ([see Installation](#installation))

**2. MongoDB Connection Failed**
```
Error: Could not connect to MongoDB
```

**Solution:** 
- Check connection string in `.env`
- Whitelist your IP in MongoDB Atlas
- Verify network connectivity

**3. Google Cloud Authentication Error**
```
Error: Could not authenticate with Google Cloud
```
**Solution:**
- Verify `gcs-credentials.json` exists
- Check service account has correct permissions
- Enable required APIs in Google Cloud Console

**4. Large PDF Processing Timeout**
```
Error: Job failed after timeout
```
**Solution:**
- Use smaller PDFs (< 50 pages)
- Increase timeout in `config.py`
- Use paid hosting tier with longer timeouts

### Getting Help

- **Issues:** Open an issue on GitHub
- **Discussions:** Use GitHub Discussions
- **Email:** your-email@example.com

---

## 📊 Usage Limits

| Service | Free Tier Limit |
|---------|----------------|
| Google TTS | 1M characters/month (~60-200 podcasts) |
| Google Cloud Storage | 5 GB storage |
| MongoDB Atlas | 512 MB storage |
| Groq API | Generous (varies) |

After free tier, costs start at ~$16/million TTS characters.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👏 Acknowledgments

- **Groq** for fast AI inference
- **Google Cloud** for TTS and storage
- **FastAPI** for the amazing web framework
- **MongoDB** for database services
- **FFmpeg** for audio processing

---

## 📧 Contact

**Your Name** - [@yourtwitter](https://twitter.com/yourtwitter)

**Project Link:** [https://github.com/YOUR_USERNAME/re-verse](https://github.com/YOUR_USERNAME/re-verse)

---

## 🗺️ Roadmap

- [ ] User authentication system
- [ ] Payment integration for premium features
- [ ] Additional voice options
- [ ] Support for more file formats (DOCX, TXT)
- [ ] Podcast editing capabilities
- [ ] Custom voice cloning
- [ ] Mobile app (React Native)
- [ ] Podcast RSS feed generation

---

**Built by Adithya Athreya**

*Transform your documents into engaging audio experiences!*

### Additional Files to Create:
1. .env.example (Template for users)
```
# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=reverse_db

# Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=./gcs-credentials.json

# Groq API
GROQ_API_KEY=gsk_your_api_key_here

# API Settings
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:8000

# Server Configuration
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO

# File Upload Limits
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf
```
