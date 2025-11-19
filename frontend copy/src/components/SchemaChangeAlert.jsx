/**
 * SchemaChangeAlert Component
 * Displays alert when schema changes are detected
 */
import React from 'react';
import './SchemaChangeAlert.css';

const SchemaChangeAlert = ({ schemaChanges, onRefresh, refreshing }) => {
  if (!schemaChanges) return null;

  const { new_columns, removed_columns, type_changes } = schemaChanges;
  const hasChanges = new_columns?.length > 0 || removed_columns?.length > 0 || type_changes?.length > 0;

  if (!hasChanges) return null;

  return (
    <div className="schema-alert">
      <div className="alert-header">
        <svg className="alert-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="alert-title">Schema Changes Detected</h3>
      </div>

      <div className="alert-body">
        <p className="alert-message">
          The table structure has changed since metadata was last generated. 
          Please refresh to update the metadata.
        </p>

        <div className="changes-list">
          {new_columns?.length > 0 && (
            <div className="change-item">
              <span className="change-badge new">New Columns</span>
              <span className="change-value">{new_columns.join(', ')}</span>
            </div>
          )}

          {removed_columns?.length > 0 && (
            <div className="change-item">
              <span className="change-badge removed">Removed Columns</span>
              <span className="change-value">{removed_columns.join(', ')}</span>
            </div>
          )}

          {type_changes?.length > 0 && (
            <div className="change-item">
              <span className="change-badge modified">Type Changes</span>
              <span className="change-value">
                {type_changes.map((change, idx) => (
                  <span key={idx}>
                    {change.column}: {change.old_type} → {change.new_type}
                    {idx < type_changes.length - 1 && ', '}
                  </span>
                ))}
              </span>
            </div>
          )}
        </div>

        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="refresh-button"
        >
          {refreshing ? (
            <>
              <span className="spinner"></span>
              Refreshing...
            </>
          ) : (
            <>
              <svg className="refresh-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Metadata
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SchemaChangeAlert;