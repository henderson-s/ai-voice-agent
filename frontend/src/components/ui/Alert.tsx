/**
 * Reusable Alert Component
 */

import type { ReactNode } from 'react';
import { cn } from '../../utils/classnames';

export type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<AlertVariant, string> = {
  success: 'bg-green-100 text-green-700 border-green-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
};

export default function Alert({ variant = 'info', children, className }: AlertProps) {
  return (
    <div className={cn('p-4 rounded-lg border', variantClasses[variant], className)}>
      {children}
    </div>
  );
}
