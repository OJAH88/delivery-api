from fastapi import FastAPI, Request, Depends, APIRouter
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

app = FastAPI(title="Delivery App API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Health Check to stop 404 logs
@app.get("/")
def health_check():
    return {"status": "online"}

# Math Engine
@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    payload = await request.json()
    items = payload.get("items", [])
    raw_total = sum((i.get('base_sticker_price', 0) * i.get('qty', 1)) for i in items)
    return {"raw_total": raw_total, "final_cash_total": round(raw_total / 5.0) * 5}

# Admin Router
admin = APIRouter(prefix="/api/admin")
@admin.get("/products")
def get_products(db: Session = Depends(get_db)):
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM products WHERE is_visible = TRUE")).fetchall()]

app.include_router(admin)
