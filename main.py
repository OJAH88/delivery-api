from fastapi import FastAPI, Request, Depends, APIRouter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

app = FastAPI(title="Delivery App API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        raw_total = sum((float(i.get('base_sticker_price') or 0) * int(i.get('qty') or 0)) for i in items)
        return {"raw_total": float(raw_total), "final_cash_total": round(raw_total / 5.0) * 5}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/admin/products")
def get_products(db: Session = Depends(get_db)):
    try:
        query = "SELECT product_id, name, base_sticker_price FROM products"
        result = db.execute(text(query)).fetchall()
        # FIX: Use _mapping to correctly convert SQLAlchemy rows to dicts
        products = [dict(row._mapping) for row in result]
        return products
    except Exception as e:
        print(f"DEBUG ERROR: {traceback.format_exc()}")
        return []

app.include_router(APIRouter(prefix="/api/admin"))
