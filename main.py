from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        try:
            query = """
                SELECT p.product_id, p.name, COALESCE(p.base_sticker_price, 0.0) as base_sticker_price, p.category_id, t.name as tier_name 
                FROM products p
                LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
            """
            result = db.execute(text(query)).fetchall()
        except:
            query = "SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price, category_id FROM products"
            result = db.execute(text(query)).fetchall()
            
        return [dict(row._mapping) for row in result]
    except Exception as e:
        return []
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    db = SessionLocal()
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # 1. Fetch Dynamic Bulk Rules from Supabase
        # NOTE: Update 'bulk_pricing_rules' and the column names to match your exact Supabase table!
        # It must order by quantity descending (e.g., 8, 4, 2) to calculate the largest blocks first.
        try:
            rules_query = "SELECT tier_name, threshold_qty, discount_amount FROM bulk_pricing_rules ORDER BY threshold_qty DESC"
            bulk_rules = db.execute(text(rules_query)).fetchall()
        except:
            bulk_rules = [] # Failsafe if the table name is different
            
        query = "SELECT product_id, category_id, name FROM products"
        db_products = {str(row.product_id): row for row in db.execute(text(query)).fetchall()}
        
        raw_total = 0.0
        tier_counts = {}
        
        # 2. Pool all items by their Tier Name
        for item in items:
            pid = str(item.get('product_id'))
            qty = int(item.get('qty') or 1)
            price = float(item.get('base_sticker_price') or 0)
            
            raw_total += (price * qty)
            
            # Identify the tier safely
            frontend_tier = str(item.get('tier_name') or 'unknown')
            tier_counts[frontend_tier] = tier_counts.get(frontend_tier, 0) + qty

        discount_applied = 0.0
        
        # 3. Dynamic Step-Down Calculation
        # This breaks the total quantity into the largest possible chunks defined in your DB
        for tier, total_qty in tier_counts.items():
            remaining_qty = total_qty
            
            # Get only the rules that apply to this specific tier
            applicable_rules = [r for r in bulk_rules if r.tier_name == tier]
            
            for rule in applicable_rules:
                # How many full blocks of this threshold fit? (e.g., how many halves are in 5 eighths?)
                num_blocks = remaining_qty // rule.threshold_qty
                
                # Apply the specific discount from the database for those blocks
                discount_applied += (num_blocks * rule.discount_amount)
                
                # Update the remainder to carry down to the next smaller threshold
                remaining_qty = remaining_qty % rule.threshold_qty
                
        final_total = max(0.0, raw_total - discount_applied)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(discount_applied),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e), "raw_total": 0.0, "discount_applied": 0.0, "final_cash_total": 0.0}
    finally:
        db.close()
