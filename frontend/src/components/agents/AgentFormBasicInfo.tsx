/**
 * Agent Form - Basic Information Section
 */

import { AgentCreateInput, ScenarioType } from '../../types';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { SCENARIO_TYPE_OPTIONS } from '../../constants/agent';

interface AgentFormBasicInfoProps {
  formData: AgentCreateInput;
  onChange: (data: Partial<AgentCreateInput>) => void;
}

export default function AgentFormBasicInfo({ formData, onChange }: AgentFormBasicInfoProps) {
  return (
    <div className="border-b pb-4">
      <h4 className="text-md font-semibold text-gray-700 mb-3">Basic Information</h4>
      <div className="space-y-4">
        <Input
          label="Name *"
          type="text"
          value={formData.name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="Dispatch Check-in Agent"
          required
        />

        <Input
          label="Description"
          type="text"
          value={formData.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Handles routine driver check-ins"
        />

        <Select
          label="Scenario Type *"
          value={formData.scenario_type}
          onChange={(e) => onChange({ scenario_type: e.target.value as ScenarioType })}
          options={SCENARIO_TYPE_OPTIONS}
          helpText="Emergency Protocol can dynamically pivot when emergency keywords are detected"
          required
        />
      </div>
    </div>
  );
}
