import { useState, useEffect } from 'react';
import { calls } from '../lib/api';
import CallResultsDisplay from '../components/CallResultsDisplay';

export default function Calls() {
  const [callList, setCallList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState<any>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadCalls();
  }, []);

  const loadCalls = async () => {
    try {
      const data = await calls.list();
      setCallList(data);
    } catch (error) {
      console.error('Error loading calls:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewCallDetails = async (call: any) => {
    try {
      const details = await calls.get(call.id);
      setSelectedCall(details);
      setShowDetails(true);
    } catch (error) {
      console.error('Error loading call details:', error);
      alert('Error loading call details');
    }
  };

  const deleteCall = async (callId: string) => {
    if (confirm('Are you sure you want to delete this call? This action cannot be undone.')) {
      try {
        await calls.delete(callId);
        loadCalls();
        if (selectedCall && selectedCall.id === callId) {
          setShowDetails(false);
          setSelectedCall(null);
        }
      } catch (error) {
        console.error('Error deleting call:', error);
        alert('Error deleting call');
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'ended': return 'bg-gray-100 text-gray-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="px-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Call History</h2>

      {loading ? (
        <div className="text-center py-8">Loading calls...</div>
      ) : callList.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No calls found</div>
      ) : (
        <div className="grid gap-4">
          {callList.map((call) => (
            <div key={call.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {call.call_type === 'web' ? '🌐 Web Call' : '📞 Phone Call'}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(call.status)}`}>
                      {call.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Driver: {call.driver_name} | Load: {call.load_number}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(call.created_at).toLocaleString()}
                    {call.duration_seconds && (
                      <span className="ml-2">• Duration: {formatDuration(call.duration_seconds)}</span>
                    )}
                  </p>
                  {call.transcript && (
                    <p className="text-xs text-gray-400 mt-2 truncate">
                      Transcript: {call.transcript.substring(0, 100)}...
                    </p>
                  )}
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => viewCallDetails(call)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => deleteCall(call.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
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
                  onClick={() => setShowDetails(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              {/* Use CallResultsDisplay component */}
              <CallResultsDisplay
                call={selectedCall}
                onRefresh={async () => {
                  try {
                    const updatedCall = await calls.refresh(selectedCall.retell_call_id || selectedCall.id);
                    setSelectedCall(updatedCall);
                    loadCalls(); // Also refresh the list
                  } catch (error: any) {
                    console.error('Error refreshing:', error);
                    alert('Error refreshing call data');
                  }
                }}
                onStartNew={() => {
                  setShowDetails(false);
                  setSelectedCall(null);
                }}
              />

              {/* Close button */}
              <div className="mt-4">
                <button
                  onClick={() => setShowDetails(false)}
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