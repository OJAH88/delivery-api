from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # Simple hardcoded test to verify communication
        raw_total = 0.0
        for item in items:
            raw_total += float(item.get('base_sticker_price', 0)) * int(item.get('qty', 1))
            
        return {
            "raw_total": raw_total,
            "discount_applied": 0.0,
            "final_cash_total": round(raw_total / 5.0) * 5
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
