/**
 * Reusable Badge Component
 */

import type { ReactNode } from 'react';
import { cn } from '../../utils/classnames';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
};

export default function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'px-2 py-1 rounded text-xs font-medium inline-block',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
