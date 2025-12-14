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

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dealsRes, ratesRes, cbdcRes, stableRes] = await Promise.all([
        api.getDeals({}).catch(() => ({ data: { deals: [] } })),
        api.getTreasuryRates().catch(() => ({ data: { rates: {} } })),
        api.getCBDCs().catch(() => ({ data: { cbdc: [] } })),
        api.getStablecoins().catch(() => ({ data: { stablecoins: [] } })),
      ]);
      
      setDeals(dealsRes.data?.deals || []);
      setRates(ratesRes.data?.rates || {});
      setCbdcs(cbdcRes.data?.cbdc || []);
      setStablecoins(stableRes.data?.stablecoins || []);
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
            {['dashboard', 'deals', 'rates'].map(t => (
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
                    <p className="text-sm opacity-80">CBDCs</p>
                    <p className="text-3xl font-bold">{cbdcs.length}</p>
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
