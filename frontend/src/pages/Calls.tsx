import { useState, useEffect } from 'react';
import type { Call, CallStatus } from '../types';
import { calls as callsApi } from '../lib/api';
import CallResultsDisplay from '../components/CallResultsDisplay';

const STATUS_COLORS: Record<CallStatus, string> = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
  ended: 'bg-gray-100 text-gray-800',
  initiated: 'bg-yellow-100 text-yellow-800',
};

function formatDuration(seconds?: number): string {
  if (!seconds) return 'N/A';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

export default function Calls() {
  const [callList, setCallList] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadCalls();
  }, []);

  const loadCalls = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await callsApi.list();
      setCallList(data);
    } catch (err) {
      setError('Failed to load calls');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const viewCallDetails = async (call: Call) => {
    try {
      const details = await callsApi.get(call.id);
      setSelectedCall(details);
      setShowDetails(true);
    } catch (err) {
      setError('Failed to load call details');
      console.error(err);
    }
  };

  const deleteCall = async (callId: string) => {
    if (!confirm('Are you sure you want to delete this call? This action cannot be undone.')) {
      return;
    }

    try {
      await callsApi.delete(callId);
      await loadCalls();

      if (selectedCall?.id === callId) {
        setShowDetails(false);
        setSelectedCall(null);
      }
    } catch (err) {
      setError('Failed to delete call');
      console.error(err);
    }
  };

  const handleRefresh = async () => {
    if (!selectedCall) return;

    try {
      const updatedCall = await callsApi.refresh(selectedCall.id);
      setSelectedCall(updatedCall);
      await loadCalls();
    } catch (err) {
      setError('Failed to refresh call data');
      console.error(err);
    }
  };

  const closeDetails = () => {
    setShowDetails(false);
    setSelectedCall(null);
  };

  return (
    <div className="px-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Call History</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading calls...</p>
        </div>
      ) : callList.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">No calls found</p>
          <p className="text-sm mt-2">Make a test call to see it appear here</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {callList.map((call) => (
            <div key={call.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {call.call_type === 'web' ? '🌐 Web Call' : '📞 Phone Call'}
                    </h3>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        STATUS_COLORS[call.status]
                      }`}
                    >
                      {call.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Driver: <span className="font-medium">{call.driver_name}</span> | Load:{' '}
                    <span className="font-medium">{call.load_number}</span>
                  </p>
                  {call.phone_number && (
                    <p className="text-sm text-gray-600">
                      Phone: <span className="font-medium">{call.phone_number}</span>
                    </p>
                  )}
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(call.created_at).toLocaleString()}
                    {call.duration_seconds && (
                      <span className="ml-2">• Duration: {formatDuration(call.duration_seconds)}</span>
                    )}
                  </p>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => viewCallDetails(call)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => deleteCall(call.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Call Details Modal */}
      {showDetails && selectedCall && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold">Call Details</h3>
                <button
                  onClick={closeDetails}
                  className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                >
                  ✕
                </button>
              </div>

              <CallResultsDisplay
                call={selectedCall}
                onRefresh={handleRefresh}
                onStartNew={closeDetails}
              />

              <div className="mt-4">
                <button
                  onClick={closeDetails}
                  className="w-full px-4 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
