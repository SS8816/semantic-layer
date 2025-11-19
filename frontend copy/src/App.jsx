/**
 * Main App Component
 */
import React, { useState } from 'react';
import TableSelector from './components/TableSelector';
import SchemaChangeAlert from './components/SchemaChangeAlert';
import TableDataViewer from './components/TableDataViewer';
import MetadataViewer from './components/MetadataViewer';
import api from './services/api';
import './App.css';

function App() {
  const [selectedTable, setSelectedTable] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleTableSelect = async (tableName) => {
    setSelectedTable(tableName);
    setMetadata(null);

    if (tableName) {
      try {
        const data = await api.getMetadata(tableName);
        setMetadata(data);
      } catch (err) {
        console.error('Error fetching metadata:', err);
      }
    }
  };

  const handleRefreshMetadata = async () => {
    if (!selectedTable) return;

    try {
      setRefreshing(true);
      await api.refreshMetadata(selectedTable);
      
      // Reload metadata after refresh
      const data = await api.getMetadata(selectedTable);
      setMetadata(data);
      
      alert('Metadata refreshed successfully!');
    } catch (err) {
      console.error('Error refreshing metadata:', err);
      alert('Failed to refresh metadata. Please try again.');
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="container">
          <h1 className="app-title">
            <svg className="app-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Metadata Explorer
          </h1>
          <p className="app-subtitle">
            Explore and manage table metadata with AI-powered insights
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          {/* Table Selector */}
          <TableSelector
            onTableSelect={handleTableSelect}
            selectedTable={selectedTable}
          />

          {selectedTable && (
            <>
              {/* Schema Change Alert */}
              {metadata?.schema_status === 'SCHEMA_CHANGED' && (
                <SchemaChangeAlert
                  schemaChanges={metadata.schema_changes}
                  onRefresh={handleRefreshMetadata}
                  refreshing={refreshing}
                />
              )}

              {/* Table Data Viewer */}
              <section className="section">
                <TableDataViewer tableName={selectedTable} />
              </section>

              {/* Metadata Viewer */}
              <section className="section">
                <MetadataViewer tableName={selectedTable} />
              </section>
            </>
          )}

          {!selectedTable && (
            <div className="empty-state">
              <svg className="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h2>Get Started</h2>
              <p>Select a table from the dropdown above to view its data and metadata</p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <p>&copy; 2025 Metadata Explorer. Internal tool.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;