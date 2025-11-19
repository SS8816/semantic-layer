/**
 * TableSelector Component
 */
import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import api from '../services/api';
import './TableSelector.css';

const TableSelector = ({ onTableSelect, selectedTable }) => {
  const [catalogs, setCatalogs] = useState([]);
  const [selectedCatalog, setSelectedCatalog] = useState('here_explorer');
  
  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState('explorer_datasets');
  
  const [tables, setTables] = useState([]);
  const [tablesWithMetadata, setTablesWithMetadata] = useState(new Set());
  
  const [loadingCatalogs, setLoadingCatalogs] = useState(false);
  const [loadingSchemas, setLoadingSchemas] = useState(false);
  const [loadingTables, setLoadingTables] = useState(false);
  
  const [error, setError] = useState(null);

  // Fetch catalogs on mount
  useEffect(() => {
    fetchCatalogs();
  }, []);

  // Fetch schemas when catalog changes
  useEffect(() => {
    if (selectedCatalog) {
      fetchSchemas();
    }
  }, [selectedCatalog]);

  // Fetch tables when schema changes
  useEffect(() => {
    if (selectedCatalog && selectedSchema) {
      fetchTables();
      fetchTablesWithMetadata();
    }
  }, [selectedCatalog, selectedSchema]);

  const fetchCatalogs = async () => {
    try {
      setLoadingCatalogs(true);
      setError(null);
      const data = await api.getCatalogs();
      setCatalogs(data.catalogs || []);
    } catch (err) {
      console.error('Error fetching catalogs:', err);
      setError('Failed to load catalogs.');
    } finally {
      setLoadingCatalogs(false);
    }
  };

  const fetchSchemas = async () => {
    try {
      setLoadingSchemas(true);
      setError(null);
      const data = await api.getSchemasInCatalog(selectedCatalog);
      setSchemas(data.schemas || []);
    } catch (err) {
      console.error('Error fetching schemas:', err);
      setError('Failed to load schemas.');
    } finally {
      setLoadingSchemas(false);
    }
  };

  const fetchTables = async () => {
    try {
      setLoadingTables(true);
      setError(null);
      
      // Get ALL tables from Starburst (not filtered by DynamoDB)
      const data = await api.getTablesInSchema(selectedCatalog, selectedSchema);
      setTables(data.tables || []);
      
    } catch (err) {
      console.error('Error fetching tables:', err);
      setError('Failed to load tables. Please try again.');
    } finally {
      setLoadingTables(false);
    }
  };

  const fetchTablesWithMetadata = async () => {
    try {
      // Get tables that have metadata in DynamoDB
      const data = await api.getTables();
      const metadataSet = new Set(
        data.tables
          .filter(t => t.catalog_schema_table.startsWith(`${selectedCatalog}.${selectedSchema}.`))
          .map(t => t.name)
      );
      setTablesWithMetadata(metadataSet);
    } catch (err) {
      console.error('Error fetching tables with metadata:', err);
      // Don't set error - this is optional
    }
  };

  // Format catalogs for react-select
  const catalogOptions = catalogs.map((catalog) => ({
    value: catalog,
    label: catalog,
  }));

  // Format schemas for react-select
  const schemaOptions = schemas.map((schema) => ({
    value: schema,
    label: schema,
  }));

  // Format tables for react-select
  const tableOptions = tables.map((tableName) => ({
    value: `${selectedCatalog}.${selectedSchema}.${tableName}`,
    label: tableName,
    hasMetadata: tablesWithMetadata.has(tableName),
  }));

  // Custom option renderer to show metadata status
  const formatTableOptionLabel = ({ label, hasMetadata }) => (
    <div className="table-option">
      <span className="table-name">{label}</span>
      {hasMetadata && (
        <span className="metadata-badge">Has Metadata</span>
      )}
    </div>
  );

  const customStyles = {
    control: (provided) => ({
      ...provided,
      minHeight: '45px',
      borderColor: '#d1d5db',
      boxShadow: 'none',
      '&:hover': {
        borderColor: '#9ca3af',
      },
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
    }),
  };

  const selectedCatalogOption = catalogOptions.find((opt) => opt.value === selectedCatalog);
  const selectedSchemaOption = schemaOptions.find((opt) => opt.value === selectedSchema);
  const selectedTableOption = tableOptions.find((opt) => opt.value === selectedTable);

  return (
    <div className="table-selector">
      {/* Catalog Selector */}
      <div className="selector-group">
        <label htmlFor="catalog-select" className="selector-label">
          Catalog
        </label>
        <Select
          id="catalog-select"
          options={catalogOptions}
          value={selectedCatalogOption}
          onChange={(option) => {
            setSelectedCatalog(option?.value || 'here_explorer');
            setSelectedSchema(''); // Reset schema
            onTableSelect(null); // Clear table selection
          }}
          placeholder={loadingCatalogs ? 'Loading catalogs...' : 'Select catalog...'}
          isLoading={loadingCatalogs}
          isSearchable
          styles={customStyles}
          className="catalog-select"
          classNamePrefix="catalog-select"
        />
      </div>

      {/* Schema Selector */}
      <div className="selector-group">
        <label htmlFor="schema-select" className="selector-label">
          Schema
        </label>
        <Select
          id="schema-select"
          options={schemaOptions}
          value={selectedSchemaOption}
          onChange={(option) => {
            setSelectedSchema(option?.value || '');
            onTableSelect(null); // Clear table selection
          }}
          placeholder={loadingSchemas ? 'Loading schemas...' : 'Select schema...'}
          isLoading={loadingSchemas}
          isSearchable
          isDisabled={!selectedCatalog}
          styles={customStyles}
          className="schema-select"
          classNamePrefix="schema-select"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={fetchTables} className="retry-button">
            Retry
          </button>
        </div>
      )}

      {/* Table Selector */}
      <div className="selector-group">
        <label htmlFor="table-select" className="selector-label">
          Table
        </label>
        <Select
          id="table-select"
          options={tableOptions}
          value={selectedTableOption}
          onChange={(option) => onTableSelect(option?.value)}
          placeholder={loadingTables ? 'Loading tables...' : 'Search and select a table...'}
          isLoading={loadingTables}
          isSearchable
          isClearable
          isDisabled={!selectedCatalog || !selectedSchema}
          formatOptionLabel={formatTableOptionLabel}
          styles={customStyles}
          className="table-select"
          classNamePrefix="table-select"
        />
      </div>

      {/* Table Count */}
      {tables.length > 0 && (
        <div className="table-count">
          {tables.length} tables in {selectedCatalog}.{selectedSchema}
          {tablesWithMetadata.size > 0 && (
            <span className="metadata-count"> ({tablesWithMetadata.size} with metadata)</span>
          )}
        </div>
      )}
    </div>
  );
};

export default TableSelector;