/**
 * Reusable Loading Spinner Component
 */

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export default function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div
        className={`animate-spin rounded-full border-b-2 border-indigo-600 ${sizeClasses[size]}`}
      />
      {message && <p className="mt-2 text-gray-600">{message}</p>}
    </div>
  );
}
