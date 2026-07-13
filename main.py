from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI(title="Delivery App API")

# Allow all origins for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # Hardened calculation
        raw_total = 0.0
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 0)
            raw_total += (price * qty)
            
        final_cash_total = round(raw_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        # If this crashes, you will see the exact error in the frontend Network tab
        return {"error": str(e), "traceback": traceback.format_exc()}
