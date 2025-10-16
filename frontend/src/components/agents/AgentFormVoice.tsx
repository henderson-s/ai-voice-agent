import Select from "../ui/Select";
import { LANGUAGE_OPTIONS } from "../../constants/agent";
//
import type { AgentCreateInput } from "../../types";

interface AgentFormVoiceProps {
  formData: AgentCreateInput;
  onChange: (data: Partial<AgentCreateInput>) => void;
}

export default function AgentFormVoice({
  formData,
  onChange,
}: AgentFormVoiceProps) {
  return (
    <div className="border-b pb-4">
      <h4 className="text-md font-semibold text-gray-700 mb-3">
        Voice Settings
      </h4>
      <Select
        label="Language"
        value={formData.language}
        onChange={(e) => onChange({ language: e.target.value })}
        options={LANGUAGE_OPTIONS}
        helpText="Voice will be automatically selected by Retell AI"
      />
    </div>
  );
}
