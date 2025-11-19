import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { Sun, Moon, User, LogOut, Database, Home, Table } from 'lucide-react';
import { Button, Badge, Tooltip } from './ui';
import api from '../services/api';

const Header = ({ user, onLogout, generationProgress }) => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await api.logout();
      onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-background-card dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm transition-theme">
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left: Logo, Title, and Navigation */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <img src="/here-xy.jpg" alt="HERE Technologies" className="h-10 w-10 object-contain" />
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  Metadata Explorer
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  HERE Technologies
                </p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="flex items-center gap-2">
              <Link
                to="/"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  isActive('/')
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Home className="h-4 w-4" />
                <span className="text-sm font-medium">Browse</span>
              </Link>
              <Link
                to="/enriched-tables"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  isActive('/enriched-tables')
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Table className="h-4 w-4" />
                <span className="text-sm font-medium">Enriched Tables</span>
              </Link>
            </nav>
          </div>

          {/* Center: Progress Bar (if generating) */}
          {generationProgress && (
            <div className="flex-1 max-w-md mx-8">
              <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary-600 dark:bg-primary-400 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${generationProgress.progress || 0}%` }}
                />
              </div>
              <p className="text-xs text-center mt-1 text-gray-600 dark:text-gray-400">
                {generationProgress.message || 'Processing...'}
              </p>
            </div>
          )}

          {/* Right: User Info and Actions */}
          <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            <Tooltip content={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} position="bottom">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-all focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>
            </Tooltip>

            {/* User Info */}
            {user && (
              <>
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <User className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                  <div className="text-sm">
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {user.username}
                    </p>
                    {user.email && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {user.email}
                      </p>
                    )}
                  </div>
                </div>

                {/* Logout Button */}
                <Tooltip content="Logout" position="bottom">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<LogOut className="h-4 w-4" />}
                    onClick={handleLogout}
                    aria-label="Logout"
                  >
                    <span className="hidden sm:inline">Logout</span>
                  </Button>
                </Tooltip>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
