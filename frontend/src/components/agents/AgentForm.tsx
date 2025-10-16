/**
 * Agent Form Component - Complete form for creating/editing agents
 */

import { useState } from "react";
import Button from "../ui/Button";
import { Card, CardBody } from "../ui/Card";
import AgentFormBasicInfo from "./AgentFormBasicInfo";
import AgentFormPrompts from "./AgentFormPrompts";
import AgentFormVoice from "./AgentFormVoice";
import AgentFormAdvanced from "./AgentFormAdvanced";
import { DEFAULT_AGENT_FORM_DATA } from "../../constants/agent";
//
import type {
  AgentConfiguration,
  AgentCreateInput,
  AgentUpdateInput,
} from "../../types";

interface AgentFormProps {
  editingAgent: AgentConfiguration | null;
  onSubmit: (data: AgentCreateInput | AgentUpdateInput) => Promise<void>;
  onCancel: () => void;
}

export default function AgentForm({
  editingAgent,
  onSubmit,
  onCancel,
}: AgentFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [formData, setFormData] = useState<AgentCreateInput>(
    editingAgent
      ? {
          name: editingAgent.name || "",
          description: editingAgent.description || "",
          scenario_type: editingAgent.scenario_type || "driver_checkin",
          system_prompt: editingAgent.system_prompt,
          initial_greeting: editingAgent.initial_greeting,
          voice_id: editingAgent.voice_id || "11labs-Adrian",
          language: editingAgent.language || "en-US",
          enable_backchannel: editingAgent.enable_backchannel ?? true,
          backchannel_words: editingAgent.backchannel_words || [
            "mm-hmm",
            "I see",
            "got it",
          ],
          enable_filler_words: editingAgent.enable_filler_words ?? true,
          filler_words: editingAgent.filler_words || ["um", "uh", "hmm"],
          interruption_sensitivity:
            editingAgent.interruption_sensitivity || 0.7,
          response_delay_ms: editingAgent.response_delay_ms || 800,
          responsiveness: editingAgent.responsiveness || 0.8,
          ambient_sound: editingAgent.ambient_sound || "call-center",
          ambient_sound_volume: editingAgent.ambient_sound_volume || 0.5,
          max_call_duration_seconds:
            editingAgent.max_call_duration_seconds || 600,
          enable_auto_end_call: editingAgent.enable_auto_end_call ?? true,
          end_call_after_silence_ms:
            editingAgent.end_call_after_silence_ms || 10000,
          pronunciation_guide: editingAgent.pronunciation_guide || {},
          reminder_keywords: editingAgent.reminder_keywords || [
            "POD",
            "proof of delivery",
          ],
          enable_reminder: editingAgent.enable_reminder ?? true,
          emergency_keywords: editingAgent.emergency_keywords || [
            "accident",
            "crash",
            "emergency",
          ],
        }
      : DEFAULT_AGENT_FORM_DATA
  );

  const handleChange = (data: Partial<AgentCreateInput>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  return (
    <Card className="mb-6 max-h-[80vh] overflow-y-auto">
      <CardBody>
        <h3 className="text-lg font-semibold mb-4">
          {editingAgent ? "Edit Agent" : "Create New Agent"}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <AgentFormBasicInfo formData={formData} onChange={handleChange} />

          {/* Prompts */}
          <AgentFormPrompts formData={formData} onChange={handleChange} />

          {/* Voice Settings */}
          <AgentFormVoice formData={formData} onChange={handleChange} />

          {/* Advanced Settings Toggle */}
          <div>
            <Button
              type="button"
              variant="ghost"
              fullWidth
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? "▼" : "▶"} Advanced Human-Like Settings
              (Recommended)
            </Button>
          </div>

          {/* Advanced Settings */}
          {showAdvanced && (
            <AgentFormAdvanced formData={formData} onChange={handleChange} />
          )}

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <Button type="submit" fullWidth size="lg">
              {editingAgent ? "Update Agent" : "Create Agent"}
            </Button>
            {editingAgent && (
              <Button
                type="button"
                variant="secondary"
                fullWidth
                size="lg"
                onClick={onCancel}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
