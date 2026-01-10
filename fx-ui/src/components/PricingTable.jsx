import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, RefreshCw, Save, X } from 'lucide-react';
import { getAdminResource, createAdminResource, updateAdminResource, deleteAdminResource, reloadAdminResource } from '../services/api';

const PricingTable = ({ onUpdate }) => {
  const [activeSubTab, setActiveSubTab] = useState('segments');
  const [segments, setSegments] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [segResp, tierResp] = await Promise.all([
        getAdminResource('pricing-segments'),
        getAdminResource('pricing-tiers')
      ]);
      setSegments(segResp.data.data || []);
      setTiers(tierResp.data.data || []);
      if (onUpdate) onUpdate();
    } catch (_error) {
      showNotification('Failed to load pricing config', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentResource = () => activeSubTab === 'segments' ? 'pricing-segments' : 'pricing-tiers';
  const getCurrentData = () => activeSubTab === 'segments' ? segments : tiers;

  const handleCreate = () => {
    if (activeSubTab === 'segments') {
      setEditingItem({
        segment_id: '',
        base_margin_bps: 50,
        min_margin_bps: 20,
        max_margin_bps: 100,
        volume_discount_eligible: true,
        negotiated_rates_allowed: false,
        _isNew: true  // Track if this is a new segment
      });
    } else {
      setEditingItem({
        tier_id: '',
        min_amount: 0,
        max_amount: null,
        adjustment_bps: 0,
        description: '',
        _isNew: true  // Track if this is a new tier
      });
    }
    setIsModalOpen(true);
  };

  const handleEdit = (item) => {
    setEditingItem({ ...item, _isNew: false });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const resource = getCurrentResource();
      const idField = activeSubTab === 'segments' ? 'segment_id' : 'tier_id';
      const itemId = editingItem[idField];

      if (!itemId) {
        showNotification('ID is required', 'error');
        return;
      }

      const currentData = getCurrentData();
      const isNew = !currentData.find(item => item[idField] === itemId);

      // Remove temporary fields before saving
      const itemData = { ...editingItem };
      delete itemData._isNew;

      if (isNew) {
        await createAdminResource(resource, itemData);
        showNotification(`${activeSubTab === 'segments' ? 'Segment' : 'Tier'} created successfully`, 'success');
      } else {
        await updateAdminResource(resource, itemId, itemData);
        showNotification(`${activeSubTab === 'segments' ? 'Segment' : 'Tier'} updated successfully`, 'success');
      }

      setIsModalOpen(false);
      setEditingItem(null);
      fetchAll();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to save', 'error');
    }
  };

  const handleDelete = async (item) => {
    const idField = activeSubTab === 'segments' ? 'segment_id' : 'tier_id';
    const itemId = item[idField];

    if (!window.confirm(`Are you sure you want to delete ${itemId}?`)) {
      return;
    }

    try {
      await deleteAdminResource(getCurrentResource(), itemId);
      showNotification('Deleted successfully', 'success');
      fetchAll();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to delete', 'error');
    }
  };

  const handleReload = async () => {
    try {
      await Promise.all([
        reloadAdminResource('pricing-segments'),
        reloadAdminResource('pricing-tiers')
      ]);
      showNotification('Configuration reloaded successfully', 'success');
    } catch (_error) {
      showNotification('Failed to reload configuration', 'error');
    }
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const filteredData = getCurrentData().filter(item => {
    if (!searchTerm) return true;
    const searchFields = activeSubTab === 'segments' ? [item.segment_id] : [item.tier_id, item.description];
    return searchFields.some(field => field?.toLowerCase().includes(searchTerm.toLowerCase()));
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Pricing Configuration</h2>
          <p className="text-gray-600 mt-1">Manage pricing segments and amount-based tiers</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReload} className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg">
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
          <button onClick={handleCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
            <Plus className="h-4 w-4" />
            Add {activeSubTab === 'segments' ? 'Segment' : 'Tier'}
          </button>
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="mb-4 border-b">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveSubTab('segments')}
            className={`px-4 py-2 font-medium border-b-2 ${activeSubTab === 'segments' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-800'}`}
          >
            Segments ({segments.length})
          </button>
          <button
            onClick={() => setActiveSubTab('tiers')}
            className={`px-4 py-2 font-medium border-b-2 ${activeSubTab === 'tiers' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-800'}`}
          >
            Tiers ({tiers.length})
          </button>
        </nav>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder={`Search ${activeSubTab}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
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
                {activeSubTab === 'segments' ? (
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Segment ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base Margin</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Volume Discount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                ) : (
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Adjustment</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                )}
              </thead>
              <tbody className="divide-y">
                {filteredData.map((item) => (
                  <tr key={activeSubTab === 'segments' ? item.segment_id : item.tier_id} className="hover:bg-gray-50">
                    {activeSubTab === 'segments' ? (
                      <>
                        <td className="px-6 py-4 font-medium text-gray-900">{item.segment_id}</td>
                        <td className="px-6 py-4 text-gray-700">{item.base_margin_bps} bps</td>
                        <td className="px-6 py-4 text-gray-700">{item.min_margin_bps} bps</td>
                        <td className="px-6 py-4 text-gray-700">{item.max_margin_bps} bps</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs ${item.volume_discount_eligible ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {item.volume_discount_eligible ? 'Yes' : 'No'}
                          </span>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-6 py-4 font-medium text-gray-900">{item.tier_id}</td>
                        <td className="px-6 py-4 text-gray-700">${(item.min_amount || 0).toLocaleString()}</td>
                        <td className="px-6 py-4 text-gray-700">{item.max_amount ? `$${item.max_amount.toLocaleString()}` : 'Unlimited'}</td>
                        <td className="px-6 py-4 text-gray-700">{item.adjustment_bps} bps</td>
                        <td className="px-6 py-4 text-gray-700">{item.description}</td>
                      </>
                    )}
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(item)} className="text-blue-600 hover:text-blue-800"><Edit2 className="h-4 w-4" /></button>
                        <button onClick={() => handleDelete(item)} className="text-red-600 hover:text-red-800"><Trash2 className="h-4 w-4" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredData.length === 0 && <div className="text-center py-12 text-gray-500">No {activeSubTab} found</div>}
        </div>
      )}

      {isModalOpen && editingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-xl font-bold">{activeSubTab === 'segments' ? 'Segment' : 'Tier'}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="h-6 w-6" /></button>
            </div>

            <div className="p-6 space-y-4">
              {activeSubTab === 'segments' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Segment ID *</label>
                    <input
                      type="text"
                      value={editingItem.segment_id}
                      onChange={(e) => setEditingItem({ ...editingItem, segment_id: e.target.value.toUpperCase() })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      disabled={!editingItem._isNew}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Base Margin (bps)</label>
                      <input
                        type="number"
                        value={editingItem.base_margin_bps}
                        onChange={(e) => setEditingItem({ ...editingItem, base_margin_bps: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Min Margin (bps)</label>
                      <input
                        type="number"
                        value={editingItem.min_margin_bps}
                        onChange={(e) => setEditingItem({ ...editingItem, min_margin_bps: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Max Margin (bps)</label>
                      <input
                        type="number"
                        value={editingItem.max_margin_bps}
                        onChange={(e) => setEditingItem({ ...editingItem, max_margin_bps: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex gap-6">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={editingItem.volume_discount_eligible}
                        onChange={(e) => setEditingItem({ ...editingItem, volume_discount_eligible: e.target.checked })}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm">Volume Discount Eligible</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={editingItem.negotiated_rates_allowed}
                        onChange={(e) => setEditingItem({ ...editingItem, negotiated_rates_allowed: e.target.checked })}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm">Negotiated Rates Allowed</span>
                    </label>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tier ID *</label>
                    <input
                      type="text"
                      value={editingItem.tier_id}
                      onChange={(e) => setEditingItem({ ...editingItem, tier_id: e.target.value.toUpperCase() })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      disabled={!editingItem._isNew}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Min Amount</label>
                      <input
                        type="number"
                        value={editingItem.min_amount}
                        onChange={(e) => setEditingItem({ ...editingItem, min_amount: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount (null = unlimited)</label>
                      <input
                        type="number"
                        value={editingItem.max_amount || ''}
                        onChange={(e) => setEditingItem({ ...editingItem, max_amount: e.target.value ? parseFloat(e.target.value) : null })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Adjustment (bps)</label>
                      <input
                        type="number"
                        value={editingItem.adjustment_bps}
                        onChange={(e) => setEditingItem({ ...editingItem, adjustment_bps: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <input
                      type="text"
                      value={editingItem.description}
                      onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              )}
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

export default PricingTable;
