import React, { useState, useEffect } from 'react';
import { Search, Edit2, AlertCircle, CheckCircle2, Filter } from 'lucide-react';
import { Card, Badge, Spinner, EmptyState } from './ui';
import api from '../services/api';

const EnrichedTablesPage = ({ onEditMetadata }) => {
  const [tables, setTables] = useState([]);
  const [filteredTables, setFilteredTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCatalog, setSelectedCatalog] = useState('');
  const [selectedSchema, setSelectedSchema] = useState('');

  // Unique catalogs and schemas for filters
  const [catalogs, setCatalogs] = useState([]);
  const [schemas, setSchemas] = useState([]);

  useEffect(() => {
    fetchEnrichedTables();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [tables, searchTerm, selectedCatalog, selectedSchema]);

  const fetchEnrichedTables = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEnrichedTables();
      setTables(data.tables || []);

      // Extract unique catalogs and schemas
      const uniqueCatalogs = [...new Set(data.tables.map(t => t.catalog))];
      setCatalogs(uniqueCatalogs);

      const uniqueSchemas = [...new Set(data.tables.map(t => t.schema))];
      setSchemas(uniqueSchemas);
    } catch (err) {
      console.error('Failed to fetch enriched tables:', err);
      setError(err.response?.data?.detail || 'Failed to load enriched tables');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...tables];

    // Apply catalog filter
    if (selectedCatalog) {
      filtered = filtered.filter(t => t.catalog === selectedCatalog);
    }

    // Apply schema filter
    if (selectedSchema) {
      filtered = filtered.filter(t => t.schema === selectedSchema);
    }

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(
        t =>
          t.table_name.toLowerCase().includes(search) ||
          t.catalog.toLowerCase().includes(search) ||
          t.schema.toLowerCase().includes(search)
      );
    }

    setFilteredTables(filtered);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CURRENT':
        return (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Current
          </Badge>
        );
      case 'CHANGED':
        return (
          <Badge variant="warning" size="sm">
            <AlertCircle className="h-3 w-3 mr-1" />
            Schema Changed
          </Badge>
        );
      default:
        return (
          <Badge variant="default" size="sm">
            {status}
          </Badge>
        );
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleEdit = (table) => {
    onEditMetadata(table);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading enriched tables...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <EmptyState
          icon={<AlertCircle className="h-16 w-16 text-red-500" />}
          title="Error Loading Tables"
          description={error}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Enriched Tables
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          View and manage all tables with enriched metadata
        </p>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Tables
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, catalog, or schema..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Catalog Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Filter by Catalog
              </label>
              <select
                value={selectedCatalog}
                onChange={(e) => setSelectedCatalog(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Catalogs</option>
                {catalogs.map((catalog) => (
                  <option key={catalog} value={catalog}>
                    {catalog}
                  </option>
                ))}
              </select>
            </div>

            {/* Schema Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Filter by Schema
              </label>
              <select
                value={selectedSchema}
                onChange={(e) => setSelectedSchema(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Schemas</option>
                {schemas.map((schema) => (
                  <option key={schema} value={schema}>
                    {schema}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Results count */}
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            Showing {filteredTables.length} of {tables.length} tables
          </div>
        </div>
      </Card>

      {/* Tables */}
      {filteredTables.length === 0 ? (
        <EmptyState
          icon={<Filter className="h-16 w-16" />}
          title="No Tables Found"
          description="Try adjusting your filters or search term"
        />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Catalog
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Schema
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Table Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Columns
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredTables.map((table) => (
                  <tr
                    key={table.full_name}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {table.catalog}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {table.schema}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {table.table_name}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(table.last_updated)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getStatusBadge(table.schema_status)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {table.column_count}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleEdit(table)}
                        className="inline-flex items-center px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                      >
                        <Edit2 className="h-3.5 w-3.5 mr-1.5" />
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default EnrichedTablesPage;
