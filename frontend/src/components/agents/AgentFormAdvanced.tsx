import Input from "../ui/Input";
import Select from "../ui/Select";
import { AMBIENT_SOUND_OPTIONS } from "../../constants/agent";
import { arrayToString, stringToArray } from "../../utils/format";
import type { AgentCreateInput, AmbientSound } from "../../types";

interface AgentFormAdvancedProps {
  formData: AgentCreateInput;
  onChange: (data: Partial<AgentCreateInput>) => void;
}

export default function AgentFormAdvanced({
  formData,
  onChange,
}: AgentFormAdvancedProps) {
  const handleArrayInput = (field: keyof AgentCreateInput, value: string) => {
    onChange({ [field]: stringToArray(value) });
  };

  return (
    <div className="space-y-6">
      {/* Human-Like Behavior */}
      <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Human-Like Behavior
        </h4>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enable_backchannel}
              onChange={(e) =>
                onChange({ enable_backchannel: e.target.checked })
              }
              className="w-4 h-4"
            />
            <label className="text-sm font-medium text-gray-700">
              Enable Backchanneling (mm-hmm, I see)
            </label>
          </div>

          {formData.enable_backchannel && (
            <Input
              label="Backchannel Words"
              type="text"
              value={arrayToString(formData.backchannel_words || [])}
              onChange={(e) =>
                handleArrayInput("backchannel_words", e.target.value)
              }
              placeholder="mm-hmm, I see, got it"
            />
          )}

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enable_filler_words}
              onChange={(e) =>
                onChange({ enable_filler_words: e.target.checked })
              }
              className="w-4 h-4"
            />
            <label className="text-sm font-medium text-gray-700">
              Enable Filler Words (um, uh)
            </label>
          </div>

          {formData.enable_filler_words && (
            <Input
              label="Filler Words"
              type="text"
              value={arrayToString(formData.filler_words || [])}
              onChange={(e) => handleArrayInput("filler_words", e.target.value)}
              placeholder="um, uh, hmm"
            />
          )}
        </div>
      </div>

      {/* Conversation Dynamics */}
      <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Conversation Dynamics
        </h4>
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
              onChange={(e) =>
                onChange({
                  interruption_sensitivity: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <p className="text-xs text-gray-500">
              Lower = harder to interrupt, Higher = more natural conversation
            </p>
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
              onChange={(e) =>
                onChange({ response_delay_ms: parseInt(e.target.value) })
              }
              className="w-full"
            />
            <p className="text-xs text-gray-500">
              Natural pause before agent responds
            </p>
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
              onChange={(e) =>
                onChange({ responsiveness: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <p className="text-xs text-gray-500">
              How quickly agent picks up on conversation cues
            </p>
          </div>
        </div>
      </div>

      {/* Ambient Sound */}
      <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Ambient Sound (Realism)
        </h4>
        <div className="space-y-4">
          <Select
            label="Ambient Sound Type"
            value={formData.ambient_sound}
            onChange={(e) =>
              onChange({ ambient_sound: e.target.value as AmbientSound })
            }
            options={AMBIENT_SOUND_OPTIONS}
            helpText="Adds realistic background ambience"
          />

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
              onChange={(e) =>
                onChange({ ambient_sound_volume: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <p className="text-xs text-gray-500">
              Range: 0 (quiet) to 2 (loud), default: 1
            </p>
          </div>
        </div>
      </div>

      {/* Scenario-Specific Settings */}
      <div className="border-b pb-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Scenario-Specific Settings
        </h4>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enable_reminder}
              onChange={(e) => onChange({ enable_reminder: e.target.checked })}
              className="w-4 h-4"
            />
            <label className="text-sm font-medium text-gray-700">
              Enable POD/Reminder
            </label>
          </div>

          {formData.enable_reminder && (
            <Input
              label="Reminder Keywords"
              type="text"
              value={arrayToString(formData.reminder_keywords || [])}
              onChange={(e) =>
                handleArrayInput("reminder_keywords", e.target.value)
              }
              placeholder="POD, proof of delivery, paperwork"
            />
          )}

          <Input
            label="Emergency Detection Keywords"
            type="text"
            value={arrayToString(formData.emergency_keywords || [])}
            onChange={(e) =>
              handleArrayInput("emergency_keywords", e.target.value)
            }
            placeholder="accident, crash, breakdown, medical"
            helpText="Agent will pivot to emergency protocol when these are detected"
          />
        </div>
      </div>

      {/* Call Management */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-gray-700 mb-3">
          Call Management
        </h4>
        <div className="space-y-4">
          <Input
            label="Max Call Duration (seconds)"
            type="number"
            value={formData.max_call_duration_seconds?.toString()}
            onChange={(e) =>
              onChange({ max_call_duration_seconds: parseInt(e.target.value) })
            }
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.enable_auto_end_call}
              onChange={(e) =>
                onChange({ enable_auto_end_call: e.target.checked })
              }
              className="w-4 h-4"
            />
            <label className="text-sm font-medium text-gray-700">
              Auto-end call after silence
            </label>
          </div>

          {formData.enable_auto_end_call && (
            <Input
              label="Silence Timeout (ms)"
              type="number"
              value={formData.end_call_after_silence_ms?.toString()}
              onChange={(e) =>
                onChange({
                  end_call_after_silence_ms: parseInt(e.target.value),
                })
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}
