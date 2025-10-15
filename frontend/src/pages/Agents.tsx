import { useState, useEffect } from 'react';
import type { AgentConfiguration, AgentCreateInput, AgentUpdateInput, ScenarioType, AmbientSound } from '../types';
import { agents as agentsApi } from '../lib/api';

export default function Agents() {
  const [agentList, setAgentList] = useState<AgentConfiguration[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentConfiguration | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

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

  const defaultFormData: AgentCreateInput = {
    name: '',
    description: '',
    scenario_type: 'driver_checkin' as ScenarioType,
    system_prompt: defaultPrompt,
    initial_greeting: 'Hi {{driver_name}}, this is Dispatch with a check call on load {{load_number}}. Can you give me an update on your status?',
    voice_id: '11labs-Adrian',
    language: 'en-US',
    enable_backchannel: true,
    backchannel_words: ['mm-hmm', 'I see', 'got it', 'okay'],
    enable_filler_words: true,
    filler_words: ['um', 'uh', 'hmm', 'let me see'],
    interruption_sensitivity: 0.7,
    response_delay_ms: 800,
    responsiveness: 0.8,
    ambient_sound: 'call-center',
    ambient_sound_volume: 0.5,
    max_call_duration_seconds: 600,
    enable_auto_end_call: true,
    end_call_after_silence_ms: 10000,
    pronunciation_guide: {},
    reminder_keywords: ['POD', 'proof of delivery', 'paperwork'],
    enable_reminder: true,
    emergency_keywords: ['accident', 'crash', 'emergency', 'help', 'breakdown', 'broke down', 'medical', 'injury', 'blowout', 'flat tire', 'broke', 'stuck']
  };

  const [formData, setFormData] = useState<AgentCreateInput>(defaultFormData);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    const data = await agentsApi.list();
    setAgentList(data);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingAgent) {
      await agentsApi.update(editingAgent.id, formData as AgentUpdateInput);
      setShowEditForm(false);
      setEditingAgent(null);
    } else {
      await agentsApi.create(formData);
      setShowForm(false);
    }
    setFormData(defaultFormData);
    setShowAdvanced(false);
    loadAgents();
  };

  const handleEdit = (agent: AgentConfiguration) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name || '',
      description: agent.description || '',
      scenario_type: (agent.scenario_type || 'driver_checkin') as ScenarioType,
      system_prompt: agent.system_prompt,
      initial_greeting: agent.initial_greeting,
      voice_id: agent.voice_id || '11labs-Adrian',
      language: agent.language || 'en-US',
      enable_backchannel: agent.enable_backchannel ?? true,
      backchannel_words: agent.backchannel_words || ['mm-hmm', 'I see', 'got it'],
      enable_filler_words: agent.enable_filler_words ?? true,
      filler_words: agent.filler_words || ['um', 'uh', 'hmm'],
      interruption_sensitivity: agent.interruption_sensitivity || 0.7,
      response_delay_ms: agent.response_delay_ms || 800,
      responsiveness: agent.responsiveness || 0.8,
      ambient_sound: agent.ambient_sound || 'call-center',
      ambient_sound_volume: agent.ambient_sound_volume || 0.5,
      max_call_duration_seconds: agent.max_call_duration_seconds || 600,
      enable_auto_end_call: agent.enable_auto_end_call ?? true,
      end_call_after_silence_ms: agent.end_call_after_silence_ms || 10000,
      pronunciation_guide: agent.pronunciation_guide || {},
      reminder_keywords: agent.reminder_keywords || ['POD', 'proof of delivery'],
      enable_reminder: agent.enable_reminder ?? true,
      emergency_keywords: agent.emergency_keywords || ['accident', 'crash', 'emergency']
    });
    setShowEditForm(true);
    setShowForm(false);
  };

  const handleDelete = async (agentId: string) => {
    if (confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      await agentsApi.delete(agentId);
      loadAgents();
    }
  };

  const cancelEdit = () => {
    setShowEditForm(false);
    setEditingAgent(null);
    setFormData(defaultFormData);
    setShowAdvanced(false);
  };

  const handleArrayInput = (field: string, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(s => s);
    setFormData({ ...formData, [field]: array });
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

      {(showForm || showEditForm) && (
        <div className="bg-white p-6 rounded-lg shadow mb-6 max-h-[80vh] overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">{editingAgent ? 'Edit Agent' : 'Create New Agent'}</h3>
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Basic Information */}
            <div className="border-b pb-4">
              <h4 className="text-md font-semibold text-gray-700 mb-3">Basic Information</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="Dispatch Check-in Agent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="Handles routine driver check-ins"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Scenario Type *</label>
                  <select
                    value={formData.scenario_type}
                    onChange={(e) => setFormData({ ...formData, scenario_type: e.target.value as ScenarioType })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="driver_checkin">Driver Check-in (Standard)</option>
                    <option value="emergency_protocol">Emergency Protocol (Dynamic Pivot)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Emergency Protocol can dynamically pivot when emergency keywords are detected
                  </p>
                </div>
              </div>
            </div>

            {/* Prompts */}
            <div className="border-b pb-4">
              <h4 className="text-md font-semibold text-gray-700 mb-3">Prompts & Greetings</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt *</label>
                  <textarea
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                    rows={8}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Initial Greeting *
                  </label>
                  <input
                    type="text"
                    value={formData.initial_greeting}
                    onChange={(e) => setFormData({ ...formData, initial_greeting: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use <code className="bg-gray-100 px-1 rounded">{'{driver_name}'}</code> and{' '}
                    <code className="bg-gray-100 px-1 rounded">{'{load_number}'}</code> placeholders
                  </p>
                </div>
              </div>
            </div>

            {/* Voice Settings */}
            <div className="border-b pb-4">
              <h4 className="text-md font-semibold text-gray-700 mb-3">Voice Settings</h4>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <select
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="en-US">English (US)</option>
                  <option value="es-ES">Spanish</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Voice will be automatically selected by Retell AI</p>
              </div>
            </div>

            {/* Advanced Settings Toggle */}
            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700 flex items-center justify-center gap-2"
              >
                {showAdvanced ? '▼' : '▶'} Advanced Human-Like Settings (Recommended)
              </button>
            </div>

            {showAdvanced && (
              <>
                {/* Human-Like Behavior */}
                <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-md font-semibold text-gray-700 mb-3">Human-Like Behavior</h4>
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enable_backchannel}
                        onChange={(e) => setFormData({ ...formData, enable_backchannel: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <label className="text-sm font-medium text-gray-700">Enable Backchanneling (mm-hmm, I see)</label>
                    </div>

                    {formData.enable_backchannel && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Backchannel Words</label>
                        <input
                          type="text"
                          value={formData.backchannel_words?.join(', ') || ''}
                          onChange={(e) => handleArrayInput('backchannel_words', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          placeholder="mm-hmm, I see, got it"
                        />
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enable_filler_words}
                        onChange={(e) => setFormData({ ...formData, enable_filler_words: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <label className="text-sm font-medium text-gray-700">Enable Filler Words (um, uh)</label>
                    </div>

                    {formData.enable_filler_words && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Filler Words</label>
                        <input
                          type="text"
                          value={formData.filler_words?.join(', ') || ''}
                          onChange={(e) => handleArrayInput('filler_words', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          placeholder="um, uh, hmm"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Conversation Dynamics */}
                <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-md font-semibold text-gray-700 mb-3">Conversation Dynamics</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Interruption Sensitivity: {formData.interruption_sensitivity}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={formData.interruption_sensitivity}
                        onChange={(e) => setFormData({ ...formData, interruption_sensitivity: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">Lower = harder to interrupt, Higher = more natural conversation</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Response Delay: {formData.response_delay_ms}ms
                      </label>
                      <input
                        type="range"
                        min="500"
                        max="1500"
                        step="50"
                        value={formData.response_delay_ms}
                        onChange={(e) => setFormData({ ...formData, response_delay_ms: parseInt(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">Natural pause before agent responds</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Responsiveness: {formData.responsiveness}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={formData.responsiveness}
                        onChange={(e) => setFormData({ ...formData, responsiveness: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">How quickly agent picks up on conversation cues</p>
                    </div>
                  </div>
                </div>

                {/* Ambient Sound */}
                <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-md font-semibold text-gray-700 mb-3">Ambient Sound (Realism)</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Ambient Sound Type</label>
                      <select
                        value={formData.ambient_sound}
                        onChange={(e) => setFormData({ ...formData, ambient_sound: e.target.value as AmbientSound })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="call-center">Call Center</option>
                        <option value="coffee-shop">Coffee Shop</option>
                        <option value="convention-hall">Convention Hall</option>
                        <option value="summer-outdoor">Summer Outdoor</option>
                        <option value="mountain-outdoor">Mountain Outdoor</option>
                        <option value="static-noise">Static Noise</option>
                      </select>
                      <p className="text-xs text-gray-500 mt-1">Adds realistic background ambience</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Ambient Volume: {formData.ambient_sound_volume}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={formData.ambient_sound_volume}
                        onChange={(e) => setFormData({ ...formData, ambient_sound_volume: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500">Range: 0 (quiet) to 2 (loud), default: 1</p>
                    </div>
                  </div>
                </div>

                {/* Scenario-Specific Settings */}
                <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-md font-semibold text-gray-700 mb-3">Scenario-Specific Settings</h4>
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enable_reminder}
                        onChange={(e) => setFormData({ ...formData, enable_reminder: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <label className="text-sm font-medium text-gray-700">Enable POD/Reminder</label>
                    </div>

                    {formData.enable_reminder && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Reminder Keywords</label>
                        <input
                          type="text"
                          value={formData.reminder_keywords?.join(', ') || ''}
                          onChange={(e) => handleArrayInput('reminder_keywords', e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          placeholder="POD, proof of delivery, paperwork"
                        />
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Detection Keywords</label>
                      <input
                        type="text"
                        value={formData.emergency_keywords?.join(', ') || ''}
                        onChange={(e) => handleArrayInput('emergency_keywords', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="accident, crash, breakdown, medical"
                      />
                      <p className="text-xs text-gray-500 mt-1">Agent will pivot to emergency protocol when these are detected</p>
                    </div>
                  </div>
                </div>

                {/* Call Management */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-md font-semibold text-gray-700 mb-3">Call Management</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Max Call Duration (seconds)</label>
                      <input
                        type="number"
                        value={formData.max_call_duration_seconds}
                        onChange={(e) => setFormData({ ...formData, max_call_duration_seconds: parseInt(e.target.value) })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enable_auto_end_call}
                        onChange={(e) => setFormData({ ...formData, enable_auto_end_call: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <label className="text-sm font-medium text-gray-700">Auto-end call after silence</label>
                    </div>

                    {formData.enable_auto_end_call && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Silence Timeout (ms)</label>
                        <input
                          type="number"
                          value={formData.end_call_after_silence_ms}
                          onChange={(e) => setFormData({ ...formData, end_call_after_silence_ms: parseInt(e.target.value) })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <button
                type="submit"
                className="flex-1 bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700"
              >
                {editingAgent ? 'Update Agent' : 'Create Agent'}
              </button>
              {showEditForm && (
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="flex-1 bg-gray-500 text-white py-3 rounded-lg font-medium hover:bg-gray-600"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {/* Agent List */}
      <div className="grid gap-4">
        {agentList.map((agent) => (
          <div key={agent.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                    {agent.scenario_type === 'driver_checkin' ? 'Check-in' : 'Emergency'}
                  </span>
                </div>
                {agent.description && <p className="text-sm text-gray-600 mt-1">{agent.description}</p>}
                <p className="text-sm text-gray-500 mt-2">
                  Greeting: <span className="italic">{agent.initial_greeting}</span>
                </p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {agent.enable_backchannel && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Backchannel</span>
                  )}
                  {agent.enable_filler_words && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Filler Words</span>
                  )}
                  {agent.ambient_sound !== 'off' && (
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                      Ambient: {agent.ambient_sound}
                    </span>
                  )}
                </div>
                <div className="mt-2 text-xs text-gray-400">
                  Created: {new Date(agent.created_at).toLocaleDateString()}
                  {agent.retell_agent_id && (
                    <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded">
                      Active in Retell
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => handleEdit(agent)}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(agent.id)}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
