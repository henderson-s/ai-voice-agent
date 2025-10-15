import { useState, useEffect } from 'react';
import type { Call, CallResults, CallTranscript } from '../types';
import { calls as callsApi } from '../lib/api';

interface CallResultsDisplayProps {
  call: Call;
  onRefresh: () => Promise<void>;
  onStartNew: () => void;
}

/**
 * Format enum values for display (snake_case to Title Case)
 */
function formatFieldValue(value: string | null | undefined): string {
  if (!value) return 'Not specified';
  return value
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function CallResultsDisplay({
  call,
  onRefresh,
  onStartNew,
}: CallResultsDisplayProps) {
  const [results, setResults] = useState<CallResults | null>(null);
  const [transcript, setTranscript] = useState<CallTranscript | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCallDetails();
  }, [call.id]);

  const fetchCallDetails = async (): Promise<void> => {
    if (!call.id) {
      setLoading(false);
      setError('No call ID provided');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await callsApi.getFull(call.id);
      setResults(data.results || null);
      setTranscript(data.transcript || null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch call details';
      setError(errorMessage);
      console.error('Error fetching call details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (): Promise<void> => {
    try {
      setRefreshing(true);
      setError(null);
      await onRefresh();
      await fetchCallDetails();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh data';
      setError(errorMessage);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="mb-4 p-6 bg-white border border-gray-200 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading call results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-4 p-6 bg-white border border-red-200 rounded-lg">
        <div className="text-center">
          <p className="text-red-600 font-medium">Error loading call results</p>
          <p className="mt-1 text-sm text-red-500">{error}</p>
          <button
            onClick={fetchCallDetails}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const isEmergency = results?.is_emergency || false;

  return (
    <div className="space-y-4 mb-4">
      {/* Header Card */}
      <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">Call Results</h3>
            <p className="text-sm text-gray-500 mt-1">
              Status: <span className="font-medium text-gray-700">{call.status}</span>
              {call.duration_seconds && (
                <> • Duration: <span className="font-medium text-gray-700">
                  {Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s
                </span></>
              )}
            </p>
          </div>
          {isEmergency ? (
            <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-semibold">
              🚨 EMERGENCY
            </span>
          ) : (
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
              ✓ Normal Call
            </span>
          )}
        </div>

        {/* Call Summary */}
        {results?.call_summary && (
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">📋 Call Summary</h4>
            <p className="text-sm text-blue-800">{results.call_summary}</p>
          </div>
        )}
      </div>

      {/* Structured Data Card */}
      {results && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">Extracted Data</h4>

          {isEmergency ? (
            // Emergency Data
            <div className="grid grid-cols-2 gap-4">
              <InfoField
                label="Call Outcome"
                value={formatFieldValue(results.call_outcome)}
                variant="red"
              />
              <InfoField
                label="Emergency Type"
                value={formatFieldValue(results.emergency_type)}
                variant="red"
              />
              <InfoField label="Safety Status" value={results.safety_status} />
              <InfoField
                label="Injury Status"
                value={formatFieldValue(results.injury_status)}
              />
              <InfoField label="Emergency Location" value={results.location_emergency} />
              <InfoField
                label="Load Secure"
                value={results.load_secure === true ? 'Yes' : results.load_secure === false ? 'No' : 'Unknown'}
                variant={results.load_secure === false ? 'red' : 'default'}
              />
              <InfoField label="Escalation Status" value={results.escalation_status} className="col-span-2" />
            </div>
          ) : (
            // Normal Check-in Data
            <div className="grid grid-cols-2 gap-4">
              <InfoField
                label="Call Outcome"
                value={formatFieldValue(results.call_outcome)}
                variant="green"
              />
              <InfoField
                label="Driver Status"
                value={formatFieldValue(results.driver_status)}
                variant="green"
              />
              <InfoField label="Current Location" value={results.current_location} className="col-span-2" />
              <InfoField label="ETA" value={results.eta} />
              <InfoField label="Delay Reason" value={results.delay_reason || 'None'} />
              <InfoField label="Unloading Status" value={results.unloading_status} />
              <InfoField
                label="POD Reminder"
                value={results.pod_reminder_acknowledged ? 'Acknowledged' : 'Not Acknowledged'}
                variant={results.pod_reminder_acknowledged ? 'green' : 'gray'}
              />
            </div>
          )}
        </div>
      )}

      {/* Transcript Card */}
      {transcript?.transcript && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">Full Transcript</h4>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
              {transcript.transcript}
            </pre>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {refreshing ? '🔄 Refreshing...' : '🔄 Refresh Data'}
        </button>
        <button
          onClick={onStartNew}
          className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition"
        >
          ➕ Start New Call
        </button>
      </div>
    </div>
  );
}

interface InfoFieldProps {
  label: string;
  value: any;
  variant?: 'default' | 'green' | 'red' | 'gray';
  className?: string;
}

function InfoField({ label, value, variant = 'default', className = '' }: InfoFieldProps) {
  const displayValue = value || 'Not specified';

  const variantStyles = {
    default: 'bg-gray-50 border-gray-200',
    green: 'bg-green-50 border-green-200',
    red: 'bg-red-50 border-red-200',
    gray: 'bg-gray-100 border-gray-300',
  };

  const textStyles = {
    default: 'text-gray-900',
    green: 'text-green-900',
    red: 'text-red-900',
    gray: 'text-gray-600',
  };

  return (
    <div className={`p-3 rounded-lg border ${variantStyles[variant]} ${className}`}>
      <div className="text-xs font-semibold text-gray-500 uppercase mb-1">{label}</div>
      <div className={`text-sm font-medium ${textStyles[variant]}`}>{displayValue}</div>
    </div>
  );
}
