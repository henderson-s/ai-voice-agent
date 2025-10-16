import { useState, useEffect } from "react";
import { agents as agentsApi } from "../lib/api";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import EmptyState from "../components/ui/EmptyState";
import AgentCard from "../components/agents/AgentCard";
import AgentForm from "../components/agents/AgentForm";
import type {
  AgentConfiguration,
  AgentCreateInput,
  AgentUpdateInput,
} from "../types";

export default function Agents() {
  const [agentList, setAgentList] = useState<AgentConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentConfiguration | null>(
    null
  );

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await agentsApi.list();
      setAgentList(data);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data: AgentCreateInput | AgentUpdateInput) => {
    if (editingAgent) {
      await agentsApi.update(editingAgent.id, data as AgentUpdateInput);
      setEditingAgent(null);
    } else {
      await agentsApi.create(data as AgentCreateInput);
      setShowForm(false);
    }
    await loadAgents();
  };

  const handleEdit = (agent: AgentConfiguration) => {
    setEditingAgent(agent);
    setShowForm(false);
  };

  const handleDelete = async (agentId: string) => {
    await agentsApi.delete(agentId);
    await loadAgents();
  };

  const handleCancel = () => {
    setEditingAgent(null);
    setShowForm(false);
  };

  const handleNewAgent = () => {
    setEditingAgent(null);
    setShowForm(!showForm);
  };

  return (
    <div className="px-4">
      <PageHeader
        title="Agent Configurations"
        action={
          <Button onClick={handleNewAgent}>
            {showForm ? "Cancel" : "New Agent"}
          </Button>
        }
      />

      {/* Agent Form */}
      {(showForm || editingAgent) && (
        <AgentForm
          editingAgent={editingAgent}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      )}

      {/* Agent List */}
      {loading ? (
        <LoadingSpinner message="Loading agents..." />
      ) : agentList.length === 0 ? (
        <EmptyState
          icon="🤖"
          title="No agents found"
          message="Create your first AI voice agent to get started"
        />
      ) : (
        <div className="grid gap-4">
          {agentList.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
