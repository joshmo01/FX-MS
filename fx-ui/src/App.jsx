import { useState, useEffect } from 'react';
import * as api from './services/api';

const StatusBadge = ({ status }) => {
  const colors = {
    DRAFT: 'bg-gray-100 text-gray-800',
    PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
    ACTIVE: 'bg-green-100 text-green-800',
    EXPIRED: 'bg-red-100 text-red-800',
    FULLY_UTILIZED: 'bg-blue-100 text-blue-800',
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100'}`}>
      {status?.replace('_', ' ')}
    </span>
  );
};

function App() {
  const [tab, setTab] = useState('dashboard');
  const [deals, setDeals] = useState([]);
  const [rates, setRates] = useState({});
  const [cbdcs, setCbdcs] = useState([]);
  const [stablecoins, setStablecoins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: "Hi! I'm your FX assistant. Ask me about rates, deals, or routes!" }
  ]);
  const [chatInput, setChatInput] = useState('');

  // Route calculator state
  const [routeForm, setRouteForm] = useState({
    currency_pair: 'USDINR',
    side: 'SELL',
    amount: '100000',
    customer_tier: 'GOLD',
  });
  const [routeResult, setRouteResult] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);

  // Pricing state
  const [pricingForm, setPricingForm] = useState({
    source_currency: 'USD',
    target_currency: 'INR',
    amount: '100000',
    segment: 'MID_MARKET',
    direction: 'SELL',
    customer_id: 'CUST-001',
  });
  const [pricingResult, setPricingResult] = useState(null);
  const [pricingLoading, setPricingLoading] = useState(false);
  const [pricingError, setPricingError] = useState(null);
  const [segments, setSegments] = useState([]);
  const [tiers, setTiers] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dealsRes, ratesRes, cbdcRes, stableRes, segmentsRes, tiersRes] = await Promise.all([
        api.getDeals({}).catch(e => ({ data: { deals: [] } })),
        api.getTreasuryRates().catch(e => ({ data: { rates: {} } })),
        api.getCBDCs().catch(e => ({ data: { cbdc: [] } })),
        api.getStablecoins().catch(e => ({ data: { stablecoins: [] } })),
        fetch('http://127.0.0.1:8000/api/v1/fx/pricing/segments').then(r => r.json()).catch(e => []),
        fetch('http://127.0.0.1:8000/api/v1/fx/pricing/tiers').then(r => r.json()).catch(e => []),
      ]);

      setDeals(dealsRes.data?.deals || []);
      setRates(ratesRes.data?.rates || {});
      setCbdcs(cbdcRes.data?.cbdc || []);
      setStablecoins(stableRes.data?.stablecoins || []);
      setSegments(segmentsRes || []);
      setTiers(tiersRes || []);
    } catch (e) {
      console.error('Fetch error:', e);
    }
    setLoading(false);
  };

  const handleCreateDeal = async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await api.createDeal({
        currency_pair: form.get('pair'),
        side: form.get('side'),
        buy_rate: parseFloat(form.get('buy_rate')),
        sell_rate: parseFloat(form.get('sell_rate')),
        amount: parseFloat(form.get('amount')),
        valid_from: form.get('valid_from'),
        valid_until: form.get('valid_until'),
        min_amount: 1000,
        created_by: 'treasury_user',
      });
      setShowCreate(false);
      fetchData();
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
  };

  const handleSubmit = async (id) => {
    try {
      await api.submitDeal(id, { submitted_by: 'treasury_user' });
      fetchData();
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
  };

  const handleApprove = async (id) => {
    try {
      await api.approveDeal(id, { approved_by: 'senior_treasury' });
      fetchData();
    } catch (e) { alert(e.response?.data?.detail || 'Error'); }
  };

  const calculateRoute = async () => {
    setRouteLoading(true);
    try {
      const pair = routeForm.currency_pair;
      const treasuryRate = rates[pair]?.ask || rates[pair]?.bid || 84.55;

      const bestRateRes = await api.getBestRate({
        currency_pair: pair,
        side: routeForm.side,
        amount: parseFloat(routeForm.amount),
        customer_tier: routeForm.customer_tier,
        treasury_rate: treasuryRate,
      });

      setRouteResult({
        ...bestRateRes.data,
        treasuryRate,
        amount: parseFloat(routeForm.amount),
      });
    } catch (e) {
      console.error('Route error:', e);
      const pair = routeForm.currency_pair;
      const treasuryRate = rates[pair]?.ask || 84.55;
      setRouteResult({
        currency_pair: pair,
        side: routeForm.side,
        rate: treasuryRate,
        source: 'TREASURY',
        deal_id: null,
        savings_bps: 0,
        treasury_rate: treasuryRate,
        amount: parseFloat(routeForm.amount),
      });
    }
    setRouteLoading(false);
  };

  const calculatePricing = async () => {
    setPricingLoading(true);
    setPricingError(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/fx/pricing/quote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_currency: pricingForm.source_currency,
          target_currency: pricingForm.target_currency,
          amount: parseFloat(pricingForm.amount),
          customer_id: pricingForm.customer_id,
          segment: pricingForm.segment,
          direction: pricingForm.direction,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setPricingResult(data);
    } catch (e) {
      console.error('Pricing error:', e);
      setPricingError(e.message);
    }
    setPricingLoading(false);
  };

  const sendChat = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput;
    setChatMessages(m => [...m, { role: 'user', content: msg }]);
    setChatInput('');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/fx/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setChatMessages(m => [...m, { role: 'assistant', content: data.response || data.detail || 'Error' }]);
    } catch (e) {
      setChatMessages(m => [...m, { role: 'assistant', content: 'Chat API not available.' }]);
    }
  };

  const activeDeals = deals.filter(d => d.status === 'ACTIVE').length;
  const pendingDeals = deals.filter(d => d.status === 'PENDING_APPROVAL').length;

  const currencyPairs = ['USDINR', 'EURINR', 'GBPINR', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDSGD', 'USDAED', 'USDCNY'];
  const customerTiers = ['PLATINUM', 'GOLD', 'SILVER', 'BRONZE', 'RETAIL'];
  const currencies = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AED', 'SGD', 'AUD', 'CAD', 'CHF'];
  const customerSegments = ['RETAIL', 'SMALL_BUSINESS', 'MID_MARKET', 'LARGE_CORPORATE', 'PRIVATE_BANKING', 'INSTITUTIONAL'];

  const swapCurrencies = () => {
    setPricingForm({
      ...pricingForm,
      source_currency: pricingForm.target_currency,
      target_currency: pricingForm.source_currency,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="text-2xl">💱</span>
            <h1 className="text-xl font-bold">FX Smart Routing</h1>
          </div>
          <nav className="flex gap-2">
            {['dashboard', 'deals', 'rates', 'routes', 'pricing'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg font-medium ${tab === t ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full"></div>
          </div>
        ) : (
          <>
            {/* Dashboard */}
            {tab === 'dashboard' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">Dashboard</h2>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-xl text-white">
                    <p className="text-sm opacity-80">Active Deals</p>
                    <p className="text-3xl font-bold">{activeDeals}</p>
                  </div>
                  <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-6 rounded-xl text-white">
                    <p className="text-sm opacity-80">Pending Approval</p>
                    <p className="text-3xl font-bold">{pendingDeals}</p>
                  </div>
                  <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-6 rounded-xl text-white">
                    <p className="text-sm opacity-80">Currency Pairs</p>
                    <p className="text-3xl font-bold">{Object.keys(rates).length}</p>
                  </div>
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 rounded-xl text-white">
                    <p className="text-sm opacity-80">Segments</p>
                    <p className="text-3xl font-bold">{segments.length}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">Live Rates</h3>
                    <table className="w-full text-sm">
                      <thead><tr className="text-left text-gray-500"><th>Pair</th><th>Bid</th><th>Ask</th><th>Position</th></tr></thead>
                      <tbody>
                        {Object.entries(rates).slice(0, 6).map(([pair, r]) => (
                          <tr key={pair} className="border-t">
                            <td className="py-2 font-medium">{pair}</td>
                            <td>{r.bid?.toFixed(4)}</td>
                            <td>{r.ask?.toFixed(4)}</td>
                            <td><span className={`px-2 py-1 rounded text-xs ${r.position === 'LONG' ? 'bg-blue-100 text-blue-700' : r.position === 'SHORT' ? 'bg-red-100 text-red-700' : 'bg-gray-100'}`}>{r.position}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">Recent Deals</h3>
                    {deals.length === 0 ? (
                      <p className="text-gray-500">No deals yet. Create one!</p>
                    ) : (
                      deals.slice(0, 5).map(d => (
                        <div key={d.deal_id} className="flex justify-between items-center py-2 border-b">
                          <div>
                            <p className="font-medium">{d.deal_id}</p>
                            <p className="text-sm text-gray-500">{d.currency_pair} - ${(d.amount/1000).toFixed(0)}K</p>
                          </div>
                          <StatusBadge status={d.status} />
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Deals */}
            {tab === 'deals' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold">Deals Management</h2>
                  <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">+ Create Deal</button>
                </div>

                <div className="bg-white rounded-xl shadow overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr className="text-left text-xs text-gray-500 uppercase">
                        <th className="px-6 py-3">Deal ID</th>
                        <th className="px-6 py-3">Pair</th>
                        <th className="px-6 py-3">Side</th>
                        <th className="px-6 py-3">Amount</th>
                        <th className="px-6 py-3">Buy/Sell</th>
                        <th className="px-6 py-3">Status</th>
                        <th className="px-6 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deals.length === 0 ? (
                        <tr><td colSpan="7" className="px-6 py-8 text-center text-gray-500">No deals yet</td></tr>
                      ) : (
                        deals.map(d => (
                          <tr key={d.deal_id} className="border-t hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-blue-600">{d.deal_id}</td>
                            <td className="px-6 py-4">{d.currency_pair}</td>
                            <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${d.side === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{d.side}</span></td>
                            <td className="px-6 py-4">${(d.amount/1000).toFixed(0)}K</td>
                            <td className="px-6 py-4">{d.buy_rate} / {d.sell_rate}</td>
                            <td className="px-6 py-4"><StatusBadge status={d.status} /></td>
                            <td className="px-6 py-4 space-x-2">
                              {d.status === 'DRAFT' && <button onClick={() => handleSubmit(d.deal_id)} className="text-blue-600 hover:underline">Submit</button>}
                              {d.status === 'PENDING_APPROVAL' && <button onClick={() => handleApprove(d.deal_id)} className="text-green-600 hover:underline">Approve</button>}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {showCreate && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-lg">
                      <h3 className="text-lg font-semibold mb-4">Create New Deal</h3>
                      <form onSubmit={handleCreateDeal} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">Currency Pair</label>
                            <select name="pair" className="w-full border rounded-lg px-3 py-2">
                              <option>USDINR</option><option>EURUSD</option><option>GBPUSD</option><option>EURINR</option><option>GBPINR</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Side</label>
                            <select name="side" className="w-full border rounded-lg px-3 py-2">
                              <option>SELL</option><option>BUY</option>
                            </select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">Buy Rate</label>
                            <input name="buy_rate" type="number" step="0.0001" defaultValue="84.40" required className="w-full border rounded-lg px-3 py-2" />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Sell Rate</label>
                            <input name="sell_rate" type="number" step="0.0001" defaultValue="84.55" required className="w-full border rounded-lg px-3 py-2" />
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Amount (USD)</label>
                          <input name="amount" type="number" defaultValue="500000" required className="w-full border rounded-lg px-3 py-2" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">Valid From</label>
                            <input name="valid_from" type="datetime-local" required className="w-full border rounded-lg px-3 py-2" />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Valid Until</label>
                            <input name="valid_until" type="datetime-local" required className="w-full border rounded-lg px-3 py-2" />
                          </div>
                        </div>
                        <div className="flex justify-end gap-3 pt-4">
                          <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-100 rounded-lg">Cancel</button>
                          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Create</button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Rates */}
            {tab === 'rates' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">FX Rates</h2>

                <div className="bg-white rounded-xl shadow p-6">
                  <h3 className="font-semibold mb-4">Treasury Rates</h3>
                  <table className="w-full">
                    <thead><tr className="text-left text-xs text-gray-500 uppercase"><th className="pb-3">Pair</th><th>Bid</th><th>Ask</th><th>Mid</th><th>Position</th></tr></thead>
                    <tbody>
                      {Object.entries(rates).map(([pair, r]) => (
                        <tr key={pair} className="border-t">
                          <td className="py-3 font-medium">{pair}</td>
                          <td>{r.bid?.toFixed(4)}</td>
                          <td>{r.ask?.toFixed(4)}</td>
                          <td>{r.mid?.toFixed(4)}</td>
                          <td><span className={`px-2 py-1 rounded text-xs ${r.position === 'LONG' ? 'bg-blue-100 text-blue-700' : r.position === 'SHORT' ? 'bg-red-100 text-red-700' : 'bg-gray-100'}`}>{r.position}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">CBDCs ({cbdcs.length})</h3>
                    {cbdcs.length === 0 ? (
                      <p className="text-gray-500 text-sm">Loading...</p>
                    ) : (
                      <table className="w-full text-sm">
                        <thead><tr className="text-left text-gray-500"><th>Code</th><th>Name</th><th>Issuer</th><th>mBridge</th></tr></thead>
                        <tbody>
                          {cbdcs.map(c => (
                            <tr key={c.code} className="border-t">
                              <td className="py-2 font-medium">{c.code}</td>
                              <td>{c.name}</td>
                              <td>{c.issuer}</td>
                              <td>{c.mbridge ? '✅' : '❌'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">Stablecoins ({stablecoins.length})</h3>
                    <table className="w-full text-sm">
                      <thead><tr className="text-left text-gray-500"><th>Code</th><th>Name</th><th>Issuer</th><th>Regulated</th></tr></thead>
                      <tbody>
                        {stablecoins.map(s => (
                          <tr key={s.code} className="border-t">
                            <td className="py-2 font-medium">{s.code}</td>
                            <td>{s.name}</td>
                            <td>{s.issuer}</td>
                            <td>{s.regulated ? '✅' : '❌'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Routes */}
            {tab === 'routes' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">Route Calculator</h2>
                <p className="text-gray-500">Find the optimal FX route for your transaction</p>

                <div className="bg-white rounded-xl shadow p-6">
                  <h3 className="font-semibold mb-4">Calculate Best Route</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Currency Pair</label>
                      <select value={routeForm.currency_pair} onChange={e => setRouteForm({...routeForm, currency_pair: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                        {currencyPairs.map(pair => (<option key={pair} value={pair}>{pair}</option>))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Amount (USD)</label>
                      <input type="number" value={routeForm.amount} onChange={e => setRouteForm({...routeForm, amount: e.target.value})} className="w-full border rounded-lg px-3 py-2" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Side</label>
                      <select value={routeForm.side} onChange={e => setRouteForm({...routeForm, side: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                        <option value="BUY">BUY</option>
                        <option value="SELL">SELL</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Customer Tier</label>
                      <select value={routeForm.customer_tier} onChange={e => setRouteForm({...routeForm, customer_tier: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                        {customerTiers.map(tier => (<option key={tier} value={tier}>{tier}</option>))}
                      </select>
                    </div>
                  </div>
                  <button onClick={calculateRoute} disabled={routeLoading} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                    {routeLoading ? (<><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>Calculating...</>) : (<>🔍 Calculate Route</>)}
                  </button>
                </div>

                {routeResult && (
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">Route Recommendation</h3>
                    <div className={`rounded-xl p-6 mb-6 ${routeResult.source === 'DEAL' ? 'bg-green-50 border border-green-200' : 'bg-blue-50 border border-blue-200'}`}>
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">🏆</span>
                        <span className="font-semibold text-lg">Best Route: {routeResult.source === 'DEAL' ? 'Treasury Deal' : 'Treasury Rate'}</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div><p className="text-sm text-gray-500">Rate</p><p className="text-2xl font-bold">{routeResult.rate?.toFixed(4)}</p></div>
                        <div><p className="text-sm text-gray-500">Currency Pair</p><p className="text-lg font-medium">{routeResult.currency_pair}</p></div>
                        <div><p className="text-sm text-gray-500">Side</p><p className="text-lg font-medium">{routeResult.side}</p></div>
                        <div><p className="text-sm text-gray-500">Amount</p><p className="text-lg font-medium">${routeResult.amount?.toLocaleString()}</p></div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium mb-2">Conversion Preview</h4>
                      <p className="text-lg">${routeResult.amount?.toLocaleString()} USD × {routeResult.rate?.toFixed(4)} = <span className="font-bold">{(routeResult.amount * routeResult.rate)?.toLocaleString(undefined, {maximumFractionDigits: 2})} {routeResult.currency_pair?.slice(3)}</span></p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Pricing - NEW TAB */}
            {tab === 'pricing' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">FX Pricing Service</h2>
                <p className="text-gray-500">Get customer-specific pricing with segmentation and volume tiers</p>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Quote Form */}
                  <div className="lg:col-span-1">
                    <div className="bg-white rounded-xl shadow p-6">
                      <h3 className="font-semibold mb-4">💰 Get Quote</h3>
                      
                      {pricingError && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                          {pricingError}
                        </div>
                      )}

                      <div className="space-y-4">
                        <div className="grid grid-cols-5 gap-2 items-end">
                          <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
                            <select value={pricingForm.source_currency} onChange={e => setPricingForm({...pricingForm, source_currency: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                              {currencies.map(c => (<option key={c} value={c}>{c}</option>))}
                            </select>
                          </div>
                          <div className="flex justify-center">
                            <button onClick={swapCurrencies} className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200">⇄</button>
                          </div>
                          <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
                            <select value={pricingForm.target_currency} onChange={e => setPricingForm({...pricingForm, target_currency: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                              {currencies.map(c => (<option key={c} value={c}>{c}</option>))}
                            </select>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                          <input type="number" value={pricingForm.amount} onChange={e => setPricingForm({...pricingForm, amount: e.target.value})} className="w-full border rounded-lg px-3 py-2" />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Customer Segment</label>
                          <select value={pricingForm.segment} onChange={e => setPricingForm({...pricingForm, segment: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                            {customerSegments.map(s => (<option key={s} value={s}>{s.replace('_', ' ')}</option>))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Direction</label>
                          <select value={pricingForm.direction} onChange={e => setPricingForm({...pricingForm, direction: e.target.value})} className="w-full border rounded-lg px-3 py-2">
                            <option value="SELL">SELL (Convert from source)</option>
                            <option value="BUY">BUY (Acquire source)</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Customer ID</label>
                          <input type="text" value={pricingForm.customer_id} onChange={e => setPricingForm({...pricingForm, customer_id: e.target.value})} className="w-full border rounded-lg px-3 py-2" />
                        </div>

                        <button onClick={calculatePricing} disabled={pricingLoading} className="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium">
                          {pricingLoading ? (<><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>Getting Quote...</>) : (<>Get Quote</>)}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Quote Result */}
                  <div className="lg:col-span-2">
                    {pricingResult ? (
                      <div className="bg-white rounded-xl shadow p-6">
                        <div className="flex justify-between items-start mb-6">
                          <div>
                            <h3 className="font-semibold text-lg">Quote Result</h3>
                            <p className="text-sm text-gray-500 font-mono">{pricingResult.quote_id}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-sm text-green-600">Valid until</span>
                            <p className="text-sm font-medium">{new Date(pricingResult.valid_until).toLocaleTimeString()}</p>
                          </div>
                        </div>

                        {/* Rate Display */}
                        <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl p-6 text-white text-center mb-6">
                          <p className="text-sm opacity-80 mb-1">Customer Rate</p>
                          <p className="text-4xl font-bold">{pricingResult.customer_rate?.toFixed(4)}</p>
                          <p className="text-sm opacity-80 mt-2">{pricingResult.source_currency}/{pricingResult.target_currency}</p>
                        </div>

                        {/* Conversion */}
                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-gray-50 rounded-lg p-4 text-center">
                            <p className="text-sm text-gray-500">You Send</p>
                            <p className="text-xl font-bold">{parseFloat(pricingResult.source_amount).toLocaleString()}</p>
                            <p className="text-sm text-gray-500">{pricingResult.source_currency}</p>
                          </div>
                          <div className="flex items-center justify-center text-2xl text-gray-400">→</div>
                          <div className="bg-gray-50 rounded-lg p-4 text-center">
                            <p className="text-sm text-gray-500">You Receive</p>
                            <p className="text-xl font-bold">{parseFloat(pricingResult.target_amount).toLocaleString()}</p>
                            <p className="text-sm text-gray-500">{pricingResult.target_currency}</p>
                          </div>
                        </div>

                        {/* Info Badges */}
                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-blue-50 rounded-lg p-3 text-center">
                            <p className="text-xs text-blue-600 uppercase">Segment</p>
                            <p className="font-medium text-blue-800">{pricingResult.segment?.replace('_', ' ')}</p>
                          </div>
                          <div className="bg-purple-50 rounded-lg p-3 text-center">
                            <p className="text-xs text-purple-600 uppercase">Amount Tier</p>
                            <p className="font-medium text-purple-800">{pricingResult.amount_tier}</p>
                          </div>
                          <div className="bg-orange-50 rounded-lg p-3 text-center">
                            <p className="text-xs text-orange-600 uppercase">Currency Type</p>
                            <p className="font-medium text-orange-800">{pricingResult.currency_category}</p>
                          </div>
                        </div>

                        {/* Margin Breakdown */}
                        <div className="border-t pt-4">
                          <h4 className="font-medium mb-3">💹 Margin Breakdown</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between"><span className="text-gray-500">Mid-Market Rate</span><span className="font-mono">{pricingResult.mid_rate?.toFixed(4)}</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Segment Base</span><span className="font-mono text-red-600">+{pricingResult.margin_breakdown?.segment_base_bps} bps</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Tier Adjustment</span><span className={`font-mono ${pricingResult.margin_breakdown?.tier_adjustment_bps < 0 ? 'text-green-600' : 'text-red-600'}`}>{pricingResult.margin_breakdown?.tier_adjustment_bps >= 0 ? '+' : ''}{pricingResult.margin_breakdown?.tier_adjustment_bps} bps</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Currency Factor</span><span className="font-mono text-red-600">+{pricingResult.margin_breakdown?.currency_factor_bps} bps</span></div>
                            <div className="flex justify-between font-medium border-t pt-2 mt-2"><span>Total Margin</span><span className="text-green-600">{pricingResult.margin_bps} bps ({pricingResult.margin_percent?.toFixed(2)}%)</span></div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-white rounded-xl shadow p-6 flex items-center justify-center h-full min-h-[400px]">
                        <div className="text-center text-gray-400">
                          <p className="text-4xl mb-4">💱</p>
                          <p>Enter details and click "Get Quote" to see pricing</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Reference Tables */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Segments Table */}
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">📊 Customer Segments</h3>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs text-gray-500 uppercase">
                          <th className="pb-3">Segment</th>
                          <th>Base</th>
                          <th>Range</th>
                          <th>Vol. Disc.</th>
                        </tr>
                      </thead>
                      <tbody>
                        {segments.map(s => (
                          <tr key={s.segment_id} className="border-t">
                            <td className="py-2 font-medium">{s.segment_name}</td>
                            <td>{s.base_margin_bps} bps</td>
                            <td>{s.min_margin_bps}-{s.max_margin_bps} bps</td>
                            <td>{s.volume_discount_eligible ? '✅' : '❌'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Tiers Table */}
                  <div className="bg-white rounded-xl shadow p-6">
                    <h3 className="font-semibold mb-4">📈 Amount Tiers</h3>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs text-gray-500 uppercase">
                          <th className="pb-3">Tier</th>
                          <th>Amount Range</th>
                          <th>Adjustment</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tiers.map(t => (
                          <tr key={t.tier_id} className="border-t">
                            <td className="py-2 font-medium">{t.tier_id}</td>
                            <td>${t.min_amount?.toLocaleString()} - {t.max_amount ? '$' + t.max_amount.toLocaleString() : '∞'}</td>
                            <td className={t.adjustment_bps < 0 ? 'text-green-600' : t.adjustment_bps > 0 ? 'text-red-600' : ''}>
                              {t.adjustment_bps > 0 ? '+' : ''}{t.adjustment_bps} bps
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Currency Categories */}
                <div className="bg-white rounded-xl shadow p-6">
                  <h3 className="font-semibold mb-4">🌍 Currency Categories</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-2">G10 (Most Liquid)</h4>
                      <p className="text-sm text-green-600 mb-2">USD, EUR, JPY, GBP, CHF, AUD, NZD, CAD</p>
                      <p className="text-xs text-green-700">Retail: 50 bps | Corp: 15 bps | Inst: 2 bps</p>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-2">Minor</h4>
                      <p className="text-sm text-blue-600 mb-2">SGD, HKD, DKK, PLN, CZK</p>
                      <p className="text-xs text-blue-700">Retail: 100 bps | Corp: 30 bps | Inst: 5 bps</p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h4 className="font-medium text-yellow-800 mb-2">Exotic</h4>
                      <p className="text-sm text-yellow-600 mb-2">TRY, ZAR, MXN, BRL</p>
                      <p className="text-xs text-yellow-700">Retail: 200 bps | Corp: 75 bps | Inst: 15 bps</p>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <h4 className="font-medium text-red-800 mb-2">Restricted</h4>
                      <p className="text-sm text-red-600 mb-2">INR, CNY, KRW, TWD, PHP</p>
                      <p className="text-xs text-red-700">Retail: 300 bps | Corp: 100 bps | Inst: 25 bps</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Chat Button */}
      <button onClick={() => setChatOpen(!chatOpen)} className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center text-2xl z-50 hover:bg-blue-700">
        💬
      </button>

      {/* Chat Panel */}
      {chatOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-xl shadow-2xl flex flex-col z-50 border">
          <div className="bg-blue-600 text-white p-4 rounded-t-xl flex justify-between items-center">
            <span className="font-medium">💬 FX Assistant</span>
            <button onClick={() => setChatOpen(false)} className="text-xl hover:bg-blue-700 rounded px-2">×</button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] px-4 py-2 rounded-xl text-sm ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
                  {m.content}
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t flex gap-2">
            <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()}
              placeholder="Ask about rates, deals..." className="flex-1 border rounded-full px-4 py-2 text-sm" />
            <button onClick={sendChat} className="px-4 py-2 bg-blue-600 text-white rounded-full text-sm hover:bg-blue-700">Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
