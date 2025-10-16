/**
 * Formatting utility functions
 */

export function formatDuration(seconds?: number): string {
  if (!seconds) return 'N/A';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString();
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString();
}

export function arrayToString(arr: string[]): string {
  return arr.join(', ');
}

export function stringToArray(str: string): string[] {
  return str.split(',').map(s => s.trim()).filter(s => s);
}
