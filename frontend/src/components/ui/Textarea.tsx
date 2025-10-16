/**
 * Reusable Textarea Component
 */

import type { TextareaHTMLAttributes } from 'react';
import { cn } from '../../utils/classnames';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
}

export default function Textarea({
  label,
  error,
  helpText,
  className,
  ...props
}: TextareaProps) {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <textarea
        className={cn(
          'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none',
          error ? 'border-red-300' : 'border-gray-300',
          className
        )}
        {...props}
      />
      {helpText && (
        <p className="text-xs text-gray-500 mt-1">{helpText}</p>
      )}
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );
}
