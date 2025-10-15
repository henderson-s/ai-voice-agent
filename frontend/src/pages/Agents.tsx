import { useState, useEffect } from 'react';
import { agents } from '../lib/api';

export default function Agents() {
  const [agentList, setAgentList] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const defaultPrompt = `You are a professional dispatch agent calling truck drivers about their loads. Your role is to gather information and handle any situation that arises during the call.

NORMAL CHECK-IN FLOW:
- Start with an open-ended question about their current status
- If driving: ask about location, ETA, and any delays
- If arrived: ask about unloading status and timeline
- Always remind them about the POD (Proof of Delivery) at the end
- Be conversational, professional, and adaptive

EMERGENCY PROTOCOL:
If the driver mentions ANY emergency (accident, blowout, breakdown, medical issue, injury, etc.):
1. IMMEDIATELY switch to emergency mode
2. Confirm: "Are you safe right now?"
3. Ask: "Is anyone injured?"
4. Get: "What is your exact location?"
5. Verify: "Is the load secure?"
6. Say: "I'm connecting you to a human dispatcher right now for immediate assistance"

CONVERSATION STYLE:
- Be professional but warm
- Handle unclear responses by politely asking them to repeat
- If one-word answers, gently probe for detail
- Stay calm at all times
- Adapt your questions based on their responses
- Never be pushy or aggressive`;

  const [formData, setFormData] = useState({
    name: '',
    system_prompt: defaultPrompt,
    initial_greeting: 'Hi {driver_name}, this is Dispatch with a check call on load {load_number}. Can you give me an update on your status?',
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
    setFormData({ name: '', system_prompt: defaultPrompt, initial_greeting: 'Hi {driver_name}, this is Dispatch with a check call on load {load_number}. Can you give me an update on your status?' });
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
                placeholder="Dispatch Agent"
                required
              />
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
            {agent.description && <p className="text-sm text-gray-600 mt-1">{agent.description}</p>}
            <p className="text-sm text-gray-500 mt-2">{agent.system_prompt.substring(0, 150)}...</p>
          </div>
        ))}
      </div>
    </div>
  );
}

