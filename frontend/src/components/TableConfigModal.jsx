import React, { useState, useEffect } from 'react';
import { X, Settings } from 'lucide-react';
import { Button } from './ui';
import api from '../services/api';

const TableConfigModal = ({ isOpen, onClose, table, onSave }) => {
  const [searchMode, setSearchMode] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && table) {
      setSearchMode(table.search_mode || '');
      setCustomInstructions(table.custom_instructions || '');
      setError(null);
    }
  }, [isOpen, table]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      // Handle different table object formats
      let catalog, schema, tableName;

      if (table.catalog_schema_table) {
        // From MetadataViewer - has catalog_schema_table field
        const parts = table.catalog_schema_table.split('.');
        if (parts.length !== 3) {
          throw new Error('Invalid table name format');
        }
        [catalog, schema, tableName] = parts;
      } else if (table.catalog && table.schema && table.table_name) {
        // From EnrichedTablesPage - has separate fields
        catalog = table.catalog;
        schema = table.schema;
        tableName = table.table_name;
      } else {
        throw new Error('Invalid table object format');
      }

      await api.updateTableConfig(catalog, schema, tableName, {
        search_mode: searchMode || null,
        custom_instructions: customInstructions || null,
      });

      // Notify parent to refresh
      if (onSave) {
        await onSave();
      }

      onClose();
    } catch (err) {
      console.error('Error saving table config:', err);
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !table) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div
        className="bg-background-card dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Settings className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Table Configuration
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {table.catalog_schema_table || `${table.catalog}.${table.schema}.${table.table_name}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Search Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search Mode
            </label>
            <select
              value={searchMode}
              onChange={(e) => setSearchMode(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            >
              <option value="">🔍 Auto-detected (based on schema)</option>
              <option value="analytics">📊 Analytics (table-level search)</option>
              <option value="datamining">⛏️ Data Mining (column-level search)</option>
            </select>
            <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
              Auto-detection: nested types → Data Mining, flat schema → Analytics
            </p>
          </div>

          {/* Custom Instructions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Custom Instructions
            </label>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="Enter SQL examples, usage hints, or LLM instructions...&#10;&#10;Example:&#10;- Use this table for POI analysis&#10;- Always join with location_dim on location_id&#10;- For aggregations, use admin_level_2 as grouping key"
              rows={6}
              className="w-full px-4 py-3 rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm font-mono transition-colors"
            />
            <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
              Provide guidance for SQL generation and LLM usage
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TableConfigModal;
