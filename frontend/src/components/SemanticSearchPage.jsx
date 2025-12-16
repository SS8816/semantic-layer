import React, { useState, useEffect } from 'react';
import { Search, Database, AlertCircle, CheckCircle2, Loader2, FileText, Link as LinkIcon, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { Card, Badge, Spinner, EmptyState, Button } from './ui';
import api from '../services/api';

const SemanticSearchPage = () => {
  const [importedTables, setImportedTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search state
  const [query, setQuery] = useState('');
  const [threshold, setThreshold] = useState(0.40);
  const [mode, setMode] = useState('datamining'); // 'analytics' or 'datamining'
  const [includeRelationships, setIncludeRelationships] = useState(true);
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);

  // Collapsible sections state
  const [relationshipsCollapsed, setRelationshipsCollapsed] = useState(false);
  const [metadataCollapsed, setMetadataCollapsed] = useState(false);
  const [jsonBlobCollapsed, setJsonBlobCollapsed] = useState(true);

  // Copy state
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchImportedTables();
  }, []);

  const fetchImportedTables = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEnrichedTables();

      // Filter only imported tables
      const imported = (data.tables || []).filter(
        table => table.neptune_import_status === 'imported'
      );
      setImportedTables(imported);
    } catch (err) {
      console.error('Failed to fetch tables:', err);
      setError(err.response?.data?.detail || 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!query.trim()) {
      setSearchError('Please enter a search query');
      return;
    }

    try {
      setSearching(true);
      setSearchError(null);
      setSearchResults(null);

      const results = await api.semanticSearch(query, threshold, mode, includeRelationships);
      setSearchResults(results);

      if (results.query_too_vague) {
        setSearchError('No results found. Try a different query or lower the threshold.');
      }
    } catch (err) {
      console.error('Search failed:', err);
      setSearchError(err.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const copyToClipboard = () => {
    if (searchResults) {
      const jsonBlob = {
        relationships: searchResults.relationships,
        metadata: searchResults.metadata
      };
      navigator.clipboard.writeText(JSON.stringify(jsonBlob, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadge = (status) => {
    return (
      <Badge variant="success" size="sm">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        Searchable
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading searchable tables...</p>
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
          Semantic Search
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Search tables and columns using natural language queries powered by Neptune Analytics
        </p>
      </div>

      {/* Searchable Tables Section */}
      <Card>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Searchable Tables ({importedTables.length})
            </h2>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Tables that have been imported to Neptune and are available for semantic search
          </p>
        </div>

        <div className="p-4">
          {importedTables.length === 0 ? (
            <EmptyState
              icon={<Database className="h-12 w-12" />}
              title="No Searchable Tables"
              description="Generate metadata and wait for tables to be imported to Neptune Analytics"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {importedTables.map((table, index) => (
                <div
                  key={index}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                        {table.table_name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {table.catalog}.{table.schema}
                      </p>
                    </div>
                    {getStatusBadge(table.neptune_import_status)}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <div>
                      <span className="font-medium">Rows:</span> {table.row_count.toLocaleString()}
                    </div>
                    <div>
                      <span className="font-medium">Columns:</span> {table.column_count}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Search Input Section */}
      <Card>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Natural Language Query
            </h2>
          </div>
        </div>

        <div className="p-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Query
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Find geographic data, identifier columns, timestamp fields..."
                className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400"
                disabled={searching || importedTables.length === 0}
              />
            </div>

            {/* Search Mode Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Mode
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMode('analytics')}
                  disabled={searching}
                  className={`flex-1 px-4 py-2 rounded-lg border font-medium transition-colors ${
                    mode === 'analytics'
                      ? 'bg-primary-500 text-white border-primary-500'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-primary-400'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  Analytics
                  <span className="block text-xs font-normal opacity-80">Table-level search</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMode('datamining')}
                  disabled={searching}
                  className={`flex-1 px-4 py-2 rounded-lg border font-medium transition-colors ${
                    mode === 'datamining'
                      ? 'bg-primary-500 text-white border-primary-500'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-primary-400'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  Data Mining
                  <span className="block text-xs font-normal opacity-80">Column-level search</span>
                </button>
              </div>
            </div>

            {/* Include Relationships Toggle */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="includeRelationships"
                checked={includeRelationships}
                onChange={(e) => setIncludeRelationships(e.target.checked)}
                disabled={searching}
                className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
              <label htmlFor="includeRelationships" className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
                Include relationships in results
              </label>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Similarity Threshold: {threshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="-1.0"
                  max="0.95"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-full"
                  disabled={searching}
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>All results (-1.0)</span>
                  <span>Exact match (0.95)</span>
                </div>
              </div>

              <Button
                type="submit"
                disabled={searching || importedTables.length === 0 || !query.trim()}
                className="mt-6"
              >
                {searching ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </form>

          {searchError && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-400">{searchError}</p>
            </div>
          )}
        </div>
      </Card>

      {/* Search Results */}
      {searchResults && !searchResults.query_too_vague && (
        <div className="space-y-6">
          {/* Relationships Section */}
          <Card>
            <div
              className="p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={() => setRelationshipsCollapsed(!relationshipsCollapsed)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Relationships ({searchResults.relationships.length})
                  </h2>
                </div>
                {relationshipsCollapsed ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronUp className="h-5 w-5 text-gray-500" />
                )}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Detected relationships between matched tables
              </p>
            </div>

            {!relationshipsCollapsed && (
              <div className="p-4">
                {searchResults.relationships.length === 0 ? (
                  <p className="text-sm text-gray-600 dark:text-gray-400 text-center py-4">
                    No relationships found between matched tables
                  </p>
                ) : (
                  <div className="space-y-3">
                    {searchResults.relationships.map((rel, index) => (
                      <div
                        key={index}
                        className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                              <span className="truncate">{rel.source_table.split('.').pop()}.{rel.source_column}</span>
                              <span className="text-gray-400">→</span>
                              <span className="truncate">{rel.target_table.split('.').pop()}.{rel.target_column}</span>
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="default" size="sm">
                                {rel.relationship_type}
                              </Badge>
                              {rel.relationship_subtype && (
                                <Badge variant="info" size="sm">
                                  {rel.relationship_subtype}
                                </Badge>
                              )}
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {(rel.confidence * 100).toFixed(0)}% confidence
                              </span>
                            </div>
                          </div>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                          {rel.reasoning}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Detected by: {rel.detected_by}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Metadata Section */}
          <Card>
            <div
              className="p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={() => setMetadataCollapsed(!metadataCollapsed)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Metadata
                  </h2>
                </div>
                {metadataCollapsed ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronUp className="h-5 w-5 text-gray-500" />
                )}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Tables: {searchResults.metadata.tables.length} | Columns: {searchResults.metadata.columns.length}
              </p>
            </div>

            {!metadataCollapsed && (
              <div className="p-4 space-y-6">
              {/* Tables */}
              {searchResults.metadata.tables.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    Matched Tables ({searchResults.metadata.tables.length})
                  </h3>
                  <div className="space-y-3">
                    {searchResults.metadata.tables.map((table, index) => (
                      <div
                        key={index}
                        className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {table.catalog_schema_table.split('.').pop()}
                            </h4>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {table.catalog_schema_table}
                            </p>
                          </div>
                          <Badge variant="info" size="sm">
                            Similarity: {(table.similarity_score * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600 dark:text-gray-400 mt-3">
                          <div>
                            <span className="font-medium">Rows:</span> {table.row_count.toLocaleString()}
                          </div>
                          <div>
                            <span className="font-medium">Columns:</span> {table.column_count}
                          </div>
                          <div>
                            <span className="font-medium">Enrichment:</span> {table.enrichment_status}
                          </div>
                          <div>
                            <span className="font-medium">Neptune:</span> {table.neptune_import_status}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Columns */}
              {searchResults.metadata.columns.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    Matched Columns ({searchResults.metadata.columns.length})
                  </h3>
                  <div className="space-y-3">
                    {searchResults.metadata.columns.map((column, index) => (
                      <div
                        key={index}
                        className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                {column.column_name}
                              </h4>
                              <Badge variant="default" size="sm">
                                {column.column_type}
                              </Badge>
                              {column.semantic_type && (
                                <Badge variant="info" size="sm">
                                  {column.semantic_type}
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {column.catalog_schema_table} • {column.data_type}
                            </p>
                          </div>
                          <Badge variant="info" size="sm">
                            {(column.similarity_score * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                          {column.description}
                        </p>
                        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600 dark:text-gray-400">
                          {column.min_value !== null && (
                            <div>
                              <span className="font-medium">Min:</span> {column.min_value}
                            </div>
                          )}
                          {column.max_value !== null && (
                            <div>
                              <span className="font-medium">Max:</span> {column.max_value}
                            </div>
                          )}
                          {column.avg_value !== null && (
                            <div>
                              <span className="font-medium">Avg:</span> {column.avg_value.toFixed(2)}
                            </div>
                          )}
                          <div>
                            <span className="font-medium">Nulls:</span> {column.null_percentage.toFixed(1)}%
                          </div>
                        </div>
                        {column.aliases && column.aliases.length > 0 && (
                          <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                            <span className="font-medium">Aliases:</span> {column.aliases.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              </div>
            )}
          </Card>

          {/* JSON Response Section */}
          <Card>
            <div
              className="p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={() => setJsonBlobCollapsed(!jsonBlobCollapsed)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    JSON Response
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      copyToClipboard();
                    }}
                    className="text-xs"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3 w-3 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                  {jsonBlobCollapsed ? (
                    <ChevronDown className="h-5 w-5 text-gray-500" />
                  ) : (
                    <ChevronUp className="h-5 w-5 text-gray-500" />
                  )}
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Complete search response (relationships and metadata)
              </p>
            </div>

            {!jsonBlobCollapsed && (
              <div className="p-4">
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-xs text-gray-800 dark:text-gray-200 font-mono whitespace-pre-wrap">
                    {JSON.stringify(
                      {
                        relationships: searchResults.relationships,
                        metadata: searchResults.metadata
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};

export default SemanticSearchPage;
