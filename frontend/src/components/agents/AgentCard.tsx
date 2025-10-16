/**
 * Agent Card Component - Displays agent information in a card
 */

import { AgentConfiguration } from '../../types';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { Card, CardBody } from '../ui/Card';
import { formatDate } from '../../utils/format';

interface AgentCardProps {
  agent: AgentConfiguration;
  onEdit: (agent: AgentConfiguration) => void;
  onDelete: (agentId: string) => void;
}

export default function AgentCard({ agent, onEdit, onDelete }: AgentCardProps) {
  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      onDelete(agent.id);
    }
  };

  return (
    <Card>
      <CardBody>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
              <Badge variant="info">
                {agent.scenario_type === 'driver_checkin' ? 'Check-in' : 'Emergency'}
              </Badge>
            </div>

            {/* Description */}
            {agent.description && (
              <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
            )}

            {/* Greeting */}
            <p className="text-sm text-gray-500 mt-2">
              Greeting: <span className="italic">{agent.initial_greeting}</span>
            </p>

            {/* Features */}
            <div className="mt-2 flex flex-wrap gap-2">
              {agent.enable_backchannel && (
                <Badge variant="success">Backchannel</Badge>
              )}
              {agent.enable_filler_words && (
                <Badge variant="success">Filler Words</Badge>
              )}
              {agent.ambient_sound !== 'off' && (
                <Badge variant="default">Ambient: {agent.ambient_sound}</Badge>
              )}
            </div>

            {/* Metadata */}
            <div className="mt-2 text-xs text-gray-400 flex items-center gap-2">
              <span>Created: {formatDate(agent.created_at)}</span>
              {agent.retell_agent_id && (
                <Badge variant="success">Active in Retell</Badge>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 ml-4">
            <Button size="sm" onClick={() => onEdit(agent)}>
              Edit
            </Button>
            <Button size="sm" variant="danger" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
