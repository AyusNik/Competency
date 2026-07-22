from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, dashboard, chat, manager_chat, progress, certifications

app = FastAPI(title="MyPCP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4202"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(manager_chat.router)
app.include_router(progress.router)
app.include_router(certifications.router)


@app.get("/")
async def root():
    return {"message": "MyPCP API"}
