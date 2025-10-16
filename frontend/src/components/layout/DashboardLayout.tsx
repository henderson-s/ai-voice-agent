/**
 * Dashboard Layout - Wrapper for all authenticated pages
 * Provides navigation and consistent layout structure
 */

import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
