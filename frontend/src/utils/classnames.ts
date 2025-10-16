/**
 * Utility function for conditionally joining classNames
 * Similar to clsx/classnames libraries
 */

type ClassValue = string | number | boolean | undefined | null | ClassValue[];

export function cn(...classes: ClassValue[]): string {
  return classes
    .flat()
    .filter((x) => typeof x === 'string' && x.length > 0)
    .join(' ');
}
