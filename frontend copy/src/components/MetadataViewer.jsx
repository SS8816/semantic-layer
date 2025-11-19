/**
 * MetadataViewer Component
 * Displays table metadata with editing capabilities and auto-generation
 */
import React, { useState, useEffect } from "react";
import ReactJson from "react-json-view";
import api from "../services/api";
import AliasEditor from "./AliasEditor";
import "./MetadataViewer.css";

const MetadataViewer = ({ tableName }) => {
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metadataNotFound, setMetadataNotFound] = useState(false);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [generationProgress, setGenerationProgress] = useState(null);

  // Edit state
  const [editingColumn, setEditingColumn] = useState(null);
  const [editingDescription, setEditingDescription] = useState(null);
  const [editingColumnType, setEditingColumnType] = useState(null);
  const [editingSemanticType, setEditingSemanticType] = useState(null);

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

          if (status.status === "completed") {
            setGenerating(false);
            setTaskId(null);
            setGenerationProgress(null);
            // Fetch the newly generated metadata
            setTimeout(() => fetchMetadata(), 1000);
          } else if (status.status === "failed") {
            setGenerating(false);
            setTaskId(null);
            setError(
              `Metadata generation failed: ${status.error || "Unknown error"}`,
            );
          }
        } catch (err) {
          console.error("Error polling task status:", err);
        }
      }, 2000); // Poll every 2 seconds

      return () => clearInterval(interval);
    }
  }, [taskId, generating]);

  const fetchMetadata = async () => {
    try {
      setLoading(true);
      setError(null);
      setMetadataNotFound(false);

      // Parse catalog.schema.table from tableName
      const parts = tableName.split(".");
      if (parts.length !== 3) {
        throw new Error(
          "Invalid table name format. Expected: catalog.schema.table",
        );
      }

      const [catalog, schema, table] = parts;
      const data = await api.getMetadata(catalog, schema, table);
      setMetadata(data);
    } catch (err) {
      console.error("Error fetching metadata:", err);
      if (err.response?.status === 404) {
        setMetadataNotFound(true);
        setError("Metadata not found for this table.");
      } else {
        setError("Failed to load metadata. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMetadata = async () => {
    try {
      setGenerating(true);
      setError(null);

      // Parse catalog.schema.table
      const parts = tableName.split(".");
      if (parts.length !== 3) {
        throw new Error("Invalid table name format");
      }

      const [catalog, schema, table] = parts;

      // Start metadata generation
      const response = await api.generateMetadata(table, catalog, schema, true);
      setTaskId(response.task_id);
      setGenerationProgress({ status: "queued", progress: 0 });
    } catch (err) {
      console.error("Error generating metadata:", err);
      setError("Failed to start metadata generation. Please try again.");
      setGenerating(false);
    }
  };

  const handleEditAliases = (columnName) => {
    setEditingColumn(columnName);
  };

  const handleSaveAliases = async (columnName, newAliases) => {
    try {
      const parts = tableName.split(".");
      const [catalog, schema, table] = parts;

      await api.updateColumnAlias(
        catalog,
        schema,
        table,
        columnName,
        newAliases,
      );

      setMetadata((prev) => ({
        ...prev,
        columns: {
          ...prev.columns,
          [columnName]: {
            ...prev.columns[columnName],
            aliases: newAliases,
          },
        },
      }));

      setEditingColumn(null);
    } catch (err) {
      console.error("Error updating aliases:", err);
      alert("Failed to update aliases. Please try again.");
    }
  };

  const handleEditDescription = (columnName) => {
    setEditingDescription(columnName);
  };

  const handleSaveDescription = async (columnName, newDescription) => {
    try {
      const parts = tableName.split(".");
      const [catalog, schema, table] = parts;

      await api.updateColumnMetadata(catalog, schema, table, columnName, {
        description: newDescription,
      });

      setMetadata((prev) => ({
        ...prev,
        columns: {
          ...prev.columns,
          [columnName]: {
            ...prev.columns[columnName],
            description: newDescription,
          },
        },
      }));

      setEditingDescription(null);
    } catch (err) {
      console.error("Error updating description:", err);
      alert("Failed to update description. Please try again.");
    }
  };

  const handleEditColumnType = (columnName) => {
    setEditingColumnType(columnName);
  };

  const handleSaveColumnType = async (columnName, newColumnType) => {
    try {
      const parts = tableName.split(".");
      const [catalog, schema, table] = parts;

      await api.updateColumnMetadata(catalog, schema, table, columnName, {
        column_type: newColumnType,
      });

      setMetadata((prev) => ({
        ...prev,
        columns: {
          ...prev.columns,
          [columnName]: {
            ...prev.columns[columnName],
            column_type: newColumnType,
          },
        },
      }));

      setEditingColumnType(null);
    } catch (err) {
      console.error("Error updating column type:", err);
      alert("Failed to update column type. Please try again.");
    }
  };

  const handleEditSemanticType = (columnName) => {
    setEditingSemanticType(columnName);
  };

  const handleSaveSemanticType = async (columnName, newSemanticType) => {
    try {
      const parts = tableName.split(".");
      const [catalog, schema, table] = parts;

      await api.updateColumnMetadata(catalog, schema, table, columnName, {
        semantic_type: newSemanticType || null,
      });

      setMetadata((prev) => ({
        ...prev,
        columns: {
          ...prev.columns,
          [columnName]: {
            ...prev.columns[columnName],
            semantic_type: newSemanticType || null,
          },
        },
      }));

      setEditingSemanticType(null);
    } catch (err) {
      console.error("Error updating semantic type:", err);
      alert("Failed to update semantic type. Please try again.");
    }
  };

  if (!tableName) {
    return (
      <div className="metadata-viewer empty">
        <p>Select a table to view metadata</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="metadata-viewer loading">
        <div className="loader"></div>
        <p>Loading metadata...</p>
      </div>
    );
  }

  // Show generation UI
  if (generating) {
    return (
      <div className="metadata-viewer generating">
        <div className="generation-container">
          <div className="loader"></div>
          <h2>Generating Metadata...</h2>
          <p className="table-name">{tableName}</p>

          {generationProgress && (
            <div className="generation-status">
              <p className="status-text">
                Status: <strong>{generationProgress.status}</strong>
              </p>
              {generationProgress.status === "running" && (
                <p className="progress-text">Processing columns...</p>
              )}
              {generationProgress.total && (
                <p className="stats-text">
                  Progress: {generationProgress.successful || 0} /{" "}
                  {generationProgress.total} columns
                </p>
              )}
            </div>
          )}

          <p className="generation-note">
            This may take a few minutes. You can wait here or come back later.
          </p>
        </div>
      </div>
    );
  }

  // Show "Generate Metadata" button if not found
  if (metadataNotFound) {
    return (
      <div className="metadata-viewer not-found">
        <div className="not-found-container">
          <h2>Metadata Not Available</h2>
          <p className="table-name">{tableName}</p>
          <p className="message">
            Metadata has not been generated for this table yet.
          </p>
          <button onClick={handleGenerateMetadata} className="generate-button">
            Generate Metadata Now
          </button>
          {error && <p className="error-text">{error}</p>}
        </div>
      </div>
    );
  }

  if (error && !metadataNotFound) {
    return (
      <div className="metadata-viewer error">
        <p>{error}</p>
        <button onClick={fetchMetadata} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!metadata) {
    return null;
  }

  const columnTypeOptions = [
    "dimension",
    "measure",
    "identifier",
    "timestamp",
    "detail",
  ];
  const semanticTypeOptions = [
    "country",
    "state",
    "city",
    "latitude",
    "longitude",
    "None",
  ];

  return (
    <div className="metadata-viewer">
      <div className="viewer-header">
        <h2 className="viewer-title">{metadata.catalog_schema_table}</h2>
        <div className="header-info">
          <span className="info-item">
            <strong>Last Updated:</strong>{" "}
            {new Date(metadata.last_updated).toLocaleString()}
          </span>
          <span className="info-item">
            <strong>Row Count:</strong>{" "}
            {metadata.row_count?.toLocaleString() || 0}
          </span>
          <span className="info-item">
            <strong>Columns:</strong>{" "}
            {metadata.column_count || Object.keys(metadata.columns).length}
          </span>
        </div>
      </div>

      <div className="metadata-content">
        {/* Column-by-column view with editing */}
        <div className="columns-list">
          {Object.entries(metadata.columns).map(([columnName, columnData]) => (
            <div key={columnName} className="column-card">
              <div className="column-header">
                <h3 className="column-name">{columnName}</h3>
                <span className="column-type">{columnData.data_type}</span>
              </div>

              <div className="column-body">
                {/* Column Type (editable) */}
                <div className="metadata-row">
                  <span className="metadata-label">Column Type:</span>
                  {editingColumnType === columnName ? (
                    <div className="inline-editor">
                      <select
                        value={columnData.column_type || "dimension"}
                        onChange={(e) =>
                          handleSaveColumnType(columnName, e.target.value)
                        }
                        className="type-select"
                        autoFocus
                      >
                        {columnTypeOptions.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => setEditingColumnType(null)}
                        className="cancel-button"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="editable-field">
                      <span
                        className={`type-badge type-${columnData.column_type || "dimension"}`}
                      >
                        {columnData.column_type || "dimension"}
                      </span>
                      <button
                        onClick={() => handleEditColumnType(columnName)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>

                {/* Semantic Type (editable) */}
                <div className="metadata-row">
                  <span className="metadata-label">Semantic Type:</span>
                  {editingSemanticType === columnName ? (
                    <div className="inline-editor">
                      <select
                        value={columnData.semantic_type || "None"}
                        onChange={(e) => {
                          const value =
                            e.target.value === "None" ? null : e.target.value;
                          handleSaveSemanticType(columnName, value);
                        }}
                        className="type-select"
                        autoFocus
                      >
                        {semanticTypeOptions.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => setEditingSemanticType(null)}
                        className="cancel-button"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="editable-field">
                      {columnData.semantic_type ? (
                        <span
                          className={`semantic-badge semantic-${columnData.semantic_type}`}
                        >
                          {columnData.semantic_type}
                        </span>
                      ) : (
                        <span className="no-data">None</span>
                      )}
                      <button
                        onClick={() => handleEditSemanticType(columnName)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>

                {/* Aliases (editable) */}
                <div className="metadata-row">
                  <span className="metadata-label">Aliases:</span>
                  {editingColumn === columnName ? (
                    <AliasEditor
                      aliases={columnData.aliases || []}
                      onSave={(newAliases) =>
                        handleSaveAliases(columnName, newAliases)
                      }
                      onCancel={() => setEditingColumn(null)}
                    />
                  ) : (
                    <div className="aliases-display">
                      {columnData.aliases?.length > 0 ? (
                        columnData.aliases.map((alias, idx) => (
                          <span key={idx} className="alias-badge">
                            {alias}
                          </span>
                        ))
                      ) : (
                        <span className="no-data">No aliases</span>
                      )}
                      <button
                        onClick={() => handleEditAliases(columnName)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>

                {/* Description (editable) */}
                <div className="metadata-row">
                  <span className="metadata-label">Description:</span>
                  {editingDescription === columnName ? (
                    <div className="description-editor">
                      <textarea
                        defaultValue={columnData.description || ""}
                        className="description-textarea"
                        autoFocus
                        onBlur={(e) => {
                          if (e.target.value !== columnData.description) {
                            handleSaveDescription(columnName, e.target.value);
                          } else {
                            setEditingDescription(null);
                          }
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Escape") {
                            setEditingDescription(null);
                          }
                          if (e.key === "Enter" && e.ctrlKey) {
                            e.target.blur();
                          }
                        }}
                      />
                      <div className="editor-hint">
                        Press Ctrl+Enter to save, Esc to cancel
                      </div>
                    </div>
                  ) : (
                    <div className="editable-field">
                      <span className="metadata-value">
                        {columnData.description || "No description"}
                      </span>
                      <button
                        onClick={() => handleEditDescription(columnName)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>

                {/* Statistics */}
                {columnData.min_value !== null &&
                  columnData.min_value !== undefined && (
                    <div className="metadata-row">
                      <span className="metadata-label">Statistics:</span>
                      <div className="stats-display">
                        <span>Min: {columnData.min_value}</span>
                        <span>Max: {columnData.max_value}</span>
                        {columnData.avg_value !== null && (
                          <span>Avg: {columnData.avg_value.toFixed(2)}</span>
                        )}
                      </div>
                    </div>
                  )}

                <div className="metadata-row">
                  <span className="metadata-label">Cardinality:</span>
                  <span className="metadata-value">
                    {columnData.cardinality?.toLocaleString() || 0}
                  </span>
                </div>

                <div className="metadata-row">
                  <span className="metadata-label">Null %:</span>
                  <span className="metadata-value">
                    {columnData.null_percentage || 0}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Raw JSON view (collapsible) */}
        <details className="json-view">
          <summary>View Raw JSON</summary>
          <div className="json-container">
            <ReactJson
              src={metadata}
              theme="rjv-default"
              collapsed={1}
              displayDataTypes={false}
              displayObjectSize={false}
              enableClipboard={true}
              name={false}
            />
          </div>
        </details>
      </div>
    </div>
  );
};

export default MetadataViewer;
