import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Login from "./components/Login";
import TableSelector from "./components/TableSelector";
import TableDataViewer from "./components/TableDataViewer";
import MetadataViewer from "./components/MetadataViewer";
import api from "./services/api";
import "./App.css";

function App() {
  const [selectedTable, setSelectedTable] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.log("Not authenticated");
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      setSelectedTable(null);
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            user ? (
              <Navigate to="/" />
            ) : (
              <Login onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        <Route
          path="/"
          element={
            user ? (
              <div className="app">
                <header className="app-header">
                  <div className="container">
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <h1 className="app-title">
                          <svg
                            className="app-icon"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                          Metadata Explorer
                        </h1>
                        <p className="app-subtitle">
                          Explore and manage table metadata with AI-powered
                          insights
                        </p>
                      </div>
                      <div className="user-info">
                        <span>
                          Welcome, {user.display_name || user.username}
                        </span>
                        <button
                          onClick={handleLogout}
                          className="logout-button"
                        >
                          Logout
                        </button>
                      </div>
                    </div>
                  </div>
                </header>

                <main className="app-main">
                  <div className="container">
                    <TableSelector
                      onTableSelect={setSelectedTable}
                      selectedTable={selectedTable}
                    />

                    {selectedTable && (
                      <>
                        <section className="section">
                          <TableDataViewer tableName={selectedTable} />
                        </section>
                        <section className="section">
                          <MetadataViewer tableName={selectedTable} />
                        </section>
                      </>
                    )}

                    {!selectedTable && (
                      <div className="empty-state">
                        <svg
                          className="empty-icon"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <h2>Get Started</h2>
                        <p>
                          Select a table from the dropdown above to view its
                          data and metadata
                        </p>
                      </div>
                    )}
                  </div>
                </main>

                <footer className="app-footer">
                  <div className="container">
                    <p>&copy; Semantic Layer. Internal tool.</p>
                  </div>
                </footer>
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
