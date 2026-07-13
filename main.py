from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# FORCE CORS: This is the most permissive setting possible
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # Hardened calculation logic
        raw_total = 0
        for item in items:
            # Use 0 as default if keys are missing
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 0)
            raw_total += (price * qty)
            
        final_cash_total = round(raw_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        # This will tell us exactly WHY it's 500ing
        return {"error": str(e)}

@app.get("/")
def health(): return {"status": "online"}
