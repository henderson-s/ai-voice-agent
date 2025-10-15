import { useState, useEffect } from 'react';
import { agents, calls } from '../lib/api';
import { RetellWebClient } from 'retell-client-js-sdk';
import CallResultsDisplay from '../components/CallResultsDisplay';

export default function TestCall() {
  const [agentList, setAgentList] = useState<any[]>([]);
  const [callType, setCallType] = useState<'web' | 'phone'>('web');
  const [formData, setFormData] = useState({
    agent_configuration_id: '',
    driver_name: '',
    phone_number: '',
    load_number: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [inCall, setInCall] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [processingResults, setProcessingResults] = useState(false);
  const [currentCall, setCurrentCall] = useState<any>(null);
  const [transcript, setTranscript] = useState<Array<{role: string, content: string}>>([]);
  const [retellClient] = useState(() => new RetellWebClient());

  useEffect(() => {
    loadAgents();

    // Setup Retell event listeners for real-time transcription
    retellClient.on('update', (update) => {
      console.log('Retell update:', update);

      // Handle transcript updates
      if (update.transcript) {
        setTranscript(update.transcript);
      }
    });

    retellClient.on('call_started', () => {
      console.log('Call started');
      setInCall(true);
    });

    retellClient.on('call_ended', async () => {
      console.log('Call ended');
      setInCall(false);
      setCallEnded(true);
      setProcessingResults(true);
      setSuccess('Call ended. Processing transcript and extracting data...');

      // Wait for webhook processing (webhook needs time to analyze transcript)
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds

      // Retry fetching with delay to allow webhook processing
      let retries = 0;
      const maxRetries = 5;

      while (retries < maxRetries) {
        try {
          if (currentCall && currentCall.call_id) {
            setSuccess(`Fetching call results... (${retries + 1}/${maxRetries})`);

            // First try to get the call from database to get the db ID
            let callId = null;
            try {
              const dbCall = await calls.get(currentCall.call_id);
              callId = dbCall.id;
            } catch (e) {
              // Try finding in call list
              const allCalls = await calls.list();
              const foundCall = allCalls.find(c =>
                c.retell_call_id === currentCall.call_id ||
                c.id === currentCall.call_id
              );
              if (foundCall) {
                callId = foundCall.id;
              }
            }

            if (callId) {
              // Fetch full call details including transcript and results
              console.log(`Fetching full details for call ID: ${callId}`);
              const response = await fetch(
                `${import.meta.env.VITE_BACKEND_URL}/calls/${callId}/full`,
                {
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                  }
                }
              );

              console.log(`Response status: ${response.status}`);

              if (response.ok) {
                const fullData = await response.json();
                console.log('Full data received:', fullData);

                // Check if we have results
                if (fullData.results) {
                  setCurrentCall(fullData.call);
                  setProcessingResults(false);
                  setSuccess('✅ Call completed! Results analyzed and ready.');
                  break; // Success - exit retry loop
                } else {
                  // No results yet, retry
                  console.log('No results yet, retrying...');
                  retries++;
                  if (retries < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                  }
                }
              } else {
                const errorText = await response.text();
                console.error('Error fetching full call details:', response.status, errorText);
                retries++;
                if (retries < maxRetries) {
                  await new Promise(resolve => setTimeout(resolve, 2000));
                }
              }
            } else {
              console.error('Could not find call ID');
              retries++;
              if (retries < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 2000));
              }
            }
          } else {
            break; // No current call, exit
          }
        } catch (error) {
          console.error('Error in retry loop:', error);
          retries++;
          if (retries < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }

      // If we exhausted retries, show a message
      if (retries >= maxRetries) {
        setProcessingResults(false);
        setSuccess('Call completed. Click "Refresh Data" if results don\'t appear.');
      }
    });

    retellClient.on('error', (error) => {
      console.error('Retell error:', error);
      alert('Call error: ' + error.message);
    });

    return () => {
      // Cleanup on unmount
      if (inCall) {
        retellClient.stopCall();
      }
    };
  }, []);

  const loadAgents = async () => {
    const data = await agents.list();
    setAgentList(data);
    if (data.length > 0) {
      setFormData({ ...formData, agent_configuration_id: data[0].id });
    }
  };

  const handlePhoneCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await calls.createPhone(formData);
      setSuccess('Phone call initiated successfully!');
      setFormData({ ...formData, driver_name: '', phone_number: '', load_number: '' });
    } catch (error: any) {
      alert(error.message);
    }
    setLoading(false);
  };

  const handleWebCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setCallEnded(false);
    setTranscript([]);
    try {
      const webCallData = {
        agent_configuration_id: formData.agent_configuration_id,
        driver_name: formData.driver_name,
        load_number: formData.load_number,
      };
      const response = await calls.createWeb(webCallData);

      setCurrentCall(response);
      await retellClient.startCall({
        accessToken: response.access_token,
      });

      setSuccess('Web call started! Speak now...');

      // Wait a moment for webhook to process after call ends
      setTimeout(async () => {
        if (!inCall && callEnded) {
          try {
            let callDetails = null;

            if (response.call_id) {
              try {
                callDetails = await calls.get(response.call_id);
              } catch (e) {
                console.log('Could not fetch by call_id, trying by retell_call_id');
              }
            }

            if (!callDetails) {
              const allCalls = await calls.list();
              callDetails = allCalls.find(call =>
                call.retell_call_id === response.call_id ||
                call.id === response.call_id
              );
            }

            if (callDetails) {
              setCurrentCall(callDetails);
              setSuccess('Call completed successfully!');
            } else {
              console.error('Could not find call details');
              setSuccess('Call ended but details not yet available. Check call history in a moment.');
            }
          } catch (error) {
            console.error('Error fetching call details:', error);
            setSuccess('Call ended but could not fetch details. Check call history.');
          }
        }
      }, 2000);
    } catch (error: any) {
      alert(error.message);
      setInCall(false);
    }
    setLoading(false);
  };

  const endCall = async () => {
    retellClient.stopCall();
    setSuccess('Call ended by user. Fetching results...');

    // Wait for webhook processing and fetch call details
    setTimeout(async () => {
      try {
        let callDetails = null;

        if (currentCall && currentCall.call_id) {
          try {
            callDetails = await calls.get(currentCall.call_id);
          } catch (e) {
            console.log('Could not fetch by call_id, trying by retell_call_id');
          }
        }

        if (!callDetails && currentCall && currentCall.retell_call_id) {
          const allCalls = await calls.list();
          callDetails = allCalls.find(call =>
            call.retell_call_id === currentCall.retell_call_id
          );
        }

        if (callDetails) {
          setCurrentCall(callDetails);
          setSuccess('Call ended successfully!');
        } else {
          setSuccess('Call ended. Check call history for details.');
        }
      } catch (error) {
        console.error('Error fetching call details:', error);
        setSuccess('Call ended. Check call history for details.');
      }
    }, 2000);
  };

  const startNewCall = () => {
    setCallEnded(false);
    setProcessingResults(false);
    setCurrentCall(null);
    setTranscript([]);
    setSuccess('');
    setFormData({ ...formData, driver_name: '', phone_number: '', load_number: '' });
  };

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Test Call</h2>

      {success && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">{success}</div>
      )}

      {/* Real-time transcript during call */}
      {inCall && transcript.length > 0 && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-blue-800">🎙️ Live Transcript</h3>
            <span className="text-xs text-blue-600 animate-pulse">● RECORDING</span>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {transcript.map((item, index) => (
              <div key={index} className={`p-2 rounded ${
                item.role === 'agent'
                  ? 'bg-indigo-100 text-indigo-900 ml-4'
                  : 'bg-white text-gray-900 mr-4'
              }`}>
                <div className="text-xs font-semibold mb-1 uppercase">
                  {item.role === 'agent' ? '🤖 Agent' : '👤 You'}
                </div>
                <div className="text-sm">{item.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing indicator */}
      {processingResults && (
        <div className="mb-4 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <div>
              <p className="text-blue-900 font-medium">Analyzing call transcript...</p>
              <p className="text-blue-700 text-sm mt-1">Extracting structured data from conversation</p>
            </div>
          </div>
        </div>
      )}

      {/* Call results after call ends */}
      {callEnded && currentCall && !processingResults && <CallResultsDisplay call={currentCall} onRefresh={async () => {
        try {
          setSuccess('Fetching latest call data...');
          const callIdToUse = currentCall.retell_call_id || currentCall.id;
          const updatedCall = await calls.refresh(callIdToUse);
          setCurrentCall(updatedCall);
          setSuccess('Call data refreshed successfully!');
        } catch (error: any) {
          console.error('Error refreshing:', error);
          setSuccess('Error refreshing call data');
        }
      }} onStartNew={startNewCall} />}

      <div className="bg-white p-6 rounded-lg shadow">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Call Type</label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setCallType('web')}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                callType === 'web'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Web Call (Test Now)
            </button>
            <button
              type="button"
              onClick={() => setCallType('phone')}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                callType === 'phone'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Phone Call
            </button>
          </div>
        </div>

        <form onSubmit={callType === 'web' ? handleWebCall : handlePhoneCall} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Agent</label>
            <select
              value={formData.agent_configuration_id}
              onChange={(e) => setFormData({ ...formData, agent_configuration_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
            >
              {agentList.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Driver Name</label>
            <input
              type="text"
              value={formData.driver_name}
              onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="John Smith"
              required
            />
          </div>

          {callType === 'phone' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="+1234567890"
                required={callType === 'phone'}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Load Number</label>
            <input
              type="text"
              value={formData.load_number}
              onChange={(e) => setFormData({ ...formData, load_number: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="LOAD-12345"
              required
            />
          </div>

          {!inCall && !callEnded ? (
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Starting...' : callType === 'web' ? 'Start Web Call' : 'Initiate Phone Call'}
            </button>
          ) : inCall ? (
            <button
              type="button"
              onClick={endCall}
              className="w-full bg-red-600 text-white py-2 rounded-lg font-medium hover:bg-red-700"
            >
              End Call
            </button>
          ) : null}
        </form>
      </div>
    </div>
  );
}

