# FinSight

FinSight is a full-stack financial analysis platform with AI-powered document extraction, entity onboarding, underwriting workflows, and explainability modules.

## Project Structure

- `backend/` - FastAPI application and domain modules
- `frontend/` - React (Vite) web application
- `mock_data/` - Sample Tata Powers data files
- `scripts/` - Utility and validation scripts
- `docker-compose.yml` - Local development orchestration

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Docker Desktop (optional, for containerized run)

## Quick Start (Local, Without Docker)

### 1) Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`

### 2) Frontend

Open a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## Run with Docker (Development)

From repository root:

```powershell
docker compose up --build
```

## Notes

- This repository tracks development assets only.
- Production deployment files are intentionally excluded from version control.
- Virtual environments (`.venv/`) are ignored.
- PPT Link for presentation : https://www.canva.com/design/DAHDun_5nIU/hDZ2JCBolDnj6tvI8q4KTQ/edit?utm_content=DAHDun_5nIU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton

## Useful Endpoints

- API docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## License

For hackathon/internal use unless otherwise specified.
