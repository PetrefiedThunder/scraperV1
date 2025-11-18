/**
 * Main layout component with navigation
 */

import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/dashboard" className="text-2xl font-bold text-purple-600">
                GrandmaScraper
              </Link>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center space-x-6">
              <Link
                to="/dashboard"
                className="text-gray-700 hover:text-purple-600 font-medium transition"
              >
                Dashboard
              </Link>
              <Link
                to="/jobs/new"
                className="text-gray-700 hover:text-purple-600 font-medium transition"
              >
                Create Job
              </Link>
              <Link
                to="/templates"
                className="text-gray-700 hover:text-purple-600 font-medium transition"
              >
                Templates
              </Link>

              {/* User Menu */}
              <div className="flex items-center space-x-4 pl-6 border-l border-gray-200">
                <span className="text-sm text-gray-600">
                  {user?.username || user?.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-700 hover:text-red-600 font-medium transition"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
