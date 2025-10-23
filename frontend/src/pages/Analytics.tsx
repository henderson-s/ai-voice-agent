/**
 * Analytics Dashboard Page
 * 
 * Displays comprehensive analytics metrics for voice calls,
 * including cost tracking, call outcomes, and performance metrics.
 */

import { useState, useEffect } from 'react';
import { analytics as analyticsApi } from '../lib/api';
import PageHeader from '../components/ui/PageHeader';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { Card, CardBody, CardHeader } from '../components/ui/Card';
import Alert from '../components/ui/Alert';

interface MetricsData {
  summary: {
    total_calls: number;
    average_duration_seconds: number;
    total_interruptions: number;
    average_interruptions: number;
    total_tokens: number;
    total_cost: number;
    analyzed_calls: number;
  };
  costs: {
    llm_cost: number;
    tts_cost: number;
    stt_cost: number;
    total_cost: number;
    call_count: number;
  };
  outcomes: Record<string, number>;
}

export default function Analytics() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await analyticsApi.getMetrics();
      setMetrics(data);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading analytics..." />;
  }

  if (error) {
    return (
      <div className="px-4">
        <PageHeader title="Analytics Dashboard" />
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="px-4">
        <PageHeader title="Analytics Dashboard" />
        <Alert variant="info">No analytics data available yet. Make some calls to see metrics!</Alert>
      </div>
    );
  }

  const { summary, costs, outcomes } = metrics;

  return (
    <div className="px-4 max-w-7xl mx-auto">
      <PageHeader title="Analytics Dashboard" />

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Total Calls"
          value={summary.total_calls}
          icon="📞"
          color="blue"
        />
        <MetricCard
          title="Avg Duration"
          value={`${Math.round(summary.average_duration_seconds)}s`}
          icon="⏱️"
          color="green"
        />
        <MetricCard
          title="Total Cost"
          value={`$${summary.total_cost.toFixed(4)}`}
          icon="💰"
          color="purple"
        />
        <MetricCard
          title="Interruptions"
          value={summary.total_interruptions}
          subtitle={`Avg: ${summary.average_interruptions.toFixed(1)}`}
          icon="🔄"
          color="orange"
        />
      </div>

      {/* Cost Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <AnalyticsCard title="Cost Breakdown">
          <div className="space-y-4">
            <CostItem label="LLM (OpenAI)" amount={costs.llm_cost} total={costs.total_cost} color="blue" />
            <CostItem label="TTS (Cartesia)" amount={costs.tts_cost} total={costs.total_cost} color="green" />
            <CostItem label="STT (Deepgram)" amount={costs.stt_cost} total={costs.total_cost} color="purple" />
            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <span className="font-bold text-gray-900">Total</span>
                <span className="font-bold text-xl text-gray-900">
                  ${costs.total_cost.toFixed(4)}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Across {costs.call_count} call{costs.call_count !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </AnalyticsCard>

        <AnalyticsCard title="Token Usage">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Total Tokens</span>
              <span className="text-2xl font-bold text-indigo-600">
                {summary.total_tokens.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">Analyzed Calls</span>
              <span className="font-medium text-gray-900">{summary.analyzed_calls}</span>
            </div>
            {summary.analyzed_calls > 0 && (
              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Avg Tokens/Call</span>
                  <span className="font-medium text-gray-900">
                    {Math.round(summary.total_tokens / summary.analyzed_calls).toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>
        </AnalyticsCard>
      </div>

      {/* Call Outcomes */}
      <AnalyticsCard title="Call Outcomes Distribution">
        {Object.keys(outcomes).length === 0 ? (
          <p className="text-gray-500 text-center py-8">No call outcomes data available</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(outcomes)
              .sort(([, a], [, b]) => b - a)
              .map(([outcome, count]) => (
                <OutcomeBar
                  key={outcome}
                  label={formatOutcome(outcome)}
                  count={count}
                  total={Object.values(outcomes).reduce((sum, val) => sum + val, 0)}
                />
              ))}
          </div>
        )}
      </AnalyticsCard>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <StatBox
          label="Avg Interruptions/Call"
          value={summary.average_interruptions.toFixed(2)}
          description="User interruptions during calls"
        />
        <StatBox
          label="Cost per Call"
          value={`$${summary.analyzed_calls > 0 ? (summary.total_cost / summary.analyzed_calls).toFixed(4) : '0.00'}`}
          description="Average cost per analyzed call"
        />
        <StatBox
          label="Tokens per Call"
          value={summary.analyzed_calls > 0 ? Math.round(summary.total_tokens / summary.analyzed_calls).toLocaleString() : '0'}
          description="Average tokens per call"
        />
      </div>
    </div>
  );
}

// ============================================
// Helper Components
// ============================================

interface AnalyticsCardProps {
  title: string;
  children: React.ReactNode;
}

function AnalyticsCard({ title, children }: AnalyticsCardProps) {
  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </CardHeader>
      <CardBody>
        {children}
      </CardBody>
    </Card>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

function MetricCard({ title, value, subtitle, icon, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200',
    orange: 'bg-orange-50 border-orange-200',
  };

  return (
    <div className={`p-6 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <span className="text-2xl font-bold text-gray-900">{value}</span>
      </div>
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

interface CostItemProps {
  label: string;
  amount: number;
  total: number;
  color: 'blue' | 'green' | 'purple';
}

function CostItem({ label, amount, total, color }: CostItemProps) {
  const percentage = total > 0 ? (amount / total) * 100 : 0;
  
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold text-gray-900">${amount.toFixed(4)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% of total</p>
    </div>
  );
}

interface OutcomeBarProps {
  label: string;
  count: number;
  total: number;
}

function OutcomeBar({ label, count, total }: OutcomeBarProps) {
  const percentage = (count / total) * 100;

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-gray-900">{count}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="h-3 rounded-full bg-indigo-600"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}%</p>
    </div>
  );
}

interface StatBoxProps {
  label: string;
  value: string;
  description: string;
}

function StatBox({ label, value, description }: StatBoxProps) {
  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200">
      <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
  );
}

// ============================================
// Utility Functions
// ============================================

function formatOutcome(outcome: string): string {
  return outcome
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

