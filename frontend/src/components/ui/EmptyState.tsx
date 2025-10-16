/**
 * Reusable Empty State Component
 */

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: string;
}

export default function EmptyState({ title, message, icon = '📭' }: EmptyStateProps) {
  return (
    <div className="text-center py-12 text-gray-500">
      <div className="text-5xl mb-4">{icon}</div>
      <p className="text-lg font-medium">{title}</p>
      <p className="text-sm mt-2">{message}</p>
    </div>
  );
}
