# Looks Lab Backend API

> **AI-Powered Personal Wellness Platform**
> 
> A comprehensive FastAPI-based backend system providing personalized wellness insights across multiple domains including skincare, haircare, diet, fitness, and more.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Database Setup](#database-setup)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Looks Lab is an AI-powered wellness platform that provides personalized insights and recommendations across 8 specialized domains. The backend handles user authentication, onboarding workflows, AI-powered analysis, subscription management, and real-time insights delivery.

### Key Capabilities

- **Anonymous Onboarding**: Users can complete onboarding before signing up
- **Multi-Domain Support**: 8 specialized wellness domains with tailored AI processing
- **OAuth Authentication**: Google and Apple Sign-In integration
- **AI-Powered Analysis**: Google Gemini integration for intelligent insights
- **Subscription Management**: Flexible subscription plans with Stripe integration
- **Image Processing**: S3-based image storage with AI analysis
- **Real-time Insights**: Personalized wellness recommendations

---

## ✨ Features

### Authentication & User Management
- 🔐 OAuth 2.0 (Google & Apple Sign-In)
- 🔑 JWT-based authentication with refresh tokens
- 👤 Comprehensive user profile management
- 🔒 Secure session handling

### Onboarding System
- 📝 Anonymous session creation (no auth required)
- 🎯 Multi-step progressive disclosure
- 🔗 Session linking post-authentication
- 📊 Progress tracking across 5 onboarding stages

### Domain Support
- 💆 **Skincare**: Skin analysis and product recommendations
- 💇 **Haircare**: Hair health insights and care routines
- 👔 **Fashion**: Style recommendations and wardrobe planning
- 🏋️ **Workout**: Personalized fitness plans
- 🍎 **Diet**: Nutrition analysis and meal planning
- 📏 **Height**: Growth tracking and optimization
- 🧘 **Quit Porn**: Behavioral tracking and support
- 💆 **Facial**: Facial feature analysis and care

### AI & Analytics
- 🤖 Google Gemini 3 Flash Preview integration
- 📸 Image analysis and processing
- 📈 Progress tracking and insights
- 🎯 Personalized recommendations

### Subscription & Payments
- 💳 Stripe integration (ready for production)
- 📅 Flexible subscription plans (monthly/yearly)
- 🎁 Trial period support
- 💰 Subscription status management

---

## 🛠 Tech Stack

### Core Framework
- **FastAPI** - Modern, high-performance web framework
- **Python 3.12+** - Latest Python features and optimizations
- **Pydantic** - Data validation using Python type annotations
- **SQLAlchemy 2.0** - Async ORM for database operations

### Database
- **PostgreSQL 16+** - Primary relational database
- **Alembic** - Database migration management
- **asyncpg** - Async PostgreSQL driver

### Authentication & Security
- **OAuth 2.0** - Google & Apple authentication
- **JWT** - Secure token-based authentication
- **Python-JOSE** - JWT token handling
- **Passlib** - Password hashing (Bcrypt)

### AI & Cloud Services
- **Google Gemini API** - AI-powered insights and analysis
- **AWS S3** - Image storage and management
- **Boto3** - AWS SDK for Python

### API & Networking
- **HTTPX** - Async HTTP client
- **Slowapi** - Rate limiting middleware
- **Python-Multipart** - File upload handling

### Development Tools
- **Uvicorn** - ASGI server
- **Python-dotenv** - Environment management
- **Ruff** - Fast Python linter
- **Black** - Code formatting

---

## 🏗 Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
│         (Mobile App / Web App / Postman)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routing    │  │  Middleware  │  │   Security   │     │
│  │   Layer      │  │   Layer      │  │   Layer      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │Onboarding│  │  Domain  │  │  Image   │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          SQLAlchemy Models & ORM                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │PostgreSQL │  │   AWS S3  │  │  Gemini   │  │ OAuth   │ │
│  │ Database  │  │  Storage  │  │    API    │  │Providers│ │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 16+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Git** - [Download Git](https://git-scm.com/downloads/)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/yourusername/looks-lab-backend.git
   cd looks-lab-backend
```

2. **Create virtual environment**
```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

### Environment Setup

1. **Create `.env` file in the project root**
```bash
   cp .env.example .env
```

2. **Configure environment variables**
```env
   # Database
   DATABASE_URI=postgresql+asyncpg://looks_lab:your_password@localhost:5432/looks_lab
   
   # Security
   JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
   JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-this-in-production
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=30
   
   # OAuth
   GOOGLE_CLIENT_ID=your-google-client-id
   APPLE_CLIENT_ID=your-apple-client-id
   
   # AI Services
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_MODEL=gemini-3-flash-preview
   
   # AWS S3 (Optional)
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=looks-lab-images
   
   # Application
   ENVIRONMENT=development
   DEBUG=true
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Database Setup

1. **Create PostgreSQL database**
```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database and user
   CREATE DATABASE looks_lab;
   CREATE USER looks_lab WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE looks_lab TO looks_lab;
```

2. **Run database migrations**
```bash
   # Generate migration (if needed)
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
```

3. **Verify migration**
```bash
   # Check current database version
   alembic current
   
   # View migration history
   alembic history
```

4. **Start the development server**
```bash
   uvicorn app.main:app --reload
```

5. **Access the application**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

---

## 📚 API Documentation

### Interactive Documentation

Once the server is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Postman Collection

Import the provided Postman collection for easy API testing:

1. **Files to import**:
   - `Looks_Lab_API.postman_collection.json`
   - `Looks_Lab_Environment.postman_environment.json`

2. **Anonymous Onboarding Flow** (No Authentication):
```
   1. POST   /api/v1/onboarding/sessions
   2. GET    /api/v1/onboarding/sessions/{id}/flow
   3. POST   /api/v1/onboarding/sessions/{id}/answers
   4. PATCH  /api/v1/onboarding/sessions/{id}/domain
   5. PATCH  /api/v1/onboarding/sessions/{id}/payment
```

3. **Authentication** (After Onboarding):
```
   6. POST   /api/v1/auth/google
   7. PATCH  /api/v1/onboarding/sessions/{id}/link
```

### Key Endpoints

#### Authentication
```
POST   /api/v1/auth/google              # Google Sign-In
POST   /api/v1/auth/apple               # Apple Sign-In
POST   /api/v1/auth/refresh             # Refresh access token
POST   /api/v1/auth/sign-out            # Sign out
```

#### Onboarding (Anonymous)
```
POST   /api/v1/onboarding/sessions                    # Create session
GET    /api/v1/onboarding/sessions/{id}/flow          # Get flow state
POST   /api/v1/onboarding/sessions/{id}/answers       # Submit answer
PATCH  /api/v1/onboarding/sessions/{id}/domain        # Select domain
PATCH  /api/v1/onboarding/sessions/{id}/payment       # Confirm payment
```

#### Onboarding (Authenticated)
```
PATCH  /api/v1/onboarding/sessions/{id}/link          # Link session to user
GET    /api/v1/onboarding/users/me/answers            # Get user answers
GET    /api/v1/onboarding/users/me/wellness           # Get wellness metrics
```

#### Domains
```
GET    /api/v1/domains/{domain}/questions             # Get domain questions
POST   /api/v1/domains/{domain}/answers               # Submit domain answer
GET    /api/v1/domains/{domain}/progress              # Get domain progress
GET    /api/v1/domains/progress/overview              # Get all domains progress
```

#### Images
```
POST   /api/v1/images/                                # Upload image
GET    /api/v1/images/                                # List user images
GET    /api/v1/images/{id}                            # Get image details
GET    /api/v1/images/{id}/url                        # Get presigned URL
DELETE /api/v1/images/{id}                            # Delete image
```

---

## 📁 Project Structure
```
looks-lab-backend/
│
├── alembic/                    # Database migrations
│   ├── versions/              # Migration scripts
│   └── env.py                 # Alembic configuration
│
├── app/
│   ├── api/                   # API layer
│   │   └── v1/
│   │       ├── routes/        # API endpoints
│   │       │   ├── auth.py
│   │       │   ├── onboarding.py
│   │       │   ├── domains.py
│   │       │   ├── images.py
│   │       │   ├── users.py
│   │       │   └── ...
│   │       └── api_router.py  # Main router
│   │
│   ├── core/                  # Core functionality
│   │   ├── config.py          # Settings & configuration
│   │   ├── database.py        # Database connection
│   │   ├── logging.py         # Logging setup
│   │   ├── rate_limit.py      # Rate limiting
│   │   └── security.py        # Security middleware
│   │
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── onboarding.py
│   │   ├── domain.py
│   │   ├── image.py
│   │   └── ...
│   │
│   ├── schemas/               # Pydantic schemas
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── domain.py
│   │   └── ...
│   │
│   ├── services/              # Business logic
│   │   ├── auth_service.py
│   │   ├── onboarding_service.py
│   │   ├── domain_service.py
│   │   └── ...
│   │
│   ├── utils/                 # Utility functions
│   │   ├── jwt_utils.py
│   │   ├── google_utils.py
│   │   ├── apple_utils.py
│   │   └── ...
│   │
│   └── main.py                # FastAPI application
│
├── .env                       # Environment variables
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── alembic.ini                # Alembic configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── Looks_Lab_API.postman_collection.json  # Postman collection
```

---

## 💻 Development

### Running in Development Mode
```bash
# Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with specific log level
uvicorn app.main:app --reload --log-level debug
```

### Code Quality
```bash
# Format code with Black
black app/

# Lint with Ruff
ruff check app/

# Type checking (if using mypy)
mypy app/
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URI` | PostgreSQL connection string | ✅ Yes | - |
| `JWT_SECRET` | JWT signing secret | ✅ Yes | - |
| `JWT_REFRESH_SECRET` | Refresh token secret | ✅ Yes | - |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | ✅ Yes | - |
| `APPLE_CLIENT_ID` | Apple OAuth client ID | ✅ Yes | - |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes | - |
| `GEMINI_MODEL` | Gemini model name | ❌ No | `gemini-3-flash-preview` |
| `AWS_ACCESS_KEY_ID` | AWS access key | ❌ No | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | ❌ No | - |
| `S3_BUCKET_NAME` | S3 bucket name | ❌ No | - |
| `ENVIRONMENT` | Environment mode | ❌ No | `development` |
| `DEBUG` | Debug mode | ❌ No | `true` |

---

## 🧪 Testing

### Manual Testing with Postman

1. Import the Postman collection
2. Set environment to "Looks Lab - Local"
3. Run requests in order (numbered 1-7)

### Testing Anonymous Onboarding Flow
```bash
# 1. Create anonymous session (no auth)
curl -X POST http://localhost:8000/api/v1/onboarding/sessions

# 2. Get flow state
curl -X GET "http://localhost:8000/api/v1/onboarding/sessions/{session_id}/flow?step=profile_setup&index=0"

# 3. Submit answer
curl -X POST http://localhost:8000/api/v1/onboarding/sessions/{session_id}/answers \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "answer": 25, "question_type": "numeric"}'

# 4. Select domain
curl -X PATCH "http://localhost:8000/api/v1/onboarding/sessions/{session_id}/domain?domain=skincare"

# 5. Confirm payment
curl -X PATCH http://localhost:8000/api/v1/onboarding/sessions/{session_id}/payment

# 6. Sign in (get tokens)
curl -X POST http://localhost:8000/api/v1/auth/google \
  -H "Content-Type: application/json" \
  -d '{"id_token": "mock-token", "email": "test@gmail.com", "name": "Test User"}'

# 7. Link session to user
curl -X PATCH http://localhost:8000/api/v1/onboarding/sessions/{session_id}/link \
  -H "Authorization: Bearer {access_token}"
```

---

## 🚢 Deployment

### Production Setup

1. **Update environment variables**
```env
   ENVIRONMENT=production
   DEBUG=false
   DATABASE_URI=postgresql+asyncpg://user:pass@prod-db:5432/looks_lab
```

2. **Set secure secrets**
```bash
   # Generate secure secrets
   python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Configure CORS**
```env
   ALLOWED_ORIGINS=https://your-frontend.com,https://api.your-domain.com
```

### Docker Deployment (Coming Soon)
```dockerfile
# Dockerfile example
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks
```bash
# Health check endpoint
curl http://localhost:8000/health
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write descriptive commit messages
- Add docstrings to all functions
- Update tests for new features
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Google Gemini for AI capabilities
- PostgreSQL community
- All contributors and supporters

---

## 📞 Support

For support, email nexvoltsolutions.com or join our Slack channel.

---

## 🗺 Roadmap

- [x] Anonymous onboarding flow
- [x] OAuth authentication (Google & Apple)
- [x] Multi-domain support
- [x] AI-powered insights
- [ ] Stripe payment integration
- [ ] Real-time notifications
- [ ] Mobile app API optimization
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Docker containerization

---

<p align="center">Made with ❤️ by the Looks Lab Team</p>

