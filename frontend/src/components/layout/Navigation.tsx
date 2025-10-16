/**
 * Navigation Component - Reusable top navigation bar
 */

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../ui/Button';
import { cn } from '../../utils/classnames';

interface NavLink {
  to: string;
  label: string;
}

const navLinks: NavLink[] = [
  { to: '/dashboard/agents', label: 'Agents' },
  { to: '/dashboard/test-call', label: 'Test Call' },
  { to: '/dashboard/calls', label: 'Call History' },
];

export default function Navigation() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Left side - Logo and nav links */}
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-indigo-600">Voice Agent</h1>
            </div>

            {/* Navigation Links */}
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition',
                    isActive(link.to)
                      ? 'border-indigo-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Right side - User info and logout */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">{user?.email}</span>
            <Button size="sm" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
