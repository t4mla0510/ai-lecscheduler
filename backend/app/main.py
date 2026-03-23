import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.db import cache, db

from app.api.routes import (
    course_router,
    lecturer_router,
    room_router,
    timeslot_router,
    schedule_router
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    cache.init(host=REDIS_HOST, port=REDIS_PORT)
    yield
    db.close()

app = FastAPI(title="GA Scheduler API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Include all routers
app.include_router(schedule_router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(course_router, prefix="/api/courses", tags=["Courses"])
app.include_router(lecturer_router, prefix="/api/lecturers", tags=["Lecturers"])
app.include_router(room_router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(timeslot_router, prefix="/api/timeslots", tags=["Timeslots"])

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head>
            <title>GA Scheduler</title>
            <style>
                body { font-family: Arial; padding: 32px; background: #fafafa; }
                .box { 
                    max-width: 600px; margin: auto; padding: 24px; 
                    background: white; border-radius: 16px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }
                h1 { color: #4B7BEC; }
                p { color: #555; font-size: 16px; }
                a { color: #20bf6b; font-weight: bold; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>GA Scheduler Backend</h1>
                <p>Your backend is running successfully </p>

                <p>Explore API docs:</p>
                <ul>
                    <li><a href="/docs">Swagger UI</a></li>
                    <li><a href="/redoc">ReDoc UI</a></li>
                </ul>

                <p>Current status: <b style="color:green;">ONLINE</b></p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "GA scheduler running"}
