from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import location_routes, pahani_request_routes,auth
from app.db import init_db
from app.routes import admin_routes
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
app.include_router(location_routes.router, prefix="/api/location")
app.include_router(pahani_request_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(auth.router,prefix="/api")