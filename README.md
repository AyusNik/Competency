# CAT System

Competency Assessment Tool — FastAPI + Angular + MongoDB

## Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running on `localhost:27017`

---

## Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Seed sample data (optional)
python seed.py

# Start server
uvicorn app.main:app --reload
```

API available at: http://localhost:8001  
Swagger docs: http://localhost:8001/docs

---

## Frontend Setup

```bash
cd frontend
npm install
ng serve
```

App available at: http://localhost:4200

---

## API Endpoints

| Resource | Endpoint |
|---|---|
| Content Mappings | `/content-mappings` |
| Competencies | `/competencies` |
| Competency Units | `/competency-units` |
| Trainings | `/trainings` |
| Courses | `/courses` |
| PLR | `/plr` |

All endpoints support `GET`, `POST`, `PUT/{id}`, `DELETE/{id}`.  
Content Mappings `GET` supports `?search=` query param.
