import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, RefreshCw, Save, X } from 'lucide-react';
import { getAdminResource, createAdminResource, updateAdminResource, deleteAdminResource, reloadAdminResource } from '../services/api';

const CustomerTiersTable = ({ onUpdate }) => {
  const [tiers, setTiers] = useState([]);
  const [filteredTiers, setFilteredTiers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTier, setEditingTier] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchTiers();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = tiers.filter(tier =>
        tier.tier_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tier.name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredTiers(filtered);
    } else {
      setFilteredTiers(tiers);
    }
  }, [searchTerm, tiers]);

  const fetchTiers = async () => {
    setLoading(true);
    try {
      const response = await getAdminResource('customer-tiers');
      setTiers(response.data.data || []);
      if (onUpdate) onUpdate();
    } catch (error) {
      showNotification('Failed to load customer tiers', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTier({
      tier_id: '',
      name: '',
      min_annual_volume_usd: 0,
      markup_discount_pct: 0,
      spread_reduction_bps: 0,
      priority_routing: false,
      dedicated_treasury: false,
      max_transaction_usd: 1000000,
      stp_threshold_usd: 100000
    });
    setIsModalOpen(true);
  };

  const handleEdit = (tier) => {
    setEditingTier({ ...tier });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      if (!editingTier.tier_id || !editingTier.name) {
        showNotification('Tier ID and Name are required', 'error');
        return;
      }

      const isNew = !tiers.find(t => t.tier_id === editingTier.tier_id);

      if (isNew) {
        await createAdminResource('customer-tiers', editingTier);
        showNotification('Customer tier created successfully', 'success');
      } else {
        await updateAdminResource('customer-tiers', editingTier.tier_id, editingTier);
        showNotification('Customer tier updated successfully', 'success');
      }

      setIsModalOpen(false);
      setEditingTier(null);
      fetchTiers();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to save tier', 'error');
    }
  };

  const handleDelete = async (tier) => {
    if (!window.confirm(`Are you sure you want to delete ${tier.tier_id}?`)) {
      return;
    }

    try {
      await deleteAdminResource('customer-tiers', tier.tier_id);
      showNotification('Customer tier deleted successfully', 'success');
      fetchTiers();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to delete tier', 'error');
    }
  };

  const handleReload = async () => {
    try {
      await reloadAdminResource('customer-tiers');
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
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Customer Tiers</h2>
          <p className="text-gray-600 mt-1">Manage customer tier definitions and pricing benefits</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReload}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Tier
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search tiers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tier ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min Volume</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Discount %</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Spread Reduction</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTiers.map((tier) => (
                  <tr key={tier.tier_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-gray-900">{tier.tier_id}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{tier.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">
                      ${(tier.min_annual_volume_usd || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{tier.markup_discount_pct}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{tier.spread_reduction_bps} bps</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        tier.priority_routing ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {tier.priority_routing ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(tier)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(tier)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredTiers.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No customer tiers found
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && editingTier && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">
                {tiers.find(t => t.tier_id === editingTier.tier_id) ? 'Edit' : 'Create'} Customer Tier
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tier ID *</label>
                  <input
                    type="text"
                    value={editingTier.tier_id}
                    onChange={(e) => setEditingTier({ ...editingTier, tier_id: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="PLATINUM"
                    disabled={tiers.find(t => t.tier_id === editingTier.tier_id)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={editingTier.name}
                    onChange={(e) => setEditingTier({ ...editingTier, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Platinum"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Min Annual Volume (USD)</label>
                  <input
                    type="number"
                    value={editingTier.min_annual_volume_usd}
                    onChange={(e) => setEditingTier({ ...editingTier, min_annual_volume_usd: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Markup Discount %</label>
                  <input
                    type="number"
                    value={editingTier.markup_discount_pct}
                    onChange={(e) => setEditingTier({ ...editingTier, markup_discount_pct: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    min="0"
                    max="100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spread Reduction (bps)</label>
                  <input
                    type="number"
                    value={editingTier.spread_reduction_bps}
                    onChange={(e) => setEditingTier({ ...editingTier, spread_reduction_bps: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Transaction (USD)</label>
                  <input
                    type="number"
                    value={editingTier.max_transaction_usd}
                    onChange={(e) => setEditingTier({ ...editingTier, max_transaction_usd: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">STP Threshold (USD)</label>
                <input
                  type="number"
                  value={editingTier.stp_threshold_usd}
                  onChange={(e) => setEditingTier({ ...editingTier, stp_threshold_usd: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={editingTier.priority_routing}
                    onChange={(e) => setEditingTier({ ...editingTier, priority_routing: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Priority Routing</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={editingTier.dedicated_treasury}
                    onChange={(e) => setEditingTier({ ...editingTier, dedicated_treasury: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Dedicated Treasury</span>
                </label>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Save className="h-4 w-4" />
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50 ${
          notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default CustomerTiersTable;
