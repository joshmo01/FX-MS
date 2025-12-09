import React, { useState, useMemo, useCallback } from 'react';

/**
 * FX Smart Routing - Interactive Route Network Explorer
 * 
 * Visual network graph showing all possible conversion paths between:
 * - Fiat currencies (USD, EUR, INR, etc.)
 * - CBDCs (e-INR, e-CNY, e-HKD, etc.)
 * - Stablecoins (USDC, USDT, EURC, etc.)
 * 
 * Author: Fintaar.ai
 */

const RouteNetworkExplorer = () => {
  // State
  const [selectedConversion, setSelectedConversion] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [showLegend, setShowLegend] = useState(true);
  const [filterRail, setFilterRail] = useState('ALL');
  const [amount, setAmount] = useState(100000);
  const [showCosts, setShowCosts] = useState(true);
  const [animatingRoute, setAnimatingRoute] = useState(null);

  // ============================================
  // CURRENCY DEFINITIONS
  // ============================================
  const currencies = {
    FIAT: {
      USD: { name: 'US Dollar', symbol: '$', region: 'Americas', x: 100, y: 150 },
      EUR: { name: 'Euro', symbol: '€', region: 'Europe', x: 100, y: 250 },
      GBP: { name: 'British Pound', symbol: '£', region: 'Europe', x: 100, y: 350 },
      INR: { name: 'Indian Rupee', symbol: '₹', region: 'Asia', x: 200, y: 450 },
      SGD: { name: 'Singapore Dollar', symbol: 'S$', region: 'Asia', x: 200, y: 550 },
      AED: { name: 'UAE Dirham', symbol: 'د.إ', region: 'MENA', x: 100, y: 450 },
      CNY: { name: 'Chinese Yuan', symbol: '¥', region: 'Asia', x: 200, y: 150 },
      HKD: { name: 'Hong Kong Dollar', symbol: 'HK$', region: 'Asia', x: 200, y: 250 },
      THB: { name: 'Thai Baht', symbol: '฿', region: 'Asia', x: 200, y: 350 },
    },
    CBDC: {
      'e-INR': { name: 'Digital Rupee', issuer: 'RBI', status: 'Pilot', fiat: 'INR', x: 400, y: 450 },
      'e-CNY': { name: 'Digital Yuan', issuer: 'PBoC', status: 'Pilot', fiat: 'CNY', mbridge: true, x: 400, y: 150 },
      'e-HKD': { name: 'Digital HKD', issuer: 'HKMA', status: 'Pilot', fiat: 'HKD', mbridge: true, x: 400, y: 250 },
      'e-THB': { name: 'Digital Baht', issuer: 'BoT', status: 'Pilot', fiat: 'THB', mbridge: true, x: 400, y: 350 },
      'e-AED': { name: 'Digital Dirham', issuer: 'CBUAE', status: 'Pilot', fiat: 'AED', mbridge: true, x: 400, y: 550 },
      'e-SGD': { name: 'Digital SGD', issuer: 'MAS', status: 'Experimental', fiat: 'SGD', x: 500, y: 500 },
    },
    STABLECOIN: {
      USDC: { name: 'USD Coin', issuer: 'Circle', peg: 'USD', regulated: true, x: 600, y: 150 },
      USDT: { name: 'Tether', issuer: 'Tether', peg: 'USD', regulated: false, x: 600, y: 250 },
      EURC: { name: 'Euro Coin', issuer: 'Circle', peg: 'EUR', regulated: true, x: 600, y: 350 },
      PYUSD: { name: 'PayPal USD', issuer: 'Paxos', peg: 'USD', regulated: true, x: 600, y: 450 },
      XSGD: { name: 'StraitsX SGD', issuer: 'StraitsX', peg: 'SGD', regulated: true, x: 600, y: 550 },
    }
  };

  // ============================================
  // CONVERSION MATRIX - All 9 Types
  // ============================================
  const conversionMatrix = useMemo(() => ({
    // 1. FIAT → FIAT
    'FIAT→FIAT': {
      type: 'FIAT_DIRECT',
      icon: '💱',
      routes: [
        { id: 'F2F-SWIFT', name: 'SWIFT Transfer', legs: 1, fee: 25, time: '1-3 days', regulated: true },
        { id: 'F2F-LOCAL', name: 'Local Rails', legs: 1, fee: 15, time: '4 hours', regulated: true },
        { id: 'F2F-CROSS', name: 'USD Triangulation', legs: 2, fee: 30, time: '4-8 hours', regulated: true },
      ]
    },
    // 2. FIAT → CBDC
    'FIAT→CBDC': {
      type: 'FIAT_TO_CBDC',
      icon: '🏛️',
      routes: [
        { id: 'F2C-DIRECT', name: 'Direct Mint', legs: 1, fee: 0, time: '5 sec', regulated: true, best: true },
        { id: 'F2C-FXMINT', name: 'FX + Mint', legs: 2, fee: 20, time: '4 hours', regulated: true },
        { id: 'F2C-MBRIDGE', name: 'mBridge Route', legs: 3, fee: 13, time: '30 sec', regulated: true, highlight: true },
      ]
    },
    // 3. CBDC → FIAT
    'CBDC→FIAT': {
      type: 'CBDC_TO_FIAT',
      icon: '💵',
      routes: [
        { id: 'C2F-REDEEM', name: 'Direct Redeem', legs: 1, fee: 0, time: '5 sec', regulated: true, best: true },
        { id: 'C2F-REDEEMFX', name: 'Redeem + FX', legs: 2, fee: 20, time: '4 hours', regulated: true },
      ]
    },
    // 4. CBDC → CBDC
    'CBDC→CBDC': {
      type: 'CBDC_CROSSBORDER',
      icon: '🌐',
      routes: [
        { id: 'C2C-MBRIDGE', name: 'mBridge PvP', legs: 1, fee: 13, time: '15 sec', regulated: true, best: true, highlight: true },
        { id: 'C2C-NEXUS', name: 'Project Nexus', legs: 1, fee: 35, time: '60 sec', regulated: true },
        { id: 'C2C-FIAT', name: 'Fiat Bridge', legs: 4, fee: 40, time: '8 hours', regulated: true },
      ]
    },
    // 5. FIAT → STABLECOIN
    'FIAT→STABLECOIN': {
      type: 'FIAT_TO_STABLE',
      icon: '🪙',
      routes: [
        { id: 'F2S-CIRCLE', name: 'Circle On-Ramp', legs: 1, fee: 0, time: '1 hour', regulated: true, best: true },
        { id: 'F2S-CEX', name: 'CEX On-Ramp', legs: 1, fee: 25, time: '2 hours', regulated: true },
        { id: 'F2S-FXONRAMP', name: 'FX + On-Ramp', legs: 2, fee: 50, time: '5 hours', regulated: true },
      ]
    },
    // 6. STABLECOIN → FIAT
    'STABLECOIN→FIAT': {
      type: 'STABLE_TO_FIAT',
      icon: '💰',
      routes: [
        { id: 'S2F-CIRCLE', name: 'Circle Off-Ramp', legs: 1, fee: 0, time: '1 hour', regulated: true, best: true },
        { id: 'S2F-CEX', name: 'CEX Off-Ramp', legs: 1, fee: 25, time: '2 hours', regulated: true },
        { id: 'S2F-OFFRAMPFX', name: 'Off-Ramp + FX', legs: 2, fee: 50, time: '5 hours', regulated: true },
      ]
    },
    // 7. STABLECOIN → STABLECOIN
    'STABLECOIN→STABLECOIN': {
      type: 'STABLE_SWAP',
      icon: '🔄',
      routes: [
        { id: 'S2S-CURVE', name: 'Curve DEX', legs: 1, fee: 4, time: '1 min', regulated: false, best: true },
        { id: 'S2S-UNISWAP', name: 'Uniswap V3', legs: 1, fee: 30, time: '1 min', regulated: false },
        { id: 'S2S-CEX', name: 'CEX Trade', legs: 1, fee: 20, time: '10 sec', regulated: true },
      ]
    },
    // 8. CBDC → STABLECOIN ⭐ NEW
    'CBDC→STABLECOIN': {
      type: 'CBDC_TO_STABLE',
      icon: '🔗',
      routes: [
        { id: 'C2S-FIAT', name: 'Fiat Intermediary', legs: 2, fee: 25, time: '5 hours', regulated: true, path: ['CBDC', 'FIAT', 'STABLECOIN'] },
        { id: 'C2S-CEX', name: 'CEX Bridge', legs: 2, fee: 50, time: '2 hours', regulated: true, path: ['CBDC', 'FIAT', 'STABLECOIN'] },
        { id: 'C2S-MBRIDGE', name: 'mBridge + Off-Ramp', legs: 3, fee: 38, time: '1 hour', regulated: true, highlight: true, path: ['CBDC', 'CBDC', 'FIAT', 'STABLECOIN'] },
        { id: 'C2S-DEX', name: 'DEX Liquidity', legs: 2, fee: 35, time: '10 min', regulated: false, experimental: true, path: ['CBDC', 'FIAT', 'STABLECOIN'] },
        { id: 'C2S-ATOMIC', name: 'Atomic Swap', legs: 1, fee: 5, time: '5 min', regulated: false, experimental: true, best: true, path: ['CBDC', 'STABLECOIN'] },
      ]
    },
    // 9. STABLECOIN → CBDC ⭐ NEW
    'STABLECOIN→CBDC': {
      type: 'STABLE_TO_CBDC',
      icon: '🏦',
      routes: [
        { id: 'S2C-FIAT', name: 'Fiat Intermediary', legs: 2, fee: 25, time: '5 hours', regulated: true, path: ['STABLECOIN', 'FIAT', 'CBDC'] },
        { id: 'S2C-CEX', name: 'CEX Bridge', legs: 2, fee: 50, time: '2 hours', regulated: true, path: ['STABLECOIN', 'FIAT', 'CBDC'] },
        { id: 'S2C-OTC', name: 'OTC Trade', legs: 1, fee: 15, time: 'T+1', regulated: true, path: ['STABLECOIN', 'CBDC'] },
        { id: 'S2C-LIQUIDITY', name: 'Liquidity Pool', legs: 2, fee: 40, time: '15 min', regulated: false, experimental: true, path: ['STABLECOIN', 'FIAT', 'CBDC'] },
        { id: 'S2C-ATOMIC', name: 'Atomic Swap', legs: 1, fee: 5, time: '5 min', regulated: false, experimental: true, best: true, path: ['STABLECOIN', 'CBDC'] },
      ]
    }
  }), []);

  // ============================================
  // STYLING
  // ============================================
  const typeStyles = {
    FIAT: { bg: 'bg-blue-500', border: 'border-blue-600', text: 'text-white', gradient: 'from-blue-400 to-blue-600' },
    CBDC: { bg: 'bg-emerald-500', border: 'border-emerald-600', text: 'text-white', gradient: 'from-emerald-400 to-emerald-600' },
    STABLECOIN: { bg: 'bg-purple-500', border: 'border-purple-600', text: 'text-white', gradient: 'from-purple-400 to-purple-600' }
  };

  // ============================================
  // CONVERSION MATRIX GRID
  // ============================================
  const ConversionMatrixGrid = () => {
    const types = ['FIAT', 'CBDC', 'STABLECOIN'];
    
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <span>📊</span> Complete Conversion Matrix
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="p-2 text-left text-sm text-gray-500">FROM ↓ / TO →</th>
                {types.map(t => (
                  <th key={t} className={`p-2 text-center text-sm font-bold ${typeStyles[t].bg} ${typeStyles[t].text} rounded-t`}>
                    {t}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {types.map(fromType => (
                <tr key={fromType}>
                  <td className={`p-2 font-bold text-sm ${typeStyles[fromType].bg} ${typeStyles[fromType].text} rounded-l`}>
                    {fromType}
                  </td>
                  {types.map(toType => {
                    const key = `${fromType}→${toType}`;
                    const conversion = conversionMatrix[key];
                    const isSelected = selectedConversion === key;
                    
                    return (
                      <td 
                        key={toType} 
                        className={`p-2 text-center cursor-pointer transition-all duration-200
                          ${isSelected ? 'bg-amber-100 ring-2 ring-amber-400' : 'bg-gray-50 hover:bg-gray-100'}
                          ${fromType === toType ? 'bg-gray-200' : ''}
                        `}
                        onClick={() => setSelectedConversion(isSelected ? null : key)}
                      >
                        {conversion && (
                          <div className="flex flex-col items-center">
                            <span className="text-2xl mb-1">{conversion.icon}</span>
                            <span className="text-xs font-medium">{conversion.routes.length} routes</span>
                            <span className="text-xs text-gray-500">
                              {Math.min(...conversion.routes.map(r => r.fee))} bps min
                            </span>
                          </div>
                        )}
                        {!conversion && fromType !== toType && (
                          <span className="text-gray-400 text-xs">N/A</span>
                        )}
                        {fromType === toType && (
                          <span className="text-gray-400 text-xs">Same</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // ============================================
  // ROUTE DETAILS PANEL
  // ============================================
  const RouteDetailsPanel = () => {
    if (!selectedConversion) {
      return (
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-8 text-center">
          <div className="text-6xl mb-4">🗺️</div>
          <h3 className="text-xl font-bold text-gray-700 mb-2">Select a Conversion</h3>
          <p className="text-gray-500">Click any cell in the matrix above to see available routes</p>
        </div>
      );
    }

    const conversion = conversionMatrix[selectedConversion];
    const [fromType, toType] = selectedConversion.split('→');

    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{conversion.icon}</span>
            <div>
              <h3 className="text-xl font-bold">{selectedConversion}</h3>
              <p className="text-sm text-gray-500">{conversion.type.replace(/_/g, ' ')}</p>
            </div>
          </div>
          <button 
            onClick={() => setSelectedConversion(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Route Flow Visualization */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-2">
            <div className={`px-4 py-2 rounded-lg bg-gradient-to-r ${typeStyles[fromType].gradient} text-white font-medium`}>
              {fromType}
            </div>
            <div className="flex items-center">
              <div className="w-12 h-0.5 bg-gray-400"></div>
              <div className="w-0 h-0 border-t-8 border-t-transparent border-b-8 border-b-transparent border-l-8 border-l-gray-400"></div>
            </div>
            <div className={`px-4 py-2 rounded-lg bg-gradient-to-r ${typeStyles[toType].gradient} text-white font-medium`}>
              {toType}
            </div>
          </div>
        </div>

        {/* Routes List */}
        <div className="space-y-3">
          {conversion.routes.map((route, idx) => (
            <div 
              key={route.id}
              className={`p-4 rounded-lg border-2 transition-all duration-200 cursor-pointer
                ${route.best ? 'border-green-400 bg-green-50' : 
                  route.highlight ? 'border-amber-400 bg-amber-50' :
                  route.experimental ? 'border-purple-300 bg-purple-50 border-dashed' :
                  'border-gray-200 bg-white hover:border-gray-300'}
              `}
              onClick={() => setAnimatingRoute(route.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">
                    {route.best ? '⭐' : route.highlight ? '🔥' : route.experimental ? '🧪' : '➡️'}
                  </div>
                  <div>
                    <div className="font-semibold flex items-center gap-2">
                      {route.name}
                      {route.best && <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">BEST</span>}
                      {route.highlight && <span className="text-xs bg-amber-500 text-white px-2 py-0.5 rounded-full">RECOMMENDED</span>}
                      {route.experimental && <span className="text-xs bg-purple-500 text-white px-2 py-0.5 rounded-full">EXPERIMENTAL</span>}
                    </div>
                    <div className="text-sm text-gray-500">
                      {route.legs} leg{route.legs > 1 ? 's' : ''} • {route.regulated ? '✅ Regulated' : '⚠️ Unregulated'}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-lg">{route.fee} bps</div>
                  <div className="text-sm text-gray-500">⏱️ {route.time}</div>
                </div>
              </div>

              {/* Route Path */}
              {route.path && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center gap-1 text-xs">
                    {route.path.map((step, i) => (
                      <React.Fragment key={i}>
                        <span className={`px-2 py-1 rounded ${
                          step === 'FIAT' ? 'bg-blue-100 text-blue-700' :
                          step === 'CBDC' ? 'bg-emerald-100 text-emerald-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>
                          {step}
                        </span>
                        {i < route.path.length - 1 && <span className="text-gray-400">→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Cost Calculator */}
              {showCosts && (
                <div className="mt-3 pt-3 border-t border-gray-200 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>Amount: ${amount.toLocaleString()}</span>
                    <span>Fee: ${((amount * route.fee) / 10000).toFixed(2)}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ============================================
  // CBDC ↔ STABLECOIN BRIDGE DETAILS
  // ============================================
  const BridgeDetails = () => (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 mb-6">
      <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
        <span>🌉</span> CBDC ↔ Stablecoin Bridge Routes
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CBDC to Stablecoin */}
        <div className="bg-white rounded-lg p-4 shadow">
          <h4 className="font-bold text-emerald-700 mb-2">CBDC → Stablecoin</h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span><strong>Fiat Bridge:</strong> CBDC → Redeem → Fiat → On-Ramp → Stablecoin</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
              <span><strong>mBridge Hybrid:</strong> CBDC → mBridge → CBDC₂ → Fiat → Stablecoin</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
              <span><strong>Atomic Swap:</strong> CBDC ⟷ Stablecoin (experimental)</span>
            </div>
          </div>
        </div>

        {/* Stablecoin to CBDC */}
        <div className="bg-white rounded-lg p-4 shadow">
          <h4 className="font-bold text-purple-700 mb-2">Stablecoin → CBDC</h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span><strong>Fiat Bridge:</strong> Stablecoin → Off-Ramp → Fiat → Mint → CBDC</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <span><strong>OTC Route:</strong> Stablecoin → OTC Desk → CBDC</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
              <span><strong>Atomic Swap:</strong> Stablecoin ⟷ CBDC (experimental)</span>
            </div>
          </div>
        </div>
      </div>

      {/* mBridge Integration Note */}
      <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm">
        <strong>🔥 mBridge Advantage:</strong> For mBridge-enabled CBDCs (e-CNY, e-HKD, e-THB, e-AED), 
        hybrid routes can achieve atomic PvP settlement with reduced counterparty risk and 
        15-second finality vs. 24+ hours for traditional rails.
      </div>
    </div>
  );

  // ============================================
  // LEGEND
  // ============================================
  const Legend = () => (
    <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
      <div className="flex flex-wrap gap-4 items-center justify-center">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-blue-400 to-blue-600"></div>
          <span className="text-sm">FIAT</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-emerald-400 to-emerald-600"></div>
          <span className="text-sm">CBDC</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gradient-to-r from-purple-400 to-purple-600"></div>
          <span className="text-sm">STABLECOIN</span>
        </div>
        <div className="border-l border-gray-300 h-6 mx-2"></div>
        <div className="flex items-center gap-1">
          <span>⭐</span><span className="text-sm">Best Rate</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🔥</span><span className="text-sm">Recommended</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🧪</span><span className="text-sm">Experimental</span>
        </div>
      </div>
    </div>
  );

  // ============================================
  // QUICK STATS
  // ============================================
  const QuickStats = () => {
    const totalRoutes = Object.values(conversionMatrix).reduce((sum, c) => sum + c.routes.length, 0);
    const regulatedRoutes = Object.values(conversionMatrix).reduce(
      (sum, c) => sum + c.routes.filter(r => r.regulated).length, 0
    );
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-blue-600">9</div>
          <div className="text-sm text-blue-700">Conversion Types</div>
        </div>
        <div className="bg-emerald-50 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-emerald-600">{totalRoutes}</div>
          <div className="text-sm text-emerald-700">Total Routes</div>
        </div>
        <div className="bg-purple-50 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-purple-600">{regulatedRoutes}</div>
          <div className="text-sm text-purple-700">Regulated Routes</div>
        </div>
        <div className="bg-amber-50 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-amber-600">4</div>
          <div className="text-sm text-amber-700">mBridge CBDCs</div>
        </div>
      </div>
    );
  };

  // ============================================
  // AMOUNT INPUT
  // ============================================
  const AmountInput = () => (
    <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
      <div className="flex items-center gap-4">
        <label className="font-medium text-gray-700">Transaction Amount:</label>
        <div className="relative flex-1 max-w-xs">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showCosts}
            onChange={(e) => setShowCosts(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm text-gray-600">Show costs</span>
        </label>
      </div>
    </div>
  );

  // ============================================
  // MAIN RENDER
  // ============================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🗺️ FX Route Network Explorer
          </h1>
          <p className="text-gray-600">
            Interactive visualization of all FIAT ↔ CBDC ↔ Stablecoin conversion routes
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Powered by Fintaar.ai Smart Routing Engine
          </p>
        </div>

        {/* Quick Stats */}
        <QuickStats />

        {/* Legend */}
        <Legend />

        {/* Amount Input */}
        <AmountInput />

        {/* CBDC-Stablecoin Bridge Details */}
        <BridgeDetails />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversion Matrix */}
          <ConversionMatrixGrid />

          {/* Route Details */}
          <RouteDetailsPanel />
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>FX Smart Routing Engine v2.0 • Multi-Rail Support (FIAT + CBDC + Stablecoin)</p>
          <p className="mt-1">© 2024 Fintaar.ai</p>
        </div>
      </div>
    </div>
  );
};

export default RouteNetworkExplorer;
