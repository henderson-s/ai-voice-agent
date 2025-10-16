import type { Call } from '../../types';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { Card, CardBody } from '../ui/Card';
import { STATUS_COLORS, CALL_TYPE_ICONS, CALL_TYPE_LABELS } from '../../constants/call';
import { formatDateTime, formatDuration } from '../../utils/format';
import { cn } from '../../utils/classnames';

interface CallCardProps {
  call: Call;
  onViewDetails: (call: Call) => void;
  onDelete: (callId: string) => void;
}

export default function CallCard({ call, onViewDetails, onDelete }: CallCardProps) {
  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this call? This action cannot be undone.')) {
      onDelete(call.id);
    }
  };

  return (
    <Card className="hover:shadow-md transition">
      <CardBody>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">
                {CALL_TYPE_ICONS[call.call_type]} {CALL_TYPE_LABELS[call.call_type]}
              </h3>
              <Badge className={cn(STATUS_COLORS[call.status])}>
                {call.status}
              </Badge>
            </div>

            {/* Driver & Load Info */}
            <p className="text-sm text-gray-600">
              Driver: <span className="font-medium">{call.driver_name}</span> | Load:{' '}
              <span className="font-medium">{call.load_number}</span>
            </p>

            {/* Phone Number */}
            {call.phone_number && (
              <p className="text-sm text-gray-600">
                Phone: <span className="font-medium">{call.phone_number}</span>
              </p>
            )}

            {/* Timestamp & Duration */}
            <p className="text-sm text-gray-500 mt-1">
              {formatDateTime(call.created_at)}
              {call.duration_seconds && (
                <span className="ml-2">• Duration: {formatDuration(call.duration_seconds)}</span>
              )}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-2 ml-4">
            <Button size="sm" onClick={() => onViewDetails(call)}>
              View Details
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
