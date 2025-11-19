import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Header from './components/Header';
import LeftRail from './components/LeftRail';
import TableDataViewer from './components/TableDataViewer';
import MetadataViewer from './components/MetadataViewer';
import EnrichedTablesPage from './components/EnrichedTablesPage';
import MetadataEditModal from './components/MetadataEditModal';
import { EmptyState, Spinner } from './components/ui';
import { Database } from 'lucide-react';
import api from './services/api';

function App() {
  const [selectedTable, setSelectedTable] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLeftRailCollapsed, setIsLeftRailCollapsed] = useState(false);

  // Modal state for editing metadata from enriched tables page
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [tableToEdit, setTableToEdit] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Check if token exists in localStorage
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setLoading(false);
        return;
      }

      // Validate token with backend
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.log('Not authenticated');
      // Clear invalid token
      localStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    // Clear token from localStorage
    localStorage.removeItem('auth_token');
    setUser(null);
    setSelectedTable(null);
  };

  const handleEditMetadata = (table) => {
    setTableToEdit(table);
    setEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setEditModalOpen(false);
    setTableToEdit(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-gray-900">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : <Login onLoginSuccess={handleLoginSuccess} />}
        />

        <Route
          path="/"
          element={
            user ? (
              <div className="flex flex-col h-screen bg-background-light dark:bg-gray-900 transition-theme">
                {/* Header */}
                <Header user={user} onLogout={handleLogout} />

                {/* Main Content Area with Left Rail */}
                <div className="flex flex-1 overflow-hidden">
                  {/* Left Rail */}
                  <div className="relative h-full overflow-visible min-w-[24px]">
                    <LeftRail
                      onTableSelect={setSelectedTable}
                      selectedTable={selectedTable}
                      isCollapsed={isLeftRailCollapsed}
                      onToggleCollapse={() => setIsLeftRailCollapsed(!isLeftRailCollapsed)}
                    />
                  </div>

                  {/* Main Content */}
                  <main className="flex-1 overflow-y-auto">
                    <div className="max-w-7xl mx-auto p-6">
                      {selectedTable ? (
                        <div className="space-y-6">
                          <TableDataViewer tableName={selectedTable} />
                          <MetadataViewer tableName={selectedTable} />
                        </div>
                      ) : (
                        <div className="mt-20">
                          <EmptyState
                            icon={<Database className="h-16 w-16" />}
                            title="Welcome to Metadata Explorer"
                            description="Select a catalog, schema, and table from the left sidebar to explore data, view enriched metadata, and discover relationships"
                          />
                        </div>
                      )}
                    </div>
                  </main>
                </div>
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/enriched-tables"
          element={
            user ? (
              <div className="flex flex-col h-screen bg-background-light dark:bg-gray-900 transition-theme">
                {/* Header */}
                <Header user={user} onLogout={handleLogout} />

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto">
                  <div className="max-w-7xl mx-auto p-6">
                    <EnrichedTablesPage onEditMetadata={handleEditMetadata} />
                  </div>
                </main>

                {/* Metadata Edit Modal */}
                <MetadataEditModal
                  isOpen={editModalOpen}
                  onClose={handleCloseEditModal}
                  table={tableToEdit}
                />
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
