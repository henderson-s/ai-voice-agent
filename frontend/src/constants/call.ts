/**
 * Constants for Call Management
 */

import type { CallStatus } from '../types';

export const STATUS_COLORS: Record<CallStatus, string> = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
  ended: 'bg-gray-100 text-gray-800',
  initiated: 'bg-yellow-100 text-yellow-800',
};

export const CALL_TYPE_ICONS = {
  web: '🌐',
  phone: '📞',
};

export const CALL_TYPE_LABELS = {
  web: 'Web Call',
  phone: 'Phone Call',
};

export const RETRY_CONFIG = {
  MAX_RETRIES: 5,
  RETRY_DELAY: 2000, // 2 seconds
  INITIAL_DELAY: 5000, // 5 seconds
};
