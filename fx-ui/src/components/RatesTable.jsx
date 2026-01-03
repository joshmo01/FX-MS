import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, RefreshCw, Save, X } from 'lucide-react';
import { getAdminResource, createAdminResource, updateAdminResource, deleteAdminResource, reloadAdminResource } from '../services/api';

const RatesTable = ({ onUpdate }) => {
  const [rates, setRates] = useState([]);
  const [filteredRates, setFilteredRates] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRate, setEditingRate] = useState(null);
  const [notification, setNotification] = useState(null);

  const positions = ['LONG', 'SHORT', 'NEUTRAL'];

  useEffect(() => {
    fetchRates();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = rates.filter(r =>
        r.pair?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredRates(filtered);
    } else {
      setFilteredRates(rates);
    }
  }, [searchTerm, rates]);

  const fetchRates = async () => {
    setLoading(true);
    try {
      const response = await getAdminResource('treasury-rates');
      setRates(response.data.data || []);
      if (onUpdate) onUpdate();
    } catch (error) {
      showNotification('Failed to load rates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingRate({
      pair: '',
      bid: 0,
      ask: 0,
      mid: 0,
      min_margin_bps: 10,
      position: 'NEUTRAL',
      _isNew: true  // Track if this is a new rate
    });
    setIsModalOpen(true);
  };

  const handleEdit = (rate) => {
    setEditingRate({ ...rate, _isNew: false });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      if (!editingRate.pair) {
        showNotification('Currency pair is required', 'error');
        return;
      }

      // Remove temporary fields and calculate mid
      const rateData = { ...editingRate };
      delete rateData._isNew;
      rateData.mid = (rateData.bid + rateData.ask) / 2;

      const isNew = !rates.find(r => r.pair === editingRate.pair);

      if (isNew) {
        await createAdminResource('treasury-rates', rateData);
        showNotification('Rate created successfully', 'success');
      } else {
        await updateAdminResource('treasury-rates', editingRate.pair, rateData);
        showNotification('Rate updated successfully', 'success');
      }

      setIsModalOpen(false);
      setEditingRate(null);
      fetchRates();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to save rate', 'error');
    }
  };

  const handleDelete = async (rate) => {
    if (!window.confirm(`Are you sure you want to delete ${rate.pair}?`)) {
      return;
    }

    try {
      await deleteAdminResource('treasury-rates', rate.pair);
      showNotification('Rate deleted successfully', 'success');
      fetchRates();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to delete rate', 'error');
    }
  };

  const handleReload = async () => {
    try {
      await reloadAdminResource('treasury-rates');
      showNotification('Configuration reloaded successfully', 'success');
    } catch (error) {
      showNotification('Failed to reload configuration', 'error');
    }
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Treasury Rates</h2>
          <p className="text-gray-600 mt-1">Manage treasury rate configurations for currency pairs</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReload} className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg">
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
          <button onClick={handleCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
            <Plus className="h-4 w-4" />
            Add Rate
          </button>
        </div>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search currency pairs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pair</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bid</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ask</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mid</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min Margin</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredRates.map((rate) => (
                  <tr key={rate.pair} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{rate.pair}</td>
                    <td className="px-6 py-4 text-gray-700">{rate.bid?.toFixed(4)}</td>
                    <td className="px-6 py-4 text-gray-700">{rate.ask?.toFixed(4)}</td>
                    <td className="px-6 py-4 text-gray-700">{rate.mid?.toFixed(4)}</td>
                    <td className="px-6 py-4 text-gray-700">{rate.min_margin_bps} bps</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        rate.position === 'LONG' ? 'bg-green-100 text-green-800' :
                        rate.position === 'SHORT' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>{rate.position}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(rate)} className="text-blue-600 hover:text-blue-800">
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button onClick={() => handleDelete(rate)} className="text-red-600 hover:text-red-800">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredRates.length === 0 && <div className="text-center py-12 text-gray-500">No rates found</div>}
        </div>
      )}

      {isModalOpen && editingRate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-xl font-bold">{rates.find(r => r.pair === editingRate.pair) ? 'Edit' : 'Create'} Rate</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency Pair * (6 letters)</label>
                <input
                  type="text"
                  maxLength={6}
                  value={editingRate.pair}
                  onChange={(e) => setEditingRate({ ...editingRate, pair: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="USDINR"
                  disabled={!editingRate._isNew}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bid</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={editingRate.bid}
                    onChange={(e) => setEditingRate({ ...editingRate, bid: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ask</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={editingRate.ask}
                    onChange={(e) => setEditingRate({ ...editingRate, ask: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mid (auto)</label>
                  <input
                    type="number"
                    value={((editingRate.bid + editingRate.ask) / 2).toFixed(4)}
                    className="w-full px-3 py-2 border rounded-lg bg-gray-50"
                    disabled
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Min Margin (bps)</label>
                  <input
                    type="number"
                    value={editingRate.min_margin_bps}
                    onChange={(e) => setEditingRate({ ...editingRate, min_margin_bps: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                  <select
                    value={editingRate.position}
                    onChange={(e) => setEditingRate({ ...editingRate, position: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {positions.map(pos => <option key={pos} value={pos}>{pos}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-100">Cancel</button>
              <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Save className="h-4 w-4" />
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default RatesTable;
