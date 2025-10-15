import { useState, useEffect } from 'react';
import { agents, calls } from '../lib/api';
import { RetellWebClient } from 'retell-client-js-sdk';

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
  const [retellClient] = useState(() => new RetellWebClient());

  useEffect(() => {
    loadAgents();
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
    try {
      const webCallData = {
        agent_configuration_id: formData.agent_configuration_id,
        driver_name: formData.driver_name,
        load_number: formData.load_number,
      };
      const response = await calls.createWeb(webCallData);
      
      await retellClient.startCall({
        accessToken: response.access_token,
      });
      
      setInCall(true);
      setSuccess('Web call started! Speak now...');
      
      retellClient.on('call_ended', () => {
        setInCall(false);
        setSuccess('Call ended.');
      });
    } catch (error: any) {
      alert(error.message);
    }
    setLoading(false);
  };

  const endCall = () => {
    retellClient.stopCall();
    setInCall(false);
  };

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Test Call</h2>

      {success && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">{success}</div>
      )}

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

          {!inCall ? (
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Starting...' : callType === 'web' ? 'Start Web Call' : 'Initiate Phone Call'}
            </button>
          ) : (
            <button
              type="button"
              onClick={endCall}
              className="w-full bg-red-600 text-white py-2 rounded-lg font-medium hover:bg-red-700"
            >
              End Call
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

