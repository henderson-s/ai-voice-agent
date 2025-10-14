import { useState, useEffect } from 'react';
import { agents, calls } from '../lib/api';

export default function TestCall() {
  const [agentList, setAgentList] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    agent_configuration_id: '',
    driver_name: '',
    phone_number: '',
    load_number: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await calls.createPhone(formData);
      setSuccess('Call initiated successfully!');
      setFormData({ ...formData, driver_name: '', phone_number: '', load_number: '' });
    } catch (error: any) {
      alert(error.message);
    }
    setLoading(false);
  };

  return (
    <div className="px-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Test Call</h2>

      {success && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">{success}</div>
      )}

      <div className="bg-white p-6 rounded-lg shadow">
        <form onSubmit={handleSubmit} className="space-y-4">
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
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="+1234567890"
              required
            />
          </div>

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

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Initiating...' : 'Start Call'}
          </button>
        </form>
      </div>
    </div>
  );
}

