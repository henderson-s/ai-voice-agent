/**
 * Agent Form - Prompts & Greetings Section
 */

import { AgentCreateInput } from '../../types';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';

interface AgentFormPromptsProps {
  formData: AgentCreateInput;
  onChange: (data: Partial<AgentCreateInput>) => void;
}

export default function AgentFormPrompts({ formData, onChange }: AgentFormPromptsProps) {
  return (
    <div className="border-b pb-4">
      <h4 className="text-md font-semibold text-gray-700 mb-3">Prompts & Greetings</h4>
      <div className="space-y-4">
        <Textarea
          label="System Prompt *"
          value={formData.system_prompt}
          onChange={(e) => onChange({ system_prompt: e.target.value })}
          className="font-mono text-sm"
          rows={8}
          required
        />

        <Input
          label="Initial Greeting *"
          type="text"
          value={formData.initial_greeting}
          onChange={(e) => onChange({ initial_greeting: e.target.value })}
          helpText={
            <>
              Use <code className="bg-gray-100 px-1 rounded">{'{{driver_name}}'}</code> and{' '}
              <code className="bg-gray-100 px-1 rounded">{'{{load_number}}'}</code> placeholders
            </>
          }
          required
        />
      </div>
    </div>
  );
}
