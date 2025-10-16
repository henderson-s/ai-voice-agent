import { useState, useEffect } from "react";
import { calls as callsApi } from "../lib/api";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import CallCard from "../components/calls/CallCard";
import CallResultsDisplay from "../components/CallResultsDisplay";
//
import type { Call } from "../types";

export default function Calls() {
  const [callList, setCallList] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadCalls();
  }, []);

  const loadCalls = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await callsApi.list();
      setCallList(data);
    } catch (err) {
      setError("Failed to load calls");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (call: Call) => {
    try {
      const details = await callsApi.get(call.id);
      setSelectedCall(details);
      setShowDetails(true);
    } catch (err) {
      setError("Failed to load call details");
      console.error(err);
    }
  };

  const handleDelete = async (callId: string) => {
    try {
      await callsApi.delete(callId);
      await loadCalls();

      if (selectedCall?.id === callId) {
        setShowDetails(false);
        setSelectedCall(null);
      }
    } catch (err) {
      setError("Failed to delete call");
      console.error(err);
    }
  };

  const handleRefresh = async () => {
    if (!selectedCall) return;

    try {
      const updatedCall = await callsApi.refresh(selectedCall.id);
      setSelectedCall(updatedCall);
      await loadCalls();
    } catch (err) {
      setError("Failed to refresh call data");
      console.error(err);
    }
  };

  const handleCloseModal = () => {
    setShowDetails(false);
    setSelectedCall(null);
  };

  return (
    <div className="px-4">
      <PageHeader title="Call History" />

      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      {loading ? (
        <LoadingSpinner message="Loading calls..." />
      ) : callList.length === 0 ? (
        <EmptyState
          icon="📞"
          title="No calls found"
          message="Make a test call to see it appear here"
        />
      ) : (
        <div className="grid gap-4">
          {callList.map((call) => (
            <CallCard
              key={call.id}
              call={call}
              onViewDetails={handleViewDetails}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Call Details Modal */}
      <Modal
        isOpen={showDetails}
        onClose={handleCloseModal}
        title="Call Details"
        size="xl"
      >
        {selectedCall && (
          <>
            <CallResultsDisplay
              call={selectedCall}
              onRefresh={handleRefresh}
              onStartNew={handleCloseModal}
            />
            <div className="mt-4">
              <Button
                fullWidth
                variant="secondary"
                size="lg"
                onClick={handleCloseModal}
              >
                Close
              </Button>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
