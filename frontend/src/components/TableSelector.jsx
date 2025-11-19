import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import { Database, Table, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';
import { Badge } from './ui';

const TableSelector = ({ onTableSelect, selectedTable }) => {
  const [catalogs, setCatalogs] = useState([]);
  const [selectedCatalog, setSelectedCatalog] = useState('here_explorer');

  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState('explorer_datasets');

  const [tables, setTables] = useState([]);
  const [tablesWithMetadata, setTablesWithMetadata] = useState(new Map());

  const [loadingCatalogs, setLoadingCatalogs] = useState(false);
  const [loadingSchemas, setLoadingSchemas] = useState(false);
  const [loadingTables, setLoadingTables] = useState(false);

  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCatalogs();
  }, []);

  useEffect(() => {
    if (selectedCatalog) {
      fetchSchemas();
    }
  }, [selectedCatalog]);

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
      const data = await api.getTables();
      const metadataMap = new Map();

      data.tables
        .filter(t => t.catalog_schema_table.startsWith(`${selectedCatalog}.${selectedSchema}.`))
        .forEach(t => {
          metadataMap.set(t.name, {
            lastUpdated: t.last_updated,
            schemaStatus: t.schema_status,
            hasMetadata: true
          });
        });

      setTablesWithMetadata(metadataMap);
    } catch (err) {
      console.error('Error fetching tables with metadata:', err);
    }
  };

  // Custom styles for react-select with dark mode
  const customStyles = {
    control: (provided, state) => ({
      ...provided,
      minHeight: '42px',
      backgroundColor: 'transparent',
      borderColor: state.isFocused ? '#0ea5e9' : '#d1d5db',
      boxShadow: state.isFocused ? '0 0 0 2px rgba(14, 165, 233, 0.1)' : 'none',
      '&:hover': {
        borderColor: '#0ea5e9',
      },
    }),
    input: (provided) => ({
      ...provided,
      color: 'inherit',
    }),
    singleValue: (provided) => ({
      ...provided,
      color: 'inherit',
    }),
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
      backgroundColor: 'white',
      border: '1px solid #e5e7eb',
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? '#0ea5e9'
        : state.isFocused
        ? '#f3f4f6'
        : 'white',
      color: state.isSelected ? 'white' : '#1f2937',
      cursor: 'pointer',
      padding: '10px 12px',
    }),
  };

  // Dark mode styles
  const darkModeStyles = {
    ...customStyles,
    menu: (provided) => ({
      ...provided,
      zIndex: 9999,
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? '#0ea5e9'
        : state.isFocused
        ? '#374151'
        : '#1f2937',
      color: state.isSelected ? 'white' : '#f3f4f6',
    }),
  };

  // Detect dark mode
  const isDarkMode = document.documentElement.classList.contains('dark');
  const selectStyles = isDarkMode ? darkModeStyles : customStyles;

  // Format options with icons
  const catalogOptions = catalogs.map((catalog) => ({
    value: catalog,
    label: catalog,
  }));

  const schemaOptions = schemas.map((schema) => ({
    value: schema,
    label: schema,
  }));

  const tableOptions = tables.map((tableName) => {
    const metadata = tablesWithMetadata.get(tableName);
    return {
      value: `${selectedCatalog}.${selectedSchema}.${tableName}`,
      label: tableName,
      hasMetadata: metadata?.hasMetadata || false,
      schemaStatus: metadata?.schemaStatus,
      lastUpdated: metadata?.lastUpdated,
    };
  });

  // Custom option renderer
  const formatTableOptionLabel = ({ label, hasMetadata, schemaStatus }) => (
    <div className="flex items-center justify-between gap-2 w-full">
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <Table className="h-4 w-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
        <span className="truncate text-sm">{label}</span>
      </div>
      <div className="flex items-center gap-1 flex-shrink-0">
        {hasMetadata && (
          <Badge variant="enriched" size="sm">
            <CheckCircle className="h-3 w-3" />
          </Badge>
        )}
        {schemaStatus === 'SCHEMA_CHANGED' && (
          <Badge variant="stale" size="sm">
            <AlertCircle className="h-3 w-3" />
          </Badge>
        )}
      </div>
    </div>
  );

  const selectedCatalogOption = catalogOptions.find((opt) => opt.value === selectedCatalog);
  const selectedSchemaOption = schemaOptions.find((opt) => opt.value === selectedSchema);
  const selectedTableOption = tableOptions.find((opt) => opt.value === selectedTable);

  return (
    <div className="space-y-4">
      {/* Catalog Selector */}
      <div className="space-y-2">
        <label
          htmlFor="catalog-select"
          className="block text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide"
        >
          <Database className="inline h-3 w-3 mr-1" />
          Catalog
        </label>
        <Select
          id="catalog-select"
          options={catalogOptions}
          value={selectedCatalogOption}
          onChange={(option) => {
            setSelectedCatalog(option?.value || 'here_explorer');
            setSelectedSchema('');
            onTableSelect(null);
          }}
          placeholder={loadingCatalogs ? 'Loading...' : 'Select catalog...'}
          isLoading={loadingCatalogs}
          isSearchable
          styles={selectStyles}
        />
      </div>

      {/* Schema Selector */}
      <div className="space-y-2">
        <label
          htmlFor="schema-select"
          className="block text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide"
        >
          Schema
        </label>
        <Select
          id="schema-select"
          options={schemaOptions}
          value={selectedSchemaOption}
          onChange={(option) => {
            setSelectedSchema(option?.value || '');
            onTableSelect(null);
          }}
          placeholder={loadingSchemas ? 'Loading...' : 'Select schema...'}
          isLoading={loadingSchemas}
          isSearchable
          isDisabled={!selectedCatalog}
          styles={selectStyles}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Table Selector */}
      <div className="space-y-2">
        <label
          htmlFor="table-select"
          className="block text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide"
        >
          <Table className="inline h-3 w-3 mr-1" />
          Table
        </label>
        <Select
          id="table-select"
          options={tableOptions}
          value={selectedTableOption}
          onChange={(option) => onTableSelect(option?.value)}
          placeholder={loadingTables ? 'Loading...' : 'Search and select a table...'}
          isLoading={loadingTables}
          isSearchable
          isClearable
          isDisabled={!selectedCatalog || !selectedSchema}
          formatOptionLabel={formatTableOptionLabel}
          styles={selectStyles}
        />
      </div>

      {/* Table Count and Stats */}
      {tables.length > 0 && (
        <div className="pt-2 space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
            <span>{tables.length} tables total</span>
            {tablesWithMetadata.size > 0 && (
              <Badge variant="enriched" size="sm">
                {tablesWithMetadata.size} enriched
              </Badge>
            )}
          </div>

          {/* Legend */}
          <div className="pt-2 border-t border-gray-200 dark:border-gray-700 space-y-1">
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Legend:</p>
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-1">
                <Badge variant="enriched" size="sm">
                  <CheckCircle className="h-3 w-3" />
                </Badge>
                <span className="text-xs text-gray-600 dark:text-gray-400">Enriched</span>
              </div>
              <div className="flex items-center gap-1">
                <Badge variant="stale" size="sm">
                  <AlertCircle className="h-3 w-3" />
                </Badge>
                <span className="text-xs text-gray-600 dark:text-gray-400">Schema Changed</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableSelector;
