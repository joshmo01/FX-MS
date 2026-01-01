import { useState } from 'react';

export default function RulesTab({ rules, onToggleRule, onDeleteRule }) {
  const [ruleFilter, setRuleFilter] = useState('ALL');
  const [showRuleCreate, setShowRuleCreate] = useState(false);

  const safeRules = Array.isArray(rules) ? rules : [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Rules Management</h2>
          <p className="text-gray-500">Configure pricing and provider selection rules</p>
        </div>
        <button
          onClick={() => setShowRuleCreate(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
        >
          <span>⚙️</span> Create Rule
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['ALL', 'PROVIDER_SELECTION', 'MARGIN_ADJUSTMENT'].map(filter => (
          <button
            key={filter}
            onClick={() => setRuleFilter(filter)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              ruleFilter === filter ? 'bg-purple-600 text-white' : 'bg-gray-100'
            }`}
          >
            {filter === 'ALL' ? 'All Rules' :
             filter === 'PROVIDER_SELECTION' ? 'Provider Selection' :
             'Margin Adjustment'}
          </button>
        ))}
      </div>

      {/* Rules Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-4 rounded-xl text-white">
          <p className="text-sm opacity-80">Total Rules</p>
          <p className="text-2xl font-bold">{safeRules.length}</p>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-4 rounded-xl text-white">
          <p className="text-sm opacity-80">Enabled</p>
          <p className="text-2xl font-bold">{safeRules.filter(r => r?.enabled).length}</p>
        </div>
        <div className="bg-gradient-to-r from-blue-500 to-cyan-600 p-4 rounded-xl text-white">
          <p className="text-sm opacity-80">Provider Rules</p>
          <p className="text-2xl font-bold">
            {safeRules.filter(r => r?.rule_type === 'PROVIDER_SELECTION').length}
          </p>
        </div>
        <div className="bg-gradient-to-r from-orange-500 to-red-600 p-4 rounded-xl text-white">
          <p className="text-sm opacity-80">Pricing Rules</p>
          <p className="text-2xl font-bold">
            {safeRules.filter(r => r?.rule_type === 'MARGIN_ADJUSTMENT').length}
          </p>
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-4">
        {safeRules
          .filter(r => ruleFilter === 'ALL' || r?.rule_type === ruleFilter)
          .sort((a, b) => (b?.priority || 0) - (a?.priority || 0))
          .map((rule, idx) => (
            <div
              key={rule?.rule_id || idx}
              className={`bg-white rounded-xl shadow p-6 border-l-4 ${
                rule?.enabled ? 'border-green-500' : 'border-gray-300'
              }`}
            >
              {/* Rule Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{rule?.rule_name || 'Unnamed'}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      rule?.rule_type === 'PROVIDER_SELECTION'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-orange-100 text-orange-700'
                    }`}>
                      {rule?.rule_type === 'PROVIDER_SELECTION' ? '🏦 Provider' : '💰 Pricing'}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                      Priority: {rule?.priority || 0}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      rule?.enabled
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {rule?.enabled ? '✓ Enabled' : '✗ Disabled'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {rule?.metadata?.description || 'No description'}
                  </p>
                  <p className="text-xs text-gray-400 font-mono">{rule?.rule_id || 'No ID'}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onToggleRule(rule?.rule_id)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium ${
                      rule?.enabled
                        ? 'bg-gray-100 hover:bg-gray-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {rule?.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => onDeleteRule(rule?.rule_id)}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Rule Details */}
              <div className="grid grid-cols-2 gap-6">
                {/* Conditions */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">
                    📋 Conditions ({rule?.conditions?.operator || 'AND'})
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1 text-xs">
                    {(rule?.conditions?.criteria || []).map((crit, cidx) => (
                      <div key={cidx} className="flex justify-between">
                        <span className="text-gray-600">{crit?.field || '?'}</span>
                        <span className="font-medium">
                          {crit?.operator || '?'}{' '}
                          {crit?.value !== null && crit?.value !== undefined
                            ? crit.value
                            : (crit?.values || []).join(', ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">⚡ Actions</h4>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1 text-xs">
                    {rule?.rule_type === 'PROVIDER_SELECTION' &&
                     rule?.actions?.provider_selection && (
                      <>
                        {(rule.actions.provider_selection.preferred_providers || []).length > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Preferred:</span>
                            <span className="font-medium text-green-600">
                              {rule.actions.provider_selection.preferred_providers.join(', ')}
                            </span>
                          </div>
                        )}
                        {(rule.actions.provider_selection.excluded_providers || []).length > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Excluded:</span>
                            <span className="font-medium text-red-600">
                              {rule.actions.provider_selection.excluded_providers.join(', ')}
                            </span>
                          </div>
                        )}
                        {rule.actions.provider_selection.routing_objective_override && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Objective:</span>
                            <span className="font-medium">
                              {rule.actions.provider_selection.routing_objective_override}
                            </span>
                          </div>
                        )}
                      </>
                    )}
                    {rule?.rule_type === 'MARGIN_ADJUSTMENT' &&
                     rule?.actions?.margin_adjustment && (
                      <>
                        {rule.actions.margin_adjustment.additional_margin_bps != null && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Additional Margin:</span>
                            <span className={`font-medium ${
                              rule.actions.margin_adjustment.additional_margin_bps < 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}>
                              {rule.actions.margin_adjustment.additional_margin_bps > 0 ? '+' : ''}
                              {rule.actions.margin_adjustment.additional_margin_bps} bps
                            </span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Tags */}
              {(rule?.metadata?.tags || []).length > 0 && (
                <div className="mt-3 flex gap-2">
                  {rule.metadata.tags.map((tag, tidx) => (
                    <span
                      key={tidx}
                      className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
      </div>

      {/* Create Rule Modal */}
      {showRuleCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl m-4">
            <h3 className="text-lg font-semibold mb-4">Create New Rule</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-700">📝 Edit JSON files to create rules:</p>
              <ul className="text-xs text-blue-600 mt-2 ml-4 space-y-1">
                <li>• Provider: <code className="bg-blue-100 px-1 rounded">config/rules/provider_rules.json</code></li>
                <li>• Pricing: <code className="bg-blue-100 px-1 rounded">config/rules/pricing_rules.json</code></li>
              </ul>
            </div>
            <button
              onClick={() => setShowRuleCreate(false)}
              className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
