/**
 * MetadataViewer Component
 * Displays table metadata in tabular format with inline editing and stats modal
 */
import React, { useState, useEffect } from "react";
import ReactJson from "react-json-view";
import api from "../services/api";
import "./MetadataViewer.css";
import RelationshipsViewer from "./RelationshipsViewer";

const truncateDescription = (description, maxLength = 150) => {
  if (!description) return "No description available";

  if (description.length <= maxLength) {
    return description;
  }

  return description.substring(0, maxLength) + "...";
};
// Helper function to simplify complex data types
const simplifyDataType = (dataType) => {
  if (!dataType) return "unknown";

  const lowerType = dataType.toLowerCase();

  // Simplify struct/row types
  if (lowerType.startsWith("row(") || lowerType.startsWith("struct<")) {
    return "row/struct";
  }

  // Simplify array types - keep just array<baseType>
  if (lowerType.startsWith("array<")) {
    const match = dataType.match(/^array<([^<>]+)>/i);
    if (match) {
      return `array<${match[1]}>`;
    }
    return "array";
  }

  // Simplify map types
  if (lowerType.startsWith("map<")) {
    return "map";
  }

  // Truncate if still too long
  if (dataType.length > 50) {
    return dataType.substring(0, 47) + "...";
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

  // Edit state
  const [editingCell, setEditingCell] = useState(null); // { columnName, field }
  const [editValue, setEditValue] = useState("");

  // Stats modal state
  const [statsModal, setStatsModal] = useState(null); // { columnName, columnData }

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
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [taskId, generating]);

  const fetchMetadata = async () => {
    try {
      setLoading(true);
      setError(null);
      setMetadataNotFound(false);

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

      const parts = tableName.split(".");
      if (parts.length !== 3) {
        throw new Error("Invalid table name format");
      }

      const [catalog, schema, table] = parts;
      const response = await api.generateMetadata(table, catalog, schema, true);
      setTaskId(response.task_id);
      setGenerationProgress({ status: "queued", progress: 0 });
    } catch (err) {
      console.error("Error generating metadata:", err);
      setError("Failed to start metadata generation. Please try again.");
      setGenerating(false);
    }
  };

  const handleEditClick = (columnName, field, currentValue) => {
    setEditingCell({ columnName, field });
    setEditValue(currentValue || "");
  };

  const handleSaveEdit = async (columnName, field) => {
    try {
      const parts = tableName.split(".");
      const [catalog, schema, table] = parts;

      if (field === "aliases") {
        const aliases = editValue
          .split(",")
          .map((a) => a.trim())
          .filter((a) => a);
        await api.updateColumnAlias(
          catalog,
          schema,
          table,
          columnName,
          aliases,
        );

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
        const updates = { [field]: editValue === "None" ? null : editValue };
        await api.updateColumnMetadata(
          catalog,
          schema,
          table,
          columnName,
          updates,
        );

        setMetadata((prev) => ({
          ...prev,
          columns: {
            ...prev.columns,
            [columnName]: {
              ...prev.columns[columnName],
              [field]: editValue === "None" ? null : editValue,
            },
          },
        }));
      }

      setEditingCell(null);
      setEditValue("");
    } catch (err) {
      console.error(`Error updating ${field}:`, err);
      alert(`Failed to update ${field}. Please try again.`);
    }
  };

  const handleCancelEdit = () => {
    setEditingCell(null);
    setEditValue("");
  };

  const handleOpenStats = (columnName, columnData) => {
    setStatsModal({ columnName, columnData });
  };

  const handleCloseStats = () => {
    setStatsModal(null);
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
    "wkt_geometry",
    "geojson_geometry",
    "geometry_type",
  ];

  // Render editable cell
  const renderEditableCell = (columnName, field, value, options = null) => {
    const isEditing =
      editingCell?.columnName === columnName && editingCell?.field === field;

    if (isEditing) {
      if (options) {
        return (
          <div className="inline-edit">
            <select
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="edit-select"
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
              className="save-btn"
            >
              ✓
            </button>
            <button onClick={handleCancelEdit} className="cancel-btn">
              ✗
            </button>
          </div>
        );
      } else {
        return (
          <div className="inline-edit">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="edit-input"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveEdit(columnName, field);
                if (e.key === "Escape") handleCancelEdit();
              }}
            />
            <button
              onClick={() => handleSaveEdit(columnName, field)}
              className="save-btn"
            >
              ✓
            </button>
            <button onClick={handleCancelEdit} className="cancel-btn">
              ✗
            </button>
          </div>
        );
      }
    }

    // Display mode
    let displayValue = value;
    if (field === "aliases") {
      displayValue = Array.isArray(value) ? value.join(", ") : "";
    } else if (field === "semantic_type" && !value) {
      displayValue = "None";
    }

    return (
      <div className="cell-content">
        <span className="cell-value">{displayValue || "-"}</span>
        <button
          onClick={() =>
            handleEditClick(
              columnName,
              field,
              field === "aliases"
                ? Array.isArray(value)
                  ? value.join(", ")
                  : ""
                : value || (field === "semantic_type" ? "None" : ""),
            )
          }
          className="edit-icon"
          title="Edit"
        >
          ✏️
        </button>
      </div>
    );
  };

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
        {/* Main Metadata Table */}
        <div className="metadata-table-container">
          <table className="metadata-table">
            <thead>
              <tr>
                <th>Column Name</th>
                <th>Data Type</th>
                <th>Column Type</th>
                <th>Semantic Type</th>
                <th>Aliases</th>
                <th>Description</th>
                <th>Stats</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metadata.columns).map(
                ([columnName, columnData]) => (
                  <tr key={columnName}>
                    {/* Column Name */}
                    <td className="col-name">{columnName}</td>

                    {/* Data Type */}
                    <td className="col-datatype" title={columnData.data_type}>
                      {simplifyDataType(columnData.data_type)}
                    </td>

                    {/* Column Type (editable) */}
                    <td className="col-type">
                      {renderEditableCell(
                        columnName,
                        "column_type",
                        columnData.column_type || "dimension",
                        columnTypeOptions,
                      )}
                    </td>

                    {/* Semantic Type (editable) */}
                    <td className="col-semantic">
                      {renderEditableCell(
                        columnName,
                        "semantic_type",
                        columnData.semantic_type,
                        semanticTypeOptions,
                      )}
                    </td>

                    {/* Aliases (editable) */}
                    <td className="col-aliases">
                      {renderEditableCell(
                        columnName,
                        "aliases",
                        columnData.aliases,
                      )}
                    </td>

                    {/* Description (editable) */}
                    <td
                      className="col-description"
                      title={columnData.description}
                    >
                      {renderEditableCell(
                        columnName,
                        "description",
                        editingCell?.column === columnName &&
                          editingCell?.field === "description"
                          ? columnData.description // Full text when editing
                          : truncateDescription(columnData.description, 150), // Truncated when viewing
                      )}
                    </td>

                    {/* Stats Button */}
                    <td className="col-stats-btn">
                      <button
                        onClick={() => handleOpenStats(columnName, columnData)}
                        className="stats-button"
                      >
                        Stats
                      </button>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
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

      {/* Stats Modal */}
      {statsModal && (
        <div className="stats-modal-overlay" onClick={handleCloseStats}>
          <div className="stats-modal" onClick={(e) => e.stopPropagation()}>
            <div className="stats-modal-header">
              <h3>Statistics: {statsModal.columnName}</h3>
              <button onClick={handleCloseStats} className="close-button">
                ✕
              </button>
            </div>
            <div className="stats-modal-body">
              <div className="stat-row">
                <span className="stat-label">Data Type:</span>
                <span
                  className="stat-value"
                  title={statsModal.columnData.data_type}
                >
                  {simplifyDataType(statsModal.columnData.data_type)}
                </span>
              </div>

              {statsModal.columnData.min_value !== null &&
                statsModal.columnData.min_value !== undefined && (
                  <>
                    <div className="stat-row">
                      <span className="stat-label">Min Value:</span>
                      <span className="stat-value">
                        {String(statsModal.columnData.min_value)}
                      </span>
                    </div>
                    <div className="stat-row">
                      <span className="stat-label">Max Value:</span>
                      <span className="stat-value">
                        {String(statsModal.columnData.max_value)}
                      </span>
                    </div>
                    {statsModal.columnData.avg_value !== null &&
                      statsModal.columnData.avg_value !== undefined && (
                        <div className="stat-row">
                          <span className="stat-label">Average:</span>
                          <span className="stat-value">
                            {statsModal.columnData.avg_value.toFixed(2)}
                          </span>
                        </div>
                      )}
                  </>
                )}

              <div className="stat-row">
                <span className="stat-label">Cardinality:</span>
                <span className="stat-value">
                  {statsModal.columnData.cardinality?.toLocaleString() || 0}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Null Percentage:</span>
                <span className="stat-value">
                  {statsModal.columnData.null_percentage || 0}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Relationships Section */}
      {tableName &&
        (() => {
          const parts = tableName.split(".");
          if (parts.length === 3) {
            const [catalog, schema, table] = parts;
            return (
              <RelationshipsViewer
                catalog={catalog}
                schema={schema}
                tableName={table}
              />
            );
          }
          return null;
        })()}
    </div>
  );
};

export default MetadataViewer;
