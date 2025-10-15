import { useState, useEffect } from 'react';
import { RetellWebClient } from 'retell-client-js-sdk';
import type { AgentConfiguration, Call, WebCallInput, PhoneCallInput, TranscriptEntry } from '../types';
import { agents as agentsApi, calls as callsApi } from '../lib/api';
import CallResultsDisplay from '../components/CallResultsDisplay';

type CallType = 'web' | 'phone';

interface CallFormData {
  agent_configuration_id: string;
  driver_name: string;
  phone_number: string;
  load_number: string;
}

const INITIAL_FORM_DATA: CallFormData = {
  agent_configuration_id: '',
  driver_name: '',
  phone_number: '',
  load_number: '',
};

export default function TestCall() {
  const [agentList, setAgentList] = useState<AgentConfiguration[]>([]);
  const [callType, setCallType] = useState<CallType>('web');
  const [formData, setFormData] = useState<CallFormData>(INITIAL_FORM_DATA);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [inCall, setInCall] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [processingResults, setProcessingResults] = useState(false);
  const [currentCall, setCurrentCall] = useState<Call | null>(null);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [retellClient] = useState(() => new RetellWebClient());

  useEffect(() => {
    loadAgents();
    setupRetellListeners();

    return () => {
      if (inCall) {
        retellClient.stopCall();
      }
    };
  }, []);

  const loadAgents = async () => {
    try {
      const data = await agentsApi.list();
      setAgentList(data);
      if (data.length > 0) {
        setFormData((prev) => ({ ...prev, agent_configuration_id: data[0].id }));
      }
    } catch (err) {
      setError('Failed to load agents');
      console.error(err);
    }
  };

  const setupRetellListeners = () => {
    retellClient.on('update', (update: any) => {
      if (update.transcript) {
        setTranscript(update.transcript);
      }
    });

    retellClient.on('call_started', () => {
      setInCall(true);
      setSuccess('Call started - speak now!');
    });

    retellClient.on('call_ended', async () => {
      setInCall(false);
      setCallEnded(true);
      setProcessingResults(true);
      setSuccess('Call ended. Processing transcript and extracting data...');

      await fetchCallResultsWithRetry();
    });

    retellClient.on('error', (error: any) => {
      console.error('Retell error:', error);
      setError(`Call error: ${error.message}`);
      setInCall(false);
    });
  };

  const fetchCallResultsWithRetry = async () => {
    const MAX_RETRIES = 5;
    const RETRY_DELAY = 2000;
    const INITIAL_DELAY = 5000;

    await new Promise((resolve) => setTimeout(resolve, INITIAL_DELAY));

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        setSuccess(`Fetching call results... (${attempt + 1}/${MAX_RETRIES})`);

        const callId = await findCallId();
        if (!callId) {
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
          continue;
        }

        const fullData = await callsApi.getFull(callId);

        if (fullData.results) {
          setCurrentCall(fullData.call);
          setProcessingResults(false);
          setSuccess('✅ Call completed! Results analyzed and ready.');
          return;
        }

        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      } catch (err) {
        console.error('Error fetching call results:', err);
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      }
    }

    setProcessingResults(false);
    setSuccess('Call completed. Click "Refresh Data" if results don\'t appear.');
  };

  const findCallId = async (): Promise<string | null> => {
    if (!currentCall) return null;

    try {
      const call = await callsApi.get(currentCall.id);
      return call.id;
    } catch {
      // Try finding in call list
      try {
        const allCalls = await callsApi.list();
        const foundCall = allCalls.find(
          (c) => c.retell_call_id === currentCall.retell_call_id || c.id === currentCall.id
        );
        return foundCall?.id || null;
      } catch {
        return null;
      }
    }
  };

  const handlePhoneCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const phoneCallData: PhoneCallInput = {
        agent_configuration_id: formData.agent_configuration_id,
        driver_name: formData.driver_name,
        phone_number: formData.phone_number,
        load_number: formData.load_number,
      };

      await callsApi.createPhone(phoneCallData);
      setSuccess('Phone call initiated successfully!');
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate phone call');
    } finally {
      setLoading(false);
    }
  };

  const handleWebCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setCallEnded(false);
    setTranscript([]);

    try {
      const webCallData: WebCallInput = {
        agent_configuration_id: formData.agent_configuration_id,
        driver_name: formData.driver_name,
        load_number: formData.load_number,
      };

      const response = await callsApi.createWeb(webCallData);
      setCurrentCall({ id: response.call_id } as Call);

      await retellClient.startCall({
        accessToken: response.access_token,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start web call');
      setInCall(false);
    } finally {
      setLoading(false);
    }
  };

  const endCall = async () => {
    retellClient.stopCall();
    setSuccess('Call ended by user. Fetching results...');
  };

  const resetForm = () => {
    setFormData({
      ...formData,
      driver_name: '',
      phone_number: '',
      load_number: '',
    });
  };

  const startNewCall = () => {
    setCallEnded(false);
    setProcessingResults(false);
    setCurrentCall(null);
    setTranscript([]);
    setSuccess('');
    setError('');
    resetForm();
  };

  const handleRefresh = async () => {
    if (!currentCall) return;

    try {
      setSuccess('Fetching latest call data...');
      const updatedCall = await callsApi.refresh(currentCall.id);
      setCurrentCall(updatedCall);
      setSuccess('Call data refreshed successfully!');
    } catch (err) {
      setError('Failed to refresh call data');
      console.error(err);
    }
  };

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Test Call</h2>

      {/* Success Message */}
      {success && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg border border-green-200">
          {success}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Live Transcript During Call */}
      {inCall && transcript.length > 0 && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-blue-800">🎙️ Live Transcript</h3>
            <span className="text-xs text-blue-600 animate-pulse">● RECORDING</span>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {transcript.map((item, index) => (
              <div
                key={index}
                className={`p-2 rounded ${
                  item.role === 'agent'
                    ? 'bg-indigo-100 text-indigo-900 ml-4'
                    : 'bg-white text-gray-900 mr-4'
                }`}
              >
                <div className="text-xs font-semibold mb-1 uppercase">
                  {item.role === 'agent' ? '🤖 Agent' : '👤 You'}
                </div>
                <div className="text-sm">{item.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Indicator */}
      {processingResults && (
        <div className="mb-4 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <div>
              <p className="text-blue-900 font-medium">Analyzing call transcript...</p>
              <p className="text-blue-700 text-sm mt-1">
                Extracting structured data from conversation
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Call Results After Call Ends */}
      {callEnded && currentCall && !processingResults && (
        <CallResultsDisplay
          call={currentCall}
          onRefresh={handleRefresh}
          onStartNew={startNewCall}
        />
      )}

      {/* Call Form */}
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
              disabled={inCall || callEnded}
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
              disabled={inCall || callEnded}
            >
              Phone Call
            </button>
          </div>
        </div>

        <form
          onSubmit={callType === 'web' ? handleWebCall : handlePhoneCall}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Agent
            </label>
            <select
              value={formData.agent_configuration_id}
              onChange={(e) =>
                setFormData({ ...formData, agent_configuration_id: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              required
              disabled={inCall || callEnded}
            >
              {agentList.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Driver Name
            </label>
            <input
              type="text"
              value={formData.driver_name}
              onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="John Smith"
              required
              disabled={inCall || callEnded}
            />
          </div>

          {callType === 'phone' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder="+1234567890"
                required
                disabled={inCall || callEnded}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Load Number
            </label>
            <input
              type="text"
              value={formData.load_number}
              onChange={(e) => setFormData({ ...formData, load_number: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="LOAD-12345"
              required
              disabled={inCall || callEnded}
            />
          </div>

          {!inCall && !callEnded ? (
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading
                ? 'Starting...'
                : callType === 'web'
                ? 'Start Web Call'
                : 'Initiate Phone Call'}
            </button>
          ) : inCall ? (
            <button
              type="button"
              onClick={endCall}
              className="w-full bg-red-600 text-white py-2 rounded-lg font-medium hover:bg-red-700 transition"
            >
              End Call
            </button>
          ) : null}
        </form>
      </div>
    </div>
  );
}
