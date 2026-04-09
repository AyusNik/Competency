from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import competencies, competency_units, trainings, courses, plr, content_mappings, assessments, ilearn, auth_manager

app = FastAPI(title="CAT System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201", "http://localhost:4202"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competencies.router)
app.include_router(competency_units.router)
app.include_router(trainings.router)
app.include_router(courses.router)
app.include_router(plr.router)
app.include_router(content_mappings.router)
app.include_router(assessments.router)
app.include_router(ilearn.router)
app.include_router(auth_manager.router)


@app.get("/")
async def root():
    return {"message": "CAT System API"}
