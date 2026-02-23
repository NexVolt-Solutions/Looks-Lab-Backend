# Looks Lab Backend API

> **AI-Powered Personal Wellness Platform**  
> FastAPI backend providing personalized wellness insights across 8 domains: skincare, haircare, diet, fitness, fashion, height, facial, and behavioral wellness.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/looks-lab-backend.git
cd looks-lab-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb looks_lab
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

**API Documentation:** http://localhost:8000/docs

---

## ✨ Key Features

- **Anonymous Onboarding** - Complete onboarding before authentication
- **AI-Powered Analysis** - Google Gemini integration for personalized insights
- **Multi-Domain Support** - 8 specialized wellness domains
- **OAuth Authentication** - Google & Apple Sign-In
- **Smart Recommendations** - AI-generated workout plans and meal plans
- **Image Analysis** - Food scanning, skin analysis, facial analysis
- **Real-time Progress** - Track wellness metrics across all domains

---

## 🏗 Architecture

```
Client (Mobile/Web)
    ↓ HTTPS
FastAPI Application
    ↓
Service Layer (Business Logic)
    ↓
Data Layer (SQLAlchemy ORM)
    ↓
PostgreSQL | AWS S3 | Google Gemini API
```

---

## 📋 Tech Stack

**Core:** FastAPI, Python 3.12, Pydantic, SQLAlchemy 2.0  
**Database:** PostgreSQL 16, Alembic, asyncpg  
**Auth:** OAuth 2.0, JWT, Google/Apple Sign-In  
**AI:** Google Gemini 3 Flash Preview  
**Storage:** AWS S3, Boto3  
**Tools:** Uvicorn, HTTPX, Slowapi (rate limiting)

---

## ⚙️ Environment Setup

Create `.env` file:

```env
# Database
DATABASE_URI=postgresql+asyncpg://looks_lab:password@localhost:5432/looks_lab

# Security
JWT_SECRET=your-secret-key-here
JWT_REFRESH_SECRET=your-refresh-secret-here

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
APPLE_CLIENT_ID=your-apple-client-id

# AI
GEMINI_API_KEY=your-gemini-api-key

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=looks-lab-images

# App
ENVIRONMENT=development
DEBUG=true
```

---

## 📚 API Endpoints

### Authentication
```
POST /api/v1/auth/google          # Google Sign-In
POST /api/v1/auth/apple           # Apple Sign-In
POST /api/v1/auth/refresh         # Refresh token
POST /api/v1/auth/sign-out        # Sign out
```

### Onboarding (Anonymous)
```
POST  /api/v1/onboarding/sessions              # Create session
GET   /api/v1/onboarding/sessions/{id}/flow    # Get current question
POST  /api/v1/onboarding/sessions/{id}/answers # Submit answer
PATCH /api/v1/onboarding/sessions/{id}/domain  # Select domain
PATCH /api/v1/onboarding/sessions/{id}/link    # Link to user (auth required)
```

### AI Features
```
POST /api/v1/domains/workout/generate-plan     # Generate workout plan
POST /api/v1/domains/diet/generate-meal-plan   # Generate meal plan
POST /api/v1/domains/diet/foods/analyze        # Analyze food image
GET  /api/v1/domains/diet/foods/barcode/{code} # Scan barcode
```

### Domains
```
GET  /api/v1/domains/{domain}/questions        # Get questions
POST /api/v1/domains/{domain}/answers          # Submit answers
GET  /api/v1/domains/{domain}/progress         # Get progress
GET  /api/v1/domains/progress/overview         # All domains progress
```

**Valid domains:** `skincare`, `haircare`, `workout`, `diet`, `fashion`, `height`, `facial`, `quit_porn`

---

## 📁 Project Structure

```
looks-lab-backend/
├── app/
│   ├── api/v1/routes/        # API endpoints
│   │   ├── auth.py           # Authentication
│   │   ├── onboarding.py     # Onboarding flow
│   │   ├── domains.py        # Generic domain routes
│   │   ├── workout.py        # Workout AI
│   │   ├── diet.py           # Diet AI
│   │   └── ...
│   ├── core/                 # Core config, database, logging
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── utils/                # Helper functions
│   └── main.py               # FastAPI app
├── alembic/                  # Database migrations
├── .env                      # Environment variables
├── requirements.txt          # Dependencies
└── README.md
```

---

## 🔧 Development

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality
```bash
# Format code
black app/

# Lint
ruff check app/
```

### Testing
Import Postman collection: `Looks_Lab_API.postman_collection.json`

---

## 📱 Mobile Integration

### Anonymous Onboarding Flow
1. Create session (no auth)
2. Answer questions
3. Select domain
4. Confirm payment
5. Sign in with Google/Apple
6. Link session to user account

### In-App Purchases
- **iOS:** Apple In-App Purchases
- **Android:** Google Play Billing
- **Recommended:** Use RevenueCat for cross-platform management

---

## 🚢 Production Deployment

1. **Set production environment**
   ```env
   ENVIRONMENT=production
   DEBUG=false
   ```

2. **Generate secure secrets**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Configure CORS**
   ```env
   ALLOWED_ORIGINS=https://your-app.com
   ```

4. **Health check**
   ```bash
   curl https://api.your-domain.com/health
   ```

---

## 📊 API Features Roadmap

- [x] Anonymous onboarding
- [x] OAuth authentication (Google & Apple)
- [x] AI workout plan generation
- [x] AI meal plan generation
- [x] Food image analysis
- [x] Multi-domain support
- [ ] In-app purchase validation
- [ ] Push notifications
- [ ] Advanced analytics
- [ ] Multi-language support

---

## 📖 Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Postman Collection:** Available in repository

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 📧 Contact

**Support:** support@nexvoltsolutions.com  
**Website:** https://lookslabai.com

---

<p align="center">Built with ❤️ by Looks Lab Team</p>
