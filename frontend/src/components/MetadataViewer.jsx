import React, { useState, useEffect } from 'react';
import ReactJson from 'react-json-view';
import {
  ChevronDown,
  ChevronRight,
  Check,
  X,
  Edit2,
  BarChart3,
  Sparkles,
  RefreshCw,
  Download,
  Copy,
} from 'lucide-react';
import api from '../services/api';
import { Card, Badge, Button, Spinner, EmptyState, Tooltip } from './ui';
import RelationshipsViewer from './RelationshipsViewer';

const truncateDescription = (description, maxLength = 150) => {
  if (!description) return 'No description available';
  if (description.length <= maxLength) {
    return description;
  }
  return description.substring(0, maxLength) + '...';
};

const simplifyDataType = (dataType) => {
  if (!dataType) return 'unknown';
  const lowerType = dataType.toLowerCase();

  if (lowerType.startsWith('row(') || lowerType.startsWith('struct<')) {
    return 'row/struct';
  }
  if (lowerType.startsWith('array<')) {
    const match = dataType.match(/^array<([^<>]+)>/i);
    if (match) {
      return `array<${match[1]}>`;
    }
    return 'array';
  }
  if (lowerType.startsWith('map<')) {
    return 'map';
  }
  if (dataType.length > 50) {
    return dataType.substring(0, 47) + '...';
  }
  return dataType;
};

