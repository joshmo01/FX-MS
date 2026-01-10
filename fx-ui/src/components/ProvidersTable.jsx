import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, RefreshCw, Save, X } from 'lucide-react';
import { getAdminResource, createAdminResource, updateAdminResource, deleteAdminResource, reloadAdminResource } from '../services/api';

const ProvidersTable = ({ onUpdate }) => {
  const [providers, setProviders] = useState([]);
  const [filteredProviders, setFilteredProviders] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [notification, setNotification] = useState(null);

  const providerTypes = ['MARKET_DATA', 'INTERNAL', 'CORRESPONDENT', 'DOMESTIC', 'FINTECH'];

  useEffect(() => {
    fetchProviders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = providers.filter(p =>
        p.provider_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredProviders(filtered);
    } else {
      setFilteredProviders(providers);
    }
  }, [searchTerm, providers]);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const response = await getAdminResource('fx-providers');
      setProviders(response.data.data || []);
      if (onUpdate) onUpdate();
    } catch (_error) {
      showNotification('Failed to load providers', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingProvider({
      provider_id: '',
      name: '',
      type: 'DOMESTIC',
      reliability_score: 0.95,
      avg_latency_ms: 100,
      markup_bps: 10,
      supported_pairs: [],
      operating_hours: '24x7',
      _isNew: true,  // Track if this is a new provider
      _supportedPairsString: ''  // String field for editing supported pairs
    });
    setIsModalOpen(true);
  };

  const handleEdit = (provider) => {
    setEditingProvider({
      ...provider,
      _isNew: false,
      _supportedPairsString: (provider.supported_pairs || []).join(', ')  // Convert array to string for editing
    });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      if (!editingProvider.provider_id || !editingProvider.name) {
        showNotification('Provider ID and Name are required', 'error');
        return;
      }

      const isNew = !providers.find(p => p.provider_id === editingProvider.provider_id);

      // Convert supported pairs string back to array before saving
      const providerData = {
        ...editingProvider,
        supported_pairs: editingProvider._supportedPairsString
          ? editingProvider._supportedPairsString.split(',').map(s => s.trim()).filter(Boolean)
          : []
      };
      delete providerData._supportedPairsString;  // Remove temp field
      delete providerData._isNew;  // Remove temp field

      if (isNew) {
        await createAdminResource('fx-providers', providerData);
        showNotification('Provider created successfully', 'success');
      } else {
        await updateAdminResource('fx-providers', editingProvider.provider_id, providerData);
        showNotification('Provider updated successfully', 'success');
      }

      setIsModalOpen(false);
      setEditingProvider(null);
      fetchProviders();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to save provider', 'error');
    }
  };

  const handleDelete = async (provider) => {
    if (!window.confirm(`Are you sure you want to delete ${provider.provider_id}?`)) {
      return;
    }

    try {
      await deleteAdminResource('fx-providers', provider.provider_id);
      showNotification('Provider deleted successfully', 'success');
      fetchProviders();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to delete provider', 'error');
    }
  };

  const handleReload = async () => {
    try {
      await reloadAdminResource('fx-providers');
      showNotification('Configuration reloaded successfully', 'success');
    } catch (_error) {
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
          <h2 className="text-2xl font-bold text-gray-900">FX Providers</h2>
          <p className="text-gray-600 mt-1">Manage FX provider configurations and capabilities</p>
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
            Add Provider
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search providers..."
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reliability</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latency</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Markup</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredProviders.map((provider) => (
                  <tr key={provider.provider_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{provider.provider_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{provider.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">{provider.type}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{(provider.reliability_score * 100).toFixed(0)}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{provider.avg_latency_ms}ms</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-700">{provider.markup_bps} bps</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(provider)} className="text-blue-600 hover:text-blue-800">
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button onClick={() => handleDelete(provider)} className="text-red-600 hover:text-red-800">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredProviders.length === 0 && (
            <div className="text-center py-12 text-gray-500">No providers found</div>
          )}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && editingProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">
                {providers.find(p => p.provider_id === editingProvider.provider_id) ? 'Edit' : 'Create'} Provider
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Provider ID *</label>
                  <input
                    type="text"
                    value={editingProvider.provider_id}
                    onChange={(e) => setEditingProvider({ ...editingProvider, provider_id: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={!editingProvider._isNew}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={editingProvider.name}
                    onChange={(e) => setEditingProvider({ ...editingProvider, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={editingProvider.type}
                    onChange={(e) => setEditingProvider({ ...editingProvider, type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {providerTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reliability Score (0-1)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={editingProvider.reliability_score}
                    onChange={(e) => setEditingProvider({ ...editingProvider, reliability_score: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Avg Latency (ms)</label>
                  <input
                    type="number"
                    value={editingProvider.avg_latency_ms}
                    onChange={(e) => setEditingProvider({ ...editingProvider, avg_latency_ms: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Markup (bps)</label>
                  <input
                    type="number"
                    value={editingProvider.markup_bps}
                    onChange={(e) => setEditingProvider({ ...editingProvider, markup_bps: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supported Pairs (comma-separated)</label>
                <input
                  type="text"
                  value={editingProvider._supportedPairsString || ''}
                  onChange={(e) => setEditingProvider({ ...editingProvider, _supportedPairsString: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="USDINR, EURUSD, GBPUSD"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Operating Hours</label>
                <input
                  type="text"
                  value={editingProvider.operating_hours}
                  onChange={(e) => setEditingProvider({ ...editingProvider, operating_hours: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="24x7 or 9x5_IST"
                />
              </div>
            </div>

            <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
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
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
          notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default ProvidersTable;
