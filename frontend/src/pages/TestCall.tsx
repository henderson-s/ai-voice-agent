/**
 * Test Call Page - Pipecat WebRTC Implementation
 * 
 * Provides a complete web-based calling interface using
 * Pipecat voice pipeline with real-time audio streaming.
 */

import { useState, useEffect, useRef } from 'react';
import type { AgentConfiguration, Call, WebCallInput } from '../types';
import { agents as agentsApi, calls as callsApi } from '../lib/api';
import { createPipecatWebSocket, type TranscriptMessage } from '../utils/websocket';
import CallResultsDisplay from '../components/CallResultsDisplay';
import Alert from '../components/ui/Alert';
import Button from '../components/ui/Button';

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
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [callStatus, setCallStatus] = useState<string>('');

  const wsClientRef = useRef<ReturnType<typeof createPipecatWebSocket> | null>(null);

  useEffect(() => {
    loadAgents();

    return () => {
      // Cleanup on unmount
      if (wsClientRef.current) {
        wsClientRef.current.stopAudio();
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

  const fetchCallResultsWithRetry = async () => {
    const MAX_RETRIES = 5;
    const RETRY_DELAY = 2000;
    const INITIAL_DELAY = 3000;

    await new Promise((resolve) => setTimeout(resolve, INITIAL_DELAY));

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        setSuccess(`Fetching call results... (${attempt + 1}/${MAX_RETRIES})`);

        if (!currentCall) continue;

        const fullData = await callsApi.getFull(currentCall.id);

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

  const handlePhoneCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('Phone calling not yet implemented with Pipecat. Use web calls for now.');
  };

  const handleWebCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setCallEnded(false);
    setTranscript([]);

    try {
      // Create call in backend
      const webCallData: WebCallInput = {
        agent_configuration_id: formData.agent_configuration_id,
        driver_name: formData.driver_name,
        load_number: formData.load_number,
      };

      const response = await callsApi.createWeb(webCallData);
      setCurrentCall({ id: response.call_id, status: 'initiated' } as Call);

      // Create WebSocket client with callbacks
      const wsClient = createPipecatWebSocket(response.call_id, {
        onTranscript: (transcript) => {
          setTranscript((prev) => [...prev, transcript]);
        },
        onStatus: (status) => {
          setCallStatus(status);
          if (status === 'started') {
            setInCall(true);
            setSuccess('🎙️ Call started - speak now!');
          } else if (status === 'stopped') {
            setInCall(false);
            setCallEnded(true);
            setProcessingResults(true);
            setSuccess('Call ended. Processing transcript...');
            fetchCallResultsWithRetry();
          }
        },
        onError: (err) => {
          setError(`Call error: ${err}`);
          setInCall(false);
        },
      });
      
      wsClientRef.current = wsClient;

      // Connect to WebSocket
      await wsClient.connect();
      setSuccess('Connected to voice pipeline...');

      // Start audio streaming
      await wsClient.startAudio();
      setSuccess('🎙️ Microphone active - call in progress!');

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start web call');
      setInCall(false);
    } finally {
      setLoading(false);
    }
  };

  const endCall = async () => {
    try {
      if (wsClientRef.current) {
        await wsClientRef.current.stopAudio();
      }
      
      if (currentCall) {
        await callsApi.endCall(currentCall.id);
      }
      
      setInCall(false);
      setCallEnded(true);
      setProcessingResults(true);
      setSuccess('Call ended. Processing results...');
      
      await fetchCallResultsWithRetry();
    } catch (err) {
      setError('Failed to end call');
      console.error(err);
    }
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
    setCallStatus('');
    resetForm();
  };

  const handleRefresh = async () => {
    if (!currentCall) return;

    try {
      setSuccess('Fetching latest call data...');
      const updatedCall = await callsApi.get(currentCall.id);
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
        <Alert variant="success" className="mb-4">
          {success}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      {/* Call Status Indicator */}
      {inCall && (
        <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-semibold text-indigo-900">Call in Progress</span>
            </div>
            <span className="text-sm text-indigo-600">Status: {callStatus}</span>
          </div>
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
                <div className="text-sm">{item.text}</div>
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
              Web Call (Browser)
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
              Phone Call (Coming Soon)
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
              {agentList.length === 0 ? (
                <option value="">No agents available</option>
              ) : (
                agentList.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))
              )}
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

          {/* Action Buttons */}
          {!inCall && !callEnded ? (
            <Button
              type="submit"
              disabled={loading || agentList.length === 0}
              fullWidth
              size="lg"
            >
              {loading
                ? 'Starting...'
                : callType === 'web'
                ? '🎙️ Start Web Call'
                : '📞 Initiate Phone Call'}
            </Button>
          ) : inCall ? (
            <Button
              type="button"
              onClick={endCall}
              variant="danger"
              fullWidth
              size="lg"
            >
              🛑 End Call
            </Button>
          ) : null}
        </form>

        {/* Microphone Permission Note */}
        {callType === 'web' && !inCall && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <span className="font-semibold">🎤 Note:</span> Your browser will ask for microphone
              permission when you start the call.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
