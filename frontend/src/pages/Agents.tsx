import { useState, useEffect } from 'react';
import { agents } from '../lib/api';

export default function Agents() {
  const [agentList, setAgentList] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    scenario_type: 'driver_checkin',
    system_prompt: '',
    initial_greeting: '',
  });

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    const data = await agents.list();
    setAgentList(data);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await agents.create(formData);
    setShowForm(false);
    setFormData({ name: '', scenario_type: 'driver_checkin', system_prompt: '', initial_greeting: '' });
    loadAgents();
  };

  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Agent Configurations</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700"
        >
          {showForm ? 'Cancel' : 'New Agent'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Scenario</label>
              <select
                value={formData.scenario_type}
                onChange={(e) => setFormData({ ...formData, scenario_type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="driver_checkin">Driver Check-in</option>
                <option value="emergency_protocol">Emergency Protocol</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
              <textarea
                value={formData.system_prompt}
                onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                rows={4}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Initial Greeting</label>
              <input
                type="text"
                value={formData.initial_greeting}
                onChange={(e) => setFormData({ ...formData, initial_greeting: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700"
            >
              Create Agent
            </button>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {agentList.map((agent) => (
          <div key={agent.id} className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
            <p className="text-sm text-gray-600 mt-1">{agent.scenario_type}</p>
            <p className="text-sm text-gray-500 mt-2">{agent.system_prompt.substring(0, 100)}...</p>
          </div>
        ))}
      </div>
    </div>
  );
}

