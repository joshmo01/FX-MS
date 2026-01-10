import { useState, useEffect } from 'react';
import { Database, Settings, DollarSign, TrendingUp } from 'lucide-react';
import { getAdminResource } from '../services/api';
import CustomerTiersTable from './CustomerTiersTable';
import ProvidersTable from './ProvidersTable';
import RatesTable from './RatesTable';
import PricingTable from './PricingTable';

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('customer-tiers');
  const [stats, setStats] = useState({
    'customer-tiers': 0,
    'fx-providers': 0,
    'treasury-rates': 0,
    'pricing-segments': 0,
    'pricing-tiers': 0
  });
  const [, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const resources = ['customer-tiers', 'fx-providers', 'treasury-rates', 'pricing-segments', 'pricing-tiers'];
      const promises = resources.map(resource =>
        getAdminResource(resource)
          .then(res => ({ resource, count: res.data.data?.length || 0 }))
          .catch(() => ({ resource, count: 0 }))
      );

      const results = await Promise.all(promises);
      const newStats = {};
      results.forEach(({ resource, count }) => {
        newStats[resource] = count;
      });
      setStats(newStats);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'customer-tiers', label: 'Customer Tiers', icon: TrendingUp },
    { id: 'fx-providers', label: 'FX Providers', icon: Database },
    { id: 'treasury-rates', label: 'Treasury Rates', icon: DollarSign },
    { id: 'pricing', label: 'Pricing Config', icon: Settings }
  ];

  const StatCard = ({ title, value, icon, color }) => {
    const Icon = icon;
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
          </div>
          <Icon className={`h-12 w-12 ${color} opacity-20`} />
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Reference Data Admin</h1>
        <p className="text-gray-600 mt-2">Manage customer tiers, FX providers, rates, and pricing configuration</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Customer Tiers"
          value={stats['customer-tiers']}
          icon={TrendingUp}
          color="text-blue-600"
        />
        <StatCard
          title="FX Providers"
          value={stats['fx-providers']}
          icon={Database}
          color="text-green-600"
        />
        <StatCard
          title="Treasury Rates"
          value={stats['treasury-rates']}
          icon={DollarSign}
          color="text-purple-600"
        />
        <StatCard
          title="Pricing Rules"
          value={stats['pricing-segments'] + stats['pricing-tiers']}
          icon={Settings}
          color="text-orange-600"
        />
      </div>

      {/* Sub-Tab Navigation */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 font-medium text-sm border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'customer-tiers' && <CustomerTiersTable onUpdate={fetchStats} />}
          {activeTab === 'fx-providers' && <ProvidersTable onUpdate={fetchStats} />}
          {activeTab === 'treasury-rates' && <RatesTable onUpdate={fetchStats} />}
          {activeTab === 'pricing' && <PricingTable onUpdate={fetchStats} />}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
