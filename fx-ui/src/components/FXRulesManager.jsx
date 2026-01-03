import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Download, Upload, Save, X, ChevronDown, ChevronUp, Copy, FileJson, AlertCircle, Check, RefreshCw } from 'lucide-react';

const OPERATORS = [
  'EQUALS', 'NOT_EQUALS', 'IN', 'NOT_IN', 'GREATER_THAN', 'GREATER_THAN_OR_EQUAL',
  'LESS_THAN', 'LESS_THAN_OR_EQUAL', 'BETWEEN', 'CONTAINS', 'STARTS_WITH', 'ENDS_WITH', 'OUTSIDE_HOURS'
];

const FIELDS = [
  'customer_segment', 'customer_tier', 'currency_pair', 'currency_category',
  'amount', 'amount_tier', 'office', 'time_of_day'
];

const PROVIDERS = [
  'TREASURY_INTERNAL', 'HDFC_BANK', 'ICICI_BANK', 'REFINITIV',
  'BANK_OF_AMERICA', 'CITI', 'WISE'
];

const ROUTING_OBJECTIVES = ['BEST_RATE', 'FASTEST_EXECUTION', 'OPTIMUM', 'LOWEST_COST'];

const API_BASE = `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/fx/rules`;

export default function FXRulesManager() {
  const [rules, setRules] = useState([]);
  const [editingRule, setEditingRule] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedRule, setExpandedRule] = useState(null);
  const [notification, setNotification] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [jsonPreview, setJsonPreview] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/`);
      if (response.ok) {
        const data = await response.json();
        setRules(Array.isArray(data) ? data : []);
      } else {
        showNotification('Failed to load rules', 'error');
      }
    } catch (error) {
      showNotification('Error connecting to API', 'error');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const generateRuleId = (type) => {
    const prefix = type === 'PROVIDER_SELECTION' ? 'PROV' : 'PRICE';
    const existingIds = rules.filter(r => r.rule_id.startsWith(prefix)).map(r => parseInt(r.rule_id.split('-')[1]));
    const nextNum = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
    return `${prefix}-${String(nextNum).padStart(3, '0')}`;
  };

  const createEmptyRule = () => ({
    rule_id: '',
    rule_name: '',
    rule_type: 'PROVIDER_SELECTION',
    priority: 50,
    enabled: true,
    valid_from: new Date().toISOString().split('T')[0] + 'T00:00:00',
    valid_until: null,
    conditions: { operator: 'AND', criteria: [] },
    actions: {
      provider_selection: {
        preferred_providers: [],
        excluded_providers: [],
        routing_objective_override: null,
        force_provider: false
      },
      margin_adjustment: null
    },
    metadata: {
      created_by: 'user',
      created_at: new Date().toISOString(),
      updated_at: null,
      description: '',
      tags: []
    }
  });

  const handleNewRule = () => {
    const newRule = createEmptyRule();
    newRule.rule_id = generateRuleId(newRule.rule_type);
    setEditingRule(newRule);
    setIsModalOpen(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule(JSON.parse(JSON.stringify(rule)));
    setIsModalOpen(true);
  };

  const handleDeleteRule = async (ruleId) => {
    if (!confirm(`Delete rule ${ruleId}?`)) return;

    try {
      const response = await fetch(`${API_BASE}/${ruleId}`, { method: 'DELETE' });
      if (response.ok) {
        await fetchRules();
        showNotification(`Rule ${ruleId} deleted`);
      } else {
        showNotification('Failed to delete rule', 'error');
      }
    } catch (error) {
      showNotification('Error deleting rule', 'error');
    }
  };

  const handleToggleRule = async (ruleId) => {
    try {
      const response = await fetch(`${API_BASE}/${ruleId}/toggle`, { method: 'POST' });
      if (response.ok) {
        await fetchRules();
        showNotification(`Rule ${ruleId} toggled`);
      } else {
        showNotification('Failed to toggle rule', 'error');
      }
    } catch (error) {
      showNotification('Error toggling rule', 'error');
    }
  };

  const handleSaveRule = async () => {
    if (!editingRule.rule_name.trim()) {
      showNotification('Rule name is required', 'error');
      return;
    }

    try {
      const existingRule = rules.find(r => r.rule_id === editingRule.rule_id);
      const method = existingRule ? 'PUT' : 'POST';
      const url = existingRule ? `${API_BASE}/${editingRule.rule_id}` : `${API_BASE}/`;

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingRule)
      });

      if (response.ok) {
        await fetchRules();
        showNotification(`Rule ${editingRule.rule_id} ${existingRule ? 'updated' : 'created'}`);
        setIsModalOpen(false);
        setEditingRule(null);
      } else {
        showNotification('Failed to save rule', 'error');
      }
    } catch (error) {
      showNotification('Error saving rule', 'error');
    }
  };

  const handleExportJSON = () => {
    const json = JSON.stringify(rules, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fx_rules.json';
    a.click();
    URL.revokeObjectURL(url);
    showNotification('JSON exported successfully');
  };

  const handleImportJSON = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          if (Array.isArray(imported)) {
            // Import rules by creating them via API
            for (const rule of imported) {
              await fetch(`${API_BASE}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rule)
              });
            }
            await fetchRules();
            showNotification(`Imported ${imported.length} rules`);
          } else {
            showNotification('Invalid JSON format', 'error');
          }
        } catch (err) {
          showNotification('Failed to parse JSON', 'error');
        }
      };
      reader.readAsText(file);
    }
  };

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(rules, null, 2));
    showNotification('JSON copied to clipboard');
  };

  const updateEditingRule = (path, value) => {
    const updated = { ...editingRule };
    const keys = path.split('.');
    let obj = updated;
    for (let i = 0; i < keys.length - 1; i++) {
      obj = obj[keys[i]];
    }
    obj[keys[keys.length - 1]] = value;

    if (path === 'rule_type') {
      if (value === 'PROVIDER_SELECTION') {
        updated.actions = {
          provider_selection: {
            preferred_providers: [],
            excluded_providers: [],
            routing_objective_override: null,
            force_provider: false
          },
          margin_adjustment: null
        };
      } else {
        updated.actions = {
          provider_selection: null,
          margin_adjustment: {
            base_margin_override: null,
            additional_margin_bps: 0,
            tier_adjustment_multiplier: 1,
            min_margin_bps: null,
            max_margin_bps: null
          }
        };
      }
      updated.rule_id = generateRuleId(value);
    }

    setEditingRule(updated);
  };

  const addCondition = () => {
    const updated = { ...editingRule };
    updated.conditions.criteria.push({
      field: 'customer_segment',
      operator: 'EQUALS',
      value: '',
      values: null
    });
    setEditingRule(updated);
  };

  const removeCondition = (index) => {
    const updated = { ...editingRule };
    updated.conditions.criteria.splice(index, 1);
    setEditingRule(updated);
  };

  const updateCondition = (index, field, value) => {
    const updated = { ...editingRule };
    updated.conditions.criteria[index][field] = value;

    if (field === 'operator') {
      if (['IN', 'NOT_IN', 'BETWEEN'].includes(value)) {
        updated.conditions.criteria[index].value = null;
        updated.conditions.criteria[index].values = [];
      } else {
        updated.conditions.criteria[index].values = null;
        updated.conditions.criteria[index].value = '';
      }
    }
    setEditingRule(updated);
  };

  const filteredRules = rules
    .filter(r => filterType === 'ALL' || r.rule_type === filterType)
    .filter(r =>
      r.rule_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.metadata?.description || '').toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => b.priority - a.priority);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading rules...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">FX Rules Manager</h1>
            <p className="text-gray-500 text-sm">Manage routing and pricing rules</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={fetchRules} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              <RefreshCw size={18} />
              <span className="text-sm">Reload</span>
            </button>
            <label className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer hover:bg-gray-200">
              <Upload size={18} />
              <span className="text-sm">Import</span>
              <input type="file" accept=".json" onChange={handleImportJSON} className="hidden" />
            </label>
            <button onClick={handleExportJSON} className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Download size={18} />
              <span className="text-sm">Export JSON</span>
            </button>
            <button onClick={handleCopyJSON} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              <Copy size={18} />
              <span className="text-sm">Copy</span>
            </button>
            <button onClick={() => setJsonPreview(!jsonPreview)} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
              <FileJson size={18} />
              <span className="text-sm">{jsonPreview ? 'Hide' : 'Preview'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50 ${
          notification.type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
        }`}>
          {notification.type === 'error' ? <AlertCircle size={18} /> : <Check size={18} />}
          {notification.message}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-blue-600">{rules.length}</div>
          <div className="text-gray-500 text-sm">Total Rules</div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-green-600">{rules.filter(r => r.rule_type === 'PROVIDER_SELECTION').length}</div>
          <div className="text-gray-500 text-sm">Provider Rules</div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-purple-600">{rules.filter(r => r.rule_type === 'MARGIN_ADJUSTMENT').length}</div>
          <div className="text-gray-500 text-sm">Pricing Rules</div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-orange-600">{rules.filter(r => r.enabled).length}</div>
          <div className="text-gray-500 text-sm">Active Rules</div>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
        <div className="flex flex-wrap items-center gap-4">
          <input
            type="text"
            placeholder="Search rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 min-w-48 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Types</option>
            <option value="PROVIDER_SELECTION">Provider Selection</option>
            <option value="MARGIN_ADJUSTMENT">Margin Adjustment</option>
          </select>
          <button
            onClick={handleNewRule}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Plus size={18} />
            New Rule
          </button>
        </div>
      </div>

      {/* JSON Preview */}
      {jsonPreview && (
        <div className="bg-gray-900 rounded-lg shadow-sm p-4 mb-4 max-h-64 overflow-auto">
          <pre className="text-green-400 text-xs font-mono">{JSON.stringify(rules, null, 2)}</pre>
        </div>
      )}

      {/* Rules List */}
      <div className="space-y-3">
        {filteredRules.map((rule) => (
          <div key={rule.rule_id} className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div
              className="p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedRule(expandedRule === rule.rule_id ? null : rule.rule_id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-2 h-12 rounded ${rule.enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm bg-gray-100 px-2 py-0.5 rounded">{rule.rule_id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        rule.rule_type === 'PROVIDER_SELECTION' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                      }`}>
                        {rule.rule_type === 'PROVIDER_SELECTION' ? 'Provider' : 'Pricing'}
                      </span>
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                        Priority: {rule.priority}
                      </span>
                    </div>
                    <div className="font-medium text-gray-800 mt-1">{rule.rule_name}</div>
                    <div className="text-sm text-gray-500">{rule.metadata?.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleToggleRule(rule.rule_id); }}
                    className={`px-3 py-1 rounded text-sm ${rule.enabled ? 'bg-gray-100 hover:bg-gray-200' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleEditRule(rule); }}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteRule(rule.rule_id); }}
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 size={18} />
                  </button>
                  {expandedRule === rule.rule_id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
              </div>
            </div>

            {expandedRule === rule.rule_id && (
              <div className="border-t bg-gray-50 p-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">Conditions</h4>
                    <div className="space-y-1">
                      {(rule.conditions?.criteria || []).map((cond, idx) => (
                        <div key={idx} className="text-sm bg-white p-2 rounded border">
                          <span className="font-mono text-blue-600">{cond.field}</span>
                          <span className="text-gray-500 mx-2">{cond.operator}</span>
                          <span className="text-green-600">{cond.value || (cond.values && cond.values.join(', '))}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">Actions</h4>
                    {rule.actions?.provider_selection && (
                      <div className="text-sm bg-white p-2 rounded border">
                        <div><strong>Preferred:</strong> {(rule.actions.provider_selection.preferred_providers || []).join(', ')}</div>
                        {(rule.actions.provider_selection.excluded_providers || []).length > 0 && (
                          <div><strong>Excluded:</strong> {rule.actions.provider_selection.excluded_providers.join(', ')}</div>
                        )}
                        {rule.actions.provider_selection.routing_objective_override && (
                          <div><strong>Objective:</strong> {rule.actions.provider_selection.routing_objective_override}</div>
                        )}
                      </div>
                    )}
                    {rule.actions?.margin_adjustment && (
                      <div className="text-sm bg-white p-2 rounded border">
                        <div><strong>Additional BPS:</strong> {rule.actions.margin_adjustment.additional_margin_bps}</div>
                        <div><strong>Tier Multiplier:</strong> {rule.actions.margin_adjustment.tier_adjustment_multiplier}</div>
                        {rule.actions.margin_adjustment.min_margin_bps && <div><strong>Min:</strong> {rule.actions.margin_adjustment.min_margin_bps} bps</div>}
                        {rule.actions.margin_adjustment.max_margin_bps && <div><strong>Max:</strong> {rule.actions.margin_adjustment.max_margin_bps} bps</div>}
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {(rule.metadata?.tags || []).map((tag, idx) => (
                    <span key={idx} className="text-xs bg-gray-200 px-2 py-0.5 rounded">{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredRules.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No rules found. Create a new rule to get started.
        </div>
      )}

      {/* Edit Modal - (Same as original, truncated for brevity) */}
      {isModalOpen && editingRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl my-8">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between rounded-t-lg">
              <h2 className="text-xl font-bold">
                {rules.find(r => r.rule_id === editingRule.rule_id) ? 'Edit Rule' : 'New Rule'}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[calc(90vh-12rem)] overflow-y-auto">
              {/* Form fields - same as original */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rule ID</label>
                  <input type="text" value={editingRule.rule_id} disabled className="w-full px-3 py-2 border rounded-lg bg-gray-100" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rule Type</label>
                  <select value={editingRule.rule_type} onChange={(e) => updateEditingRule('rule_type', e.target.value)} className="w-full px-3 py-2 border rounded-lg">
                    <option value="PROVIDER_SELECTION">Provider Selection</option>
                    <option value="MARGIN_ADJUSTMENT">Margin Adjustment</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name *</label>
                  <input type="text" value={editingRule.rule_name} onChange={(e) => updateEditingRule('rule_name', e.target.value)} className="w-full px-3 py-2 border rounded-lg" placeholder="Enter rule name" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <input type="number" value={editingRule.priority} onChange={(e) => updateEditingRule('priority', parseInt(e.target.value))} className="w-full px-3 py-2 border rounded-lg" />
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={editingRule.enabled} onChange={(e) => updateEditingRule('enabled', e.target.checked)} className="w-4 h-4 rounded" />
                    <span className="text-sm font-medium text-gray-700">Enabled</span>
                  </label>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea value={editingRule.metadata.description} onChange={(e) => updateEditingRule('metadata.description', e.target.value)} className="w-full px-3 py-2 border rounded-lg" rows={2} />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
                  <input type="text" value={editingRule.metadata.tags.join(', ')} onChange={(e) => updateEditingRule('metadata.tags', e.target.value.split(',').map(t => t.trim()).filter(t => t))} className="w-full px-3 py-2 border rounded-lg" placeholder="tag1, tag2" />
                </div>
              </div>

              {/* Conditions */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Conditions</label>
                  <button onClick={addCondition} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                    <Plus size={16} /> Add Condition
                  </button>
                </div>
                <div className="space-y-2">
                  {editingRule.conditions.criteria.map((cond, idx) => (
                    <div key={idx} className="flex flex-wrap items-center gap-2 p-3 bg-gray-50 rounded-lg">
                      <select value={cond.field} onChange={(e) => updateCondition(idx, 'field', e.target.value)} className="px-2 py-1 border rounded text-sm">
                        {FIELDS.map(f => <option key={f} value={f}>{f}</option>)}
                      </select>
                      <select value={cond.operator} onChange={(e) => updateCondition(idx, 'operator', e.target.value)} className="px-2 py-1 border rounded text-sm">
                        {OPERATORS.map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                      {['IN', 'NOT_IN', 'BETWEEN'].includes(cond.operator) ? (
                        <input type="text" value={cond.values ? cond.values.join(', ') : ''} onChange={(e) => updateCondition(idx, 'values', e.target.value.split(',').map(v => v.trim()))} placeholder="value1, value2" className="flex-1 min-w-32 px-2 py-1 border rounded text-sm" />
                      ) : (
                        <input type="text" value={cond.value || ''} onChange={(e) => updateCondition(idx, 'value', e.target.value)} placeholder="value" className="flex-1 min-w-32 px-2 py-1 border rounded text-sm" />
                      )}
                      <button onClick={() => removeCondition(idx)} className="p-1 text-red-500 hover:bg-red-50 rounded">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Provider Actions */}
              {editingRule.rule_type === 'PROVIDER_SELECTION' && editingRule.actions.provider_selection && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-700">Provider Selection Actions</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Providers</label>
                      <select multiple value={editingRule.actions.provider_selection.preferred_providers} onChange={(e) => updateEditingRule('actions.provider_selection.preferred_providers', Array.from(e.target.selectedOptions, o => o.value))} className="w-full px-3 py-2 border rounded-lg h-28">
                        {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Excluded Providers</label>
                      <select multiple value={editingRule.actions.provider_selection.excluded_providers} onChange={(e) => updateEditingRule('actions.provider_selection.excluded_providers', Array.from(e.target.selectedOptions, o => o.value))} className="w-full px-3 py-2 border rounded-lg h-28">
                        {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Routing Objective</label>
                      <select value={editingRule.actions.provider_selection.routing_objective_override || ''} onChange={(e) => updateEditingRule('actions.provider_selection.routing_objective_override', e.target.value || null)} className="w-full px-3 py-2 border rounded-lg">
                        <option value="">Default</option>
                        {ROUTING_OBJECTIVES.map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Margin Actions */}
              {editingRule.rule_type === 'MARGIN_ADJUSTMENT' && editingRule.actions.margin_adjustment && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-700">Margin Adjustment Actions</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Additional Margin (bps)</label>
                      <input type="number" value={editingRule.actions.margin_adjustment.additional_margin_bps} onChange={(e) => updateEditingRule('actions.margin_adjustment.additional_margin_bps', parseInt(e.target.value))} className="w-full px-3 py-2 border rounded-lg" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Tier Multiplier</label>
                      <input type="number" step="0.1" value={editingRule.actions.margin_adjustment.tier_adjustment_multiplier} onChange={(e) => updateEditingRule('actions.margin_adjustment.tier_adjustment_multiplier', parseFloat(e.target.value))} className="w-full px-3 py-2 border rounded-lg" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Min Margin (bps)</label>
                      <input type="number" value={editingRule.actions.margin_adjustment.min_margin_bps || ''} onChange={(e) => updateEditingRule('actions.margin_adjustment.min_margin_bps', e.target.value ? parseInt(e.target.value) : null)} className="w-full px-3 py-2 border rounded-lg" placeholder="Optional" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Max Margin (bps)</label>
                      <input type="number" value={editingRule.actions.margin_adjustment.max_margin_bps || ''} onChange={(e) => updateEditingRule('actions.margin_adjustment.max_margin_bps', e.target.value ? parseInt(e.target.value) : null)} className="w-full px-3 py-2 border rounded-lg" placeholder="Optional" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4 flex justify-end gap-3 rounded-b-lg">
              <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-100">Cancel</button>
              <button onClick={handleSaveRule} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
                <Save size={18} /> Save Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
