'use client';
import { useEffect, useState } from 'react';
import BundleBuilder from '../components/BundleBuilder';
import CartDrawer from '../components/CartDrawer';

// --- YOUR PRICING CONFIGURATIONS ---
const CONFIGS = {
  tier1: [
    { id: 't1_8', label: '1/8 oz', slots: 1, price: 45.0 },
    { id: 't1_4', label: '1/4 oz', slots: 2, price: 80.0 },
    { id: 't1_2', label: '1/2 oz', slots: 4, price: 150.0 },
    { id: 't1_1', label: '1 oz', slots: 8, price: 280.0 }
  ],
  tier2: [
    { id: 't2_8', label: '1/8 oz', slots: 1, price: 35.0 },
    { id: 't2_4', label: '1/4 oz', slots: 2, price: 60.0 },
    { id: 't2_2', label: '1/2 oz', slots: 4, price: 110.0 },
    { id: 't2_1', label: '1 oz', slots: 8, price: 200.0 }
  ],
  tier3: [
    { id: 't3_8', label: '1/8 oz', slots: 1, price: 25.0 },
    { id: 't3_4', label: '1/4 oz', slots: 2, price: 45.0 },
    { id: 't3_2', label: '1/2 oz', slots: 4, price: 80.0 },
    { id: 't3_1', label: '1 oz', slots: 8, price: 150.0 }
  ],
  bho: [
    { id: 'bho_1', label: '1g', slots: 1, price: 30.0 },
    // If 3.5g is one bucket of a single strain, slot = 1. If it's mix & match 3.5 units, that gets messy. 
    // Assuming they pick 1 strain for the 3.5g jar here:
    { id: 'bho_35', label: '3.5g Bucket', slots: 1, price: 90.0 }, 
    { id: 'bho_7', label: '7g', slots: 7, price: 170.0 }, // Mix & match 7x 1g jars
    { id: 'bho_14', label: '14g', slots: 14, price: 300.0 },
    { id: 'bho_28', label: '28g', slots: 28, price: 550.0 }
  ]
};

export default function Home() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch('https://delivery-api-jdto.onrender.com/api/admin/products')
      .then(res => res.json())
      .then(data => setProducts(Array.isArray(data) ? data : []))
      .catch(err => console.error(err));
  }, []);

  // Filter your database products into their buckets based on tier_name or category
  const tier1Strains = products.filter(p => p.tier_name === 'Tier 1');
  const tier2Strains = products.filter(p => p.tier_name === 'Tier 2');
  const tier3Strains = products.filter(p => p.tier_name === 'Tier 3');
  const bhoProducts = products.filter(p => p.category_id === 2); // Assuming 2 is BHO category

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <header className="mb-10 text-emerald-400 font-black text-2xl tracking-widest">BRANCH</header>
      
      <div className="flex flex-row gap-8 items-start">
        <main className="flex-1 space-y-8">
          
          {/* Render a builder for each category */}
          {tier1Strains.length > 0 && (
             <BundleBuilder title="Tier 1 Flower" sizes={CONFIGS.tier1} availableProducts={tier1Strains} baseUnitName="1/8th" />
          )}
          
          {tier2Strains.length > 0 && (
             <BundleBuilder title="Tier 2 Flower" sizes={CONFIGS.tier2} availableProducts={tier2Strains} baseUnitName="1/8th" />
          )}

          {tier3Strains.length > 0 && (
             <BundleBuilder title="Tier 3 Flower" sizes={CONFIGS.tier3} availableProducts={tier3Strains} baseUnitName="1/8th" />
          )}

          {bhoProducts.length > 0 && (
             <BundleBuilder title="BHO Concentrates" sizes={CONFIGS.bho} availableProducts={bhoProducts} baseUnitName="1g Jar" />
          )}

        </main>
        
        <aside className="w-80 shrink-0 sticky top-8">
          <CartDrawer />
        </aside>
      </div>
    </div>
  );
}