const MetadataViewer = ({ tableName }) => {
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metadataNotFound, setMetadataNotFound] = useState(false);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [generationProgress, setGenerationProgress] = useState(null);

  // Relationship detection status (separate from main metadata generation)
  const [relationshipStatus, setRelationshipStatus] = useState(null);

  // Edit state
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  // Stats modal state
  const [statsModal, setStatsModal] = useState(null);

  // JSON view state
  const [jsonExpanded, setJsonExpanded] = useState(false);

  useEffect(() => {
    if (tableName) {
      fetchMetadata();
    }
  }, [tableName]);

  // Poll task status when generating
  useEffect(() => {
    if (taskId && generating) {
      const interval = setInterval(async () => {
        try {
          const status = await api.getTaskStatus(taskId);
          setGenerationProgress(status);

          if (status.status === 'completed') {
            setGenerating(false);
            setTaskId(null);
            setGenerationProgress(null);
            setTimeout(() => fetchMetadata(), 1000);
          } else if (status.status === 'failed') {
            setGenerating(false);
            setTaskId(null);
            setError(`Metadata generation failed: ${status.error || 'Unknown error'}`);
          }
        } catch (err) {
          console.error('Error polling task status:', err);
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [taskId, generating]);

  // Poll relationship detection status if in_progress
  useEffect(() => {
    if (relationshipStatus === 'in_progress' && tableName) {
      const interval = setInterval(async () => {
        try {
          const parts = tableName.split('.');
          if (parts.length !== 3) return;

          const [catalog, schema, table] = parts;
          const data = await api.getMetadata(catalog, schema, table);

          // Update relationship status
          const newStatus = data.relationship_detection_status || 'not_started';
          setRelationshipStatus(newStatus);

          // If completed or failed, stop polling
          if (newStatus === 'completed' || newStatus === 'failed') {
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error polling relationship status:', err);
        }
      }, 3000); // Poll every 3 seconds

      return () => clearInterval(interval);
    }
  }, [relationshipStatus, tableName]);

  const fetchMetadata = async () => {
    try {
      setLoading(true);
      setError(null);
      setMetadataNotFound(false);

      const parts = tableName.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid table name format. Expected: catalog.schema.table');
      }

      const [catalog, schema, table] = parts;
      const data = await api.getMetadata(catalog, schema, table);
      setMetadata(data);

      // Extract relationship detection status
      setRelationshipStatus(data.relationship_detection_status || 'not_started');
    } catch (err) {
      console.error('Error fetching metadata:', err);
      if (err.response?.status === 404) {
        setMetadataNotFound(true);
        setError('Metadata not found for this table.');
      } else {
        setError('Failed to load metadata. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMetadata = async () => {
    try {
      setGenerating(true);
      setError(null);

      const parts = tableName.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid table name format');
      }

      const [catalog, schema, table] = parts;
      const response = await api.generateMetadata(table, catalog, schema, true);
      setTaskId(response.task_id);
      setGenerationProgress({ status: 'queued', progress: 0 });
    } catch (err) {
      console.error('Error generating metadata:', err);
      setError('Failed to start metadata generation. Please try again.');
      setGenerating(false);
    }
  };

  const handleEditClick = (columnName, field, currentValue) => {
    setEditingCell({ columnName, field });
    setEditValue(currentValue || '');
  };

  const handleSaveEdit = async (columnName, field) => {
    try {
      setSaving(true);
      const parts = tableName.split('.');
      const [catalog, schema, table] = parts;

      if (field === 'aliases') {
        const aliases = editValue
          .split(',')
          .map((a) => a.trim())
          .filter((a) => a);
        await api.updateColumnAlias(catalog, schema, table, columnName, aliases);

        setMetadata((prev) => ({
          ...prev,
          columns: {
            ...prev.columns,
            [columnName]: {
              ...prev.columns[columnName],
              aliases: aliases,
            },
          },
        }));
      } else {
        const updates = { [field]: editValue === 'None' ? null : editValue };
        await api.updateColumnMetadata(catalog, schema, table, columnName, updates);

        setMetadata((prev) => ({
          ...prev,
          columns: {
            ...prev.columns,
            [columnName]: {
              ...prev.columns[columnName],
              [field]: editValue === 'None' ? null : editValue,
            },
          },
        }));
      }

      setEditingCell(null);
      setEditValue('');
    } catch (err) {
      console.error(`Error updating ${field}:`, err);
      alert(`Failed to update ${field}. Please try again.`);
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue('');
  };

  const handleOpenStats = (columnName, columnData) => {
    setStatsModal({ columnName, columnData });
  };

  const handleCloseStats = () => {
    setStatsModal(null);
  };

  const columnTypeOptions = [
    'dimension',
    'measure',
    'identifier',
    'timestamp',
    'detail',
  ];

  const semanticTypeOptions = [
    'country',
    'state',
    'city',
    'latitude',
    'longitude',
    'None',
    'wkt_geometry',
    'geojson_geometry',
    'geometry_type',
  ];

  // Render editable cell
  const renderEditableCell = (columnName, field, value, options = null) => {
    const isEditing =
      editingCell?.columnName === columnName && editingCell?.field === field;

    if (isEditing) {
      if (options) {
        return (
          <div className="flex items-center gap-1">
            <select
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="flex-1 px-2 py-1 text-sm border border-primary-500 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 bg-background-card dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              autoFocus
            >
              {options.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleSaveEdit(columnName, field)}
              className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
              disabled={saving}
            >
              <Check className="h-4 w-4" />
            </button>
            <button
              onClick={handleCancelEdit}
              className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      } else {
        return (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="flex-1 px-2 py-1 text-sm border border-primary-500 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 bg-background-card dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveEdit(columnName, field);
                if (e.key === 'Escape') handleCancelEdit();
              }}
            />
            <button
              onClick={() => handleSaveEdit(columnName, field)}
              className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
              disabled={saving}
            >
              <Check className="h-4 w-4" />
            </button>
            <button
              onClick={handleCancelEdit}
              className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      }
    }

    // Display mode
    let displayValue = value;
    if (field === 'aliases') {
      displayValue = Array.isArray(value) ? value.join(', ') : '';
    } else if (field === 'semantic_type' && !value) {
      displayValue = 'None';
    }

    return (
      <div className="group flex items-center justify-between gap-2">
        <span className="flex-1 min-w-0 truncate text-sm">{displayValue || '-'}</span>
        <button
          onClick={() =>
            handleEditClick(
              columnName,
              field,
              field === 'aliases'
                ? Array.isArray(value)
                  ? value.join(', ')
                  : ''
                : value || (field === 'semantic_type' ? 'None' : '')
            )
          }
          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 rounded transition-opacity"
          title="Edit"
        >
          <Edit2 className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  };

  // Loading state
  if (loading) {
    return (
      <Card className="mt-6">
        <div className="p-12">
          <div className="flex flex-col items-center justify-center">
            <Spinner size="lg" />
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              Loading metadata...
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Generating state
  if (generating) {
    return (
      <Card className="mt-6">
        <div className="p-12">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="mb-4">
              <Sparkles className="h-12 w-12 text-primary-600 dark:text-primary-400 animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Generating Metadata
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              {tableName}
            </p>

            {generationProgress && (
              <div className="w-full max-w-md space-y-3">
                <Badge variant="primary">{generationProgress.status}</Badge>
                {generationProgress.status === 'running' && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Processing columns...
                  </p>
                )}
                {generationProgress.total && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Progress</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {generationProgress.successful || 0} / {generationProgress.total}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-primary-600 dark:bg-primary-400 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${((generationProgress.successful || 0) / generationProgress.total) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            <p className="mt-6 text-xs text-gray-500 dark:text-gray-400">
              This may take a few minutes. You can wait here or come back later.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Metadata not found state
  if (metadataNotFound) {
    return (
      <Card className="mt-6">
        <div className="p-12">
          <EmptyState
            icon={<Sparkles className="h-16 w-16" />}
            title="Metadata Not Available"
            description={`Metadata has not been generated for ${tableName} yet. Click the button below to run an AI enrichment pipeline (may take a few minutes).`}
            action={
              <Button
                variant="primary"
                icon={<Sparkles className="h-4 w-4" />}
                onClick={handleGenerateMetadata}
              >
                Generate Metadata
              </Button>
            }
          />
          {error && (
            <p className="mt-4 text-center text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>
      </Card>
    );
  }

  // Error state
  if (error && !metadataNotFound) {
    return (
      <Card className="mt-6">
        <div className="p-12">
          <EmptyState
            icon={
              <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <X className="h-8 w-8 text-red-600 dark:text-red-400" />
              </div>
            }
            title="Error Loading Metadata"
            description={error}
            action={
              <Button variant="secondary" icon={<RefreshCw className="h-4 w-4" />} onClick={fetchMetadata}>
                Retry
              </Button>
            }
          />
        </div>
      </Card>
    );
  }

  // Empty state
  if (!metadata) {
    return (
      <Card className="mt-6">
        <div className="p-12">
          <EmptyState
            title="Select a table"
            description="Choose a catalog, schema, and table from the left sidebar to view its metadata"
          />
        </div>
      </Card>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Relationship Detection Status Banner */}
      {relationshipStatus === 'in_progress' && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <RefreshCw className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-spin" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Finding Relationships
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Discovering relationships between this table and all other enriched tables (~3-5 minutes).
                You can navigate away and come back later, or wait here to see results.
              </p>
            </div>
          </div>
        </div>
      )}

      {relationshipStatus === 'completed' && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-green-900 dark:text-green-100">
                Relationships Ready
              </h4>
              <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                Relationship detection completed successfully. See discovered relationships below.
              </p>
            </div>
          </div>
        </div>
      )}

      {relationshipStatus === 'failed' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <X className="h-5 w-5 text-red-600 dark:text-red-400" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-red-900 dark:text-red-100">
                Relationship Detection Failed
              </h4>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                An error occurred during relationship detection. You can regenerate metadata to retry.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header Card */}
      <Card>
        <Card.Header className="flex items-center justify-between">
          <div>
            <Card.Title>{metadata.catalog_schema_table}</Card.Title>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <strong>Last Updated:</strong>
                {new Date(metadata.last_updated).toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <strong>Rows:</strong>
                <Badge variant="info">{metadata.row_count?.toLocaleString() || 0}</Badge>
              </span>
              <span className="flex items-center gap-1">
                <strong>Columns:</strong>
                <Badge variant="info">
                  {metadata.column_count || Object.keys(metadata.columns).length}
                </Badge>
              </span>
            </div>
          </div>
          <Button
            variant="primary"
            size="sm"
            icon={<Sparkles className="h-4 w-4" />}
            onClick={handleGenerateMetadata}
          >
            Regenerate
          </Button>
        </Card.Header>

        {/* Metadata Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/50 border-y border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Column Name
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Data Type
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Column Type
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Semantic Type
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Aliases
                </th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-3 py-2.5 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Stats
                </th>
              </tr>
            </thead>
            <tbody className="bg-background-card dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {Object.entries(metadata.columns).map(([columnName, columnData], idx) => (
                <tr
                  key={columnName}
                  className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                    idx % 2 === 0 ? '' : 'bg-gray-50/50 dark:bg-gray-800/50'
                  }`}
                >
                  <td className="px-3 py-2.5 font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap">
                    {columnName}
                  </td>
                  <td className="px-3 py-2.5 text-gray-600 dark:text-gray-400" title={columnData.data_type}>
                    <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {simplifyDataType(columnData.data_type)}
                    </code>
                  </td>
                  <td className="px-3 py-2.5">
                    {renderEditableCell(
                      columnName,
                      'column_type',
                      columnData.column_type || 'dimension',
                      columnTypeOptions
                    )}
                  </td>
                  <td className="px-3 py-2.5">
                    {renderEditableCell(
                      columnName,
                      'semantic_type',
                      columnData.semantic_type,
                      semanticTypeOptions
                    )}
                  </td>
                  <td className="px-3 py-2.5 max-w-xs">
                    {renderEditableCell(columnName, 'aliases', columnData.aliases)}
                  </td>
                  <td className="px-3 py-2.5 max-w-md" title={columnData.description}>
                    {renderEditableCell(
                      columnName,
                      'description',
                      editingCell?.columnName === columnName && editingCell?.field === 'description'
                        ? columnData.description
                        : truncateDescription(columnData.description, 150)
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-center">
                    <button
                      onClick={() => handleOpenStats(columnName, columnData)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                    >
                      <BarChart3 className="h-3.5 w-3.5" />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Raw JSON View */}
        <Card.Footer>
          <button
            onClick={() => setJsonExpanded(!jsonExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            {jsonExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            View Raw JSON
          </button>
          {jsonExpanded && (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <ReactJson
                src={metadata}
                theme={document.documentElement.classList.contains('dark') ? 'monokai' : 'rjv-default'}
                collapsed={1}
                displayDataTypes={false}
                displayObjectSize={false}
                enableClipboard={true}
                name={false}
              />
            </div>
          )}
        </Card.Footer>
      </Card>

      {/* Stats Modal */}
      {statsModal && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseStats}
        >
          <div
            className="bg-background-card dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Statistics: {statsModal.columnName}
              </h3>
              <button
                onClick={handleCloseStats}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Data Type:</span>
                <code className="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                  {simplifyDataType(statsModal.columnData.data_type)}
                </code>
              </div>

              {statsModal.columnData.min_value !== null && statsModal.columnData.min_value !== undefined && (
                <>
                  <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Min Value:</span>
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {String(statsModal.columnData.min_value)}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Max Value:</span>
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {String(statsModal.columnData.max_value)}
                    </span>
                  </div>
                  {statsModal.columnData.avg_value !== null && statsModal.columnData.avg_value !== undefined && (
                    <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Average:</span>
                      <span className="text-sm text-gray-900 dark:text-gray-100">
                        {statsModal.columnData.avg_value.toFixed(2)}
                      </span>
                    </div>
                  )}
                </>
              )}

              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Cardinality:</span>
                <Badge variant="info">{statsModal.columnData.cardinality?.toLocaleString() || 0}</Badge>
              </div>

              <div className="flex justify-between py-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Null Percentage:</span>
                <Badge variant={statsModal.columnData.null_percentage > 50 ? 'warning' : 'success'}>
                  {statsModal.columnData.null_percentage || 0}%
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Relationships Section */}
      {tableName &&
        (() => {
          const parts = tableName.split('.');
          if (parts.length === 3) {
            const [catalog, schema, table] = parts;
            return <RelationshipsViewer catalog={catalog} schema={schema} tableName={table} />;
          }
          return null;
        })()}
    </div>
  );
};

export default MetadataViewer;
