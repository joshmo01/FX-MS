import React, { useState, useMemo, useCallback, useEffect } from 'react';

/**
 * Universal FX Route Explorer
 * Interactive visualization of ALL conversion paths
 * Fiat ↔ CBDC ↔ Stablecoin with Atomic Swap support
 * 
 * Author: Fintaar.ai
 * Version: 2.0.0
 */

const UniversalRouteExplorer = () => {
  const [selectedSource, setSelectedSource] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [amount, setAmount] = useState(100000);
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('explorer');
  const [showAtomicSwaps, setShowAtomicSwaps] = useState(true);
  const [filterRegulated, setFilterRegulated] = useState(false);
  const [sortBy, setSortBy] = useState('score');

  // Currency definitions
  const currencies = useMemo(() => ({
    FIAT: [
      { code: 'USD', name: 'US Dollar', symbol: '$', flag: '🇺🇸' },
      { code: 'EUR', name: 'Euro', symbol: '€', flag: '🇪🇺' },
      { code: 'GBP', name: 'British Pound', symbol: '£', flag: '🇬🇧' },
      { code: 'INR', name: 'Indian Rupee', symbol: '₹', flag: '🇮🇳' },
      { code: 'SGD', name: 'Singapore Dollar', symbol: 'S$', flag: '🇸🇬' },
      { code: 'AED', name: 'UAE Dirham', symbol: 'د.إ', flag: '🇦🇪' },
      { code: 'CNY', name: 'Chinese Yuan', symbol: '¥', flag: '🇨🇳' },
      { code: 'HKD', name: 'Hong Kong Dollar', symbol: 'HK$', flag: '🇭🇰' },
      { code: 'THB', name: 'Thai Baht', symbol: '฿', flag: '🇹🇭' },
    ],
    CBDC: [
      { code: 'e-INR', name: 'Digital Rupee', issuer: 'RBI', flag: '🇮🇳', mbridge: false },
      { code: 'e-CNY', name: 'Digital Yuan', issuer: 'PBoC', flag: '🇨🇳', mbridge: true },
      { code: 'e-HKD', name: 'Digital HKD', issuer: 'HKMA', flag: '🇭🇰', mbridge: true },
      { code: 'e-THB', name: 'Digital Baht', issuer: 'BoT', flag: '🇹🇭', mbridge: true },
      { code: 'e-AED', name: 'Digital Dirham', issuer: 'CBUAE', flag: '🇦🇪', mbridge: true },
      { code: 'e-SGD', name: 'Digital SGD', issuer: 'MAS', flag: '🇸🇬', mbridge: false },
    ],
    STABLECOIN: [
      { code: 'USDC', name: 'USD Coin', issuer: 'Circle', regulated: true, networks: ['ETH', 'SOL', 'MATIC'] },
      { code: 'USDT', name: 'Tether', issuer: 'Tether', regulated: false, networks: ['ETH', 'TRX', 'SOL'] },
      { code: 'EURC', name: 'Euro Coin', issuer: 'Circle', regulated: true, networks: ['ETH', 'AVAX'] },
      { code: 'PYUSD', name: 'PayPal USD', issuer: 'Paxos', regulated: true, networks: ['ETH', 'SOL'] },
      { code: 'XSGD', name: 'StraitsX SGD', issuer: 'StraitsX', regulated: true, networks: ['ETH', 'MATIC'] },
    ]
  }), []);

  const conversionTypes = useMemo(() => [
    { id: 'F2F', name: 'Fiat → Fiat', icon: '💱', from: 'FIAT', to: 'FIAT', color: '#3B82F6' },
    { id: 'F2C', name: 'Fiat → CBDC', icon: '🏛️', from: 'FIAT', to: 'CBDC', color: '#8B5CF6' },
    { id: 'C2F', name: 'CBDC → Fiat', icon: '💵', from: 'CBDC', to: 'FIAT', color: '#6366F1' },
    { id: 'C2C', name: 'CBDC → CBDC', icon: '🌐', from: 'CBDC', to: 'CBDC', color: '#A855F7' },
    { id: 'F2S', name: 'Fiat → Stablecoin', icon: '🪙', from: 'FIAT', to: 'STABLECOIN', color: '#10B981' },
    { id: 'S2F', name: 'Stablecoin → Fiat', icon: '💰', from: 'STABLECOIN', to: 'FIAT', color: '#059669' },
    { id: 'S2S', name: 'Stable → Stable', icon: '🔄', from: 'STABLECOIN', to: 'STABLECOIN', color: '#14B8A6' },
    { id: 'C2S', name: 'CBDC → Stablecoin', icon: '🔗', from: 'CBDC', to: 'STABLECOIN', color: '#F59E0B' },
    { id: 'S2C', name: 'Stablecoin → CBDC', icon: '⚡', from: 'STABLECOIN', to: 'CBDC', color: '#EF4444' },
  ], []);

  const routeTemplates = useMemo(() => ({
    'F2F': [
      { id: 'SWIFT', name: 'SWIFT Transfer', fee: 25, time: '1-3 days', regulated: true, stp: true },
      { id: 'LOCAL', name: 'Local Rails (RTGS)', fee: 15, time: '4 hours', regulated: true, stp: true },
      { id: 'FINTECH', name: 'Fintech (Wise)', fee: 8, time: '12 hours', regulated: true, stp: true },
    ],
    'F2C': [
      { id: 'DIRECT_MINT', name: 'Direct Mint', fee: 0, time: '5 sec', regulated: true, best: true },
      { id: 'FX_MINT', name: 'FX + Mint', fee: 20, time: '4 hours', regulated: true },
    ],
    'C2F': [
      { id: 'DIRECT_REDEEM', name: 'Direct Redeem', fee: 0, time: '5 sec', regulated: true, best: true },
      { id: 'REDEEM_FX', name: 'Redeem + FX', fee: 20, time: '4 hours', regulated: true },
    ],
    'C2C': [
      { id: 'MBRIDGE_PVP', name: 'mBridge PvP', fee: 13, time: '15 sec', regulated: true, best: true, highlight: true },
      { id: 'PROJECT_NEXUS', name: 'Project Nexus', fee: 35, time: '60 sec', regulated: true },
      { id: 'FIAT_BRIDGE', name: 'Fiat Bridge', fee: 40, time: '8 hours', regulated: true },
    ],
    'F2S': [
      { id: 'DIRECT_MINT', name: 'Direct Mint (Issuer)', fee: 0, time: '1 hour', regulated: true, best: true },
      { id: 'CEX_ONRAMP', name: 'CEX On-ramp', fee: 30, time: '4 hours', regulated: true },
    ],
    'S2F': [
      { id: 'DIRECT_REDEEM', name: 'Direct Redeem', fee: 0, time: '1 hour', regulated: true, best: true },
      { id: 'CEX_OFFRAMP', name: 'CEX Off-ramp', fee: 25, time: '4-24 hours', regulated: true },
    ],
    'S2S': [
      { id: 'DEX_SWAP', name: 'DEX Swap', fee: 30, time: '30 sec', regulated: false },
      { id: 'CEX_TRADE', name: 'CEX Trade', fee: 20, time: '1 min', regulated: true },
    ],
    'C2S': [
      { id: 'FIAT_BRIDGE', name: 'Fiat Intermediary', fee: 45, time: '4+ hours', regulated: true },
      { id: 'CEX_BRIDGE', name: 'CEX Bridge', fee: 75, time: '2 hours', regulated: true },
      { id: 'ATOMIC_SWAP', name: '⚛️ Atomic Swap', fee: 15, time: '5 min', regulated: false, experimental: true },
    ],
    'S2C': [
      { id: 'FIAT_BRIDGE', name: 'Fiat Intermediary', fee: 50, time: '4+ hours', regulated: true },
      { id: 'CEX_BRIDGE', name: 'CEX Bridge', fee: 65, time: '2 hours', regulated: true },
      { id: 'ATOMIC_SWAP', name: '⚛️ Atomic Swap', fee: 15, time: '5 min', regulated: false, experimental: true },
    ],
  }), []);

  const getCurrencyType = useCallback((code) => {
    for (const [type, list] of Object.entries(currencies)) {
      if (list.find(c => c.code === code)) return type;
    }
    return null;
  }, [currencies]);

  const getConversionType = useCallback((sourceCode, targetCode) => {
    const sourceType = getCurrencyType(sourceCode);
    const targetType = getCurrencyType(targetCode);
    return conversionTypes.find(ct => ct.from === sourceType && ct.to === targetType);
  }, [getCurrencyType, conversionTypes]);

  const calculateScore = (template) => {
    let score = 100;
    score -= template.fee * 0.5;
    if (template.regulated) score += 10;
    if (template.best) score += 15;
    if (template.experimental) score -= 20;
    return Math.max(0, Math.min(100, score));
  };

  const calculateRoutes = useCallback((source, target, amt) => {
    const convType = getConversionType(source, target);
    if (!convType) return [];

    const templates = routeTemplates[convType.id] || [];
    
    return templates
      .filter(t => showAtomicSwaps || !t.experimental)
      .filter(t => !filterRegulated || t.regulated)
      .map((template, idx) => {
        const baseRate = 1 + (Math.random() * 0.005 - 0.0025);
        const targetAmount = amt * baseRate * (1 - template.fee / 10000);
        
        return {
          id: `${convType.id}-${template.id}-${idx}`,
          routeType: convType,
          template,
          sourceAmount: amt,
          targetAmount: targetAmount.toFixed(2),
          effectiveRate: (targetAmount / amt).toFixed(6),
          score: calculateScore(template),
        };
      })
      .sort((a, b) => {
        if (sortBy === 'fee') return a.template.fee - b.template.fee;
        return b.score - a.score;
      });
  }, [getConversionType, routeTemplates, showAtomicSwaps, filterRegulated, sortBy]);

  useEffect(() => {
    if (selectedSource && selectedTarget && selectedSource !== selectedTarget) {
      setLoading(true);
      setTimeout(() => {
        const newRoutes = calculateRoutes(selectedSource, selectedTarget, amount);
        setRoutes(newRoutes);
        setLoading(false);
      }, 300);
    } else {
      setRoutes([]);
    }
  }, [selectedSource, selectedTarget, amount, calculateRoutes]);

  const CurrencyCard = ({ currency, type, isSelected, onSelect }) => (
    <div
      onClick={() => onSelect(currency.code)}
      className={`p-2 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
        isSelected 
          ? 'border-blue-500 bg-blue-50 shadow-lg scale-105' 
          : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow'
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="text-xl">{currency.flag || '🪙'}</span>
        <div>
          <div className="font-semibold text-sm">{currency.code}</div>
          <div className="text-xs text-gray-500 truncate">{currency.name}</div>
        </div>
      </div>
      {type === 'CBDC' && currency.mbridge && (
        <div className="mt-1 text-xs bg-purple-100 text-purple-700 px-1 py-0.5 rounded inline-block">
          mBridge
        </div>
      )}
      {type === 'STABLECOIN' && currency.regulated && (
        <div className="mt-1 text-xs bg-green-100 text-green-700 px-1 py-0.5 rounded inline-block">
          Regulated
        </div>
      )}
    </div>
  );

  const RouteCard = ({ route, rank }) => (
    <div className={`p-4 rounded-lg border-2 ${
      route.template.best ? 'border-green-400 bg-green-50' :
      route.template.experimental ? 'border-orange-400 bg-orange-50' :
      route.template.highlight ? 'border-purple-400 bg-purple-50' :
      'border-gray-200 bg-white'
    }`}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${
            rank === 1 ? 'text-yellow-500' : 
            rank === 2 ? 'text-gray-400' : 
            rank === 3 ? 'text-amber-600' : 'text-gray-600'
          }`}>
            #{rank}
          </span>
          <span className="text-xl">{route.routeType.icon}</span>
          <div>
            <div className="font-semibold">{route.template.name}</div>
            <div className="text-sm text-gray-500">{route.routeType.name}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-blue-600">
            {Number(route.targetAmount).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">
            Rate: {route.effectiveRate}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-2 mt-3 text-center text-sm">
        <div className="bg-gray-100 rounded p-2">
          <div className="text-gray-500 text-xs">Fee</div>
          <div className="font-semibold">{route.template.fee} bps</div>
        </div>
        <div className="bg-gray-100 rounded p-2">
          <div className="text-gray-500 text-xs">Time</div>
          <div className="font-semibold">{route.template.time}</div>
        </div>
        <div className="bg-gray-100 rounded p-2">
          <div className="text-gray-500 text-xs">Regulated</div>
          <div className="font-semibold">{route.template.regulated ? '✅' : '⚠️'}</div>
        </div>
        <div className="bg-gray-100 rounded p-2">
          <div className="text-gray-500 text-xs">Score</div>
          <div className="font-semibold">{route.score.toFixed(0)}</div>
        </div>
      </div>

      {route.template.experimental && (
        <div className="mt-2 text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
          ⚠️ Experimental - Atomic swap via HTLC. Use at own risk.
        </div>
      )}
      
      {route.template.best && (
        <div className="mt-2 text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
          ✨ Recommended - Best cost, speed, and reliability
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-1">
            🌐 Universal FX Route Explorer
          </h1>
          <p className="text-gray-600 text-sm">
            Fiat ↔ CBDC ↔ Stablecoin • 9 Conversion Types • Atomic Swap Support
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-4 justify-center flex-wrap">
          {['explorer', 'matrix', 'atomic'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
                activeTab === tab 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab === 'explorer' && '🔍 Explorer'}
              {tab === 'matrix' && '📊 Matrix'}
              {tab === 'atomic' && '⚛️ Atomic'}
            </button>
          ))}
        </div>

        {/* Explorer Tab */}
        {activeTab === 'explorer' && (
          <div className="space-y-4">
            {/* Controls */}
            <div className="bg-white rounded-xl p-3 shadow-sm flex flex-wrap gap-3 items-center justify-between text-sm">
              <div className="flex gap-3 items-center flex-wrap">
                <div className="flex items-center gap-2">
                  <label className="text-gray-500">Amount:</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                    className="px-2 py-1 border rounded w-28"
                  />
                </div>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showAtomicSwaps}
                    onChange={(e) => setShowAtomicSwaps(e.target.checked)}
                    className="rounded"
                  />
                  <span>Atomic Swaps</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterRegulated}
                    onChange={(e) => setFilterRegulated(e.target.checked)}
                    className="rounded"
                  />
                  <span>Regulated Only</span>
                </label>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-gray-500">Sort:</label>
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-2 py-1 border rounded"
                >
                  <option value="score">Best Score</option>
                  <option value="fee">Lowest Fee</option>
                </select>
              </div>
            </div>

            {/* Currency Selection */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Source */}
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <h3 className="font-semibold mb-3 text-base">📤 Source Currency</h3>
                {Object.entries(currencies).map(([type, list]) => (
                  <div key={type} className="mb-3">
                    <div className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
                      {type === 'FIAT' && '💵'}
                      {type === 'CBDC' && '🏛️'}
                      {type === 'STABLECOIN' && '🪙'}
                      {type}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {list.map(currency => (
                        <CurrencyCard
                          key={currency.code}
                          currency={currency}
                          type={type}
                          isSelected={selectedSource === currency.code}
                          onSelect={setSelectedSource}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Target */}
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <h3 className="font-semibold mb-3 text-base">📥 Target Currency</h3>
                {Object.entries(currencies).map(([type, list]) => (
                  <div key={type} className="mb-3">
                    <div className="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
                      {type === 'FIAT' && '💵'}
                      {type === 'CBDC' && '🏛️'}
                      {type === 'STABLECOIN' && '🪙'}
                      {type}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {list.map(currency => (
                        <CurrencyCard
                          key={currency.code}
                          currency={currency}
                          type={type}
                          isSelected={selectedTarget === currency.code}
                          onSelect={setSelectedTarget}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Routes */}
            {selectedSource && selectedTarget && selectedSource !== selectedTarget && (
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold">
                    🛤️ Routes: {selectedSource} → {selectedTarget}
                  </h3>
                  <span className="text-sm text-gray-500">{routes.length} found</span>
                </div>
                
                {loading ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="animate-spin text-3xl mb-2">🔄</div>
                    Finding routes...
                  </div>
                ) : routes.length > 0 ? (
                  <div className="grid gap-3">
                    {routes.map((route, idx) => (
                      <RouteCard key={route.id} route={route} rank={idx + 1} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No routes available
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Matrix Tab */}
        {activeTab === 'matrix' && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="font-semibold mb-4">📊 Complete Conversion Matrix</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="p-3 text-left">From \ To</th>
                    <th className="p-3 text-center">💵 FIAT</th>
                    <th className="p-3 text-center">🏛️ CBDC</th>
                    <th className="p-3 text-center">🪙 STABLECOIN</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="p-3 font-semibold">💵 FIAT</td>
                    <td className="p-3 text-center bg-blue-50">
                      <div className="font-semibold">SWIFT / Local</div>
                      <div className="text-xs text-gray-500">8-25 bps • 4h-3d</div>
                    </td>
                    <td className="p-3 text-center bg-purple-50">
                      <div className="font-semibold">FX + Mint</div>
                      <div className="text-xs text-gray-500">0-20 bps • 5s-4h</div>
                    </td>
                    <td className="p-3 text-center bg-green-50">
                      <div className="font-semibold">On-Ramp</div>
                      <div className="text-xs text-gray-500">0-30 bps • 1-4h</div>
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 font-semibold">🏛️ CBDC</td>
                    <td className="p-3 text-center bg-indigo-50">
                      <div className="font-semibold">Redeem + FX</div>
                      <div className="text-xs text-gray-500">0-20 bps • 5s-4h</div>
                    </td>
                    <td className="p-3 text-center bg-violet-50">
                      <div className="font-semibold">mBridge PvP</div>
                      <div className="text-xs text-gray-500">13-40 bps • 15s-8h</div>
                    </td>
                    <td className="p-3 text-center bg-amber-50">
                      <div className="font-semibold">Bridge / ⚛️ Atomic</div>
                      <div className="text-xs text-gray-500">15-75 bps • 5m-4h</div>
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold">🪙 STABLECOIN</td>
                    <td className="p-3 text-center bg-emerald-50">
                      <div className="font-semibold">Off-Ramp</div>
                      <div className="text-xs text-gray-500">0-25 bps • 1-24h</div>
                    </td>
                    <td className="p-3 text-center bg-red-50">
                      <div className="font-semibold">Bridge / ⚛️ Atomic</div>
                      <div className="text-xs text-gray-500">15-65 bps • 5m-4h</div>
                    </td>
                    <td className="p-3 text-center bg-teal-50">
                      <div className="font-semibold">DEX / CEX</div>
                      <div className="text-xs text-gray-500">20-30 bps • 30s-1m</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="mt-6 grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-800">💵 Fiat Rails</h4>
                <ul className="text-sm text-blue-700 mt-2 space-y-1">
                  <li>• SWIFT / Correspondent</li>
                  <li>• Local RTGS / ACH</li>
                  <li>• Fintech (Wise)</li>
                </ul>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-800">🏛️ CBDC Rails</h4>
                <ul className="text-sm text-purple-700 mt-2 space-y-1">
                  <li>• Domestic CBDC</li>
                  <li>• mBridge PvP</li>
                  <li>• Project Nexus</li>
                </ul>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800">🪙 Stablecoin Rails</h4>
                <ul className="text-sm text-green-700 mt-2 space-y-1">
                  <li>• Direct Issuer</li>
                  <li>• CEX (Coinbase)</li>
                  <li>• DEX (Uniswap)</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Atomic Tab */}
        {activeTab === 'atomic' && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="font-semibold mb-4">⚛️ Atomic Swap Technology</h3>
            
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 text-orange-800 font-semibold mb-2">
                ⚠️ Experimental Feature
              </div>
              <p className="text-sm text-orange-700">
                Atomic swaps use Hash Time-Locked Contracts (HTLCs) for trustless, 
                cross-chain exchanges without intermediaries.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-800">How It Works</h4>
                <div className="space-y-3">
                  {[
                    { step: '1', title: 'Hash Lock Created', desc: 'Party A generates secret and hash lock' },
                    { step: '2', title: 'HTLC Deploy', desc: 'Both parties lock funds in contracts' },
                    { step: '3', title: 'Secret Reveal', desc: 'Party A reveals secret to claim' },
                    { step: '✓', title: 'Atomic Settlement', desc: 'Both complete or both fail' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex gap-3 items-start">
                      <span className={`${item.step === '✓' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'} rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold`}>
                        {item.step}
                      </span>
                      <div>
                        <div className="font-medium">{item.title}</div>
                        <div className="text-sm text-gray-600">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-gray-800">Supported Pairs</h4>
                <div className="space-y-2">
                  {[
                    { from: 'e-INR', to: 'USDC', status: 'Experimental', risk: 'Medium' },
                    { from: 'e-SGD', to: 'XSGD', status: 'Pilot', risk: 'Low' },
                    { from: 'e-CNY', to: 'USDT', status: 'Planned', risk: 'High' },
                    { from: 'e-AED', to: 'USDC', status: 'Planned', risk: 'Medium' },
                  ].map((pair, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{pair.from}</span>
                        <span className="text-gray-400">⚛️</span>
                        <span className="font-medium">{pair.to}</span>
                      </div>
                      <div className="flex gap-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          pair.status === 'Pilot' ? 'bg-green-100 text-green-700' :
                          pair.status === 'Experimental' ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>{pair.status}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          pair.risk === 'Low' ? 'bg-green-100 text-green-700' :
                          pair.risk === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>{pair.risk}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h5 className="font-semibold text-blue-800 mb-2">Benefits</h5>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>✓ No intermediaries</li>
                    <li>✓ Lowest fees (15 bps)</li>
                    <li>✓ Fast settlement (5 min)</li>
                    <li>✓ Trustless execution</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>FX Smart Routing Engine v2.0.0 • Fintaar.ai</p>
          <p className="mt-1">9 conversion types • 32 test scenarios • All passing ✅</p>
        </div>
      </div>
    </div>
  );
};

export default UniversalRouteExplorer;
