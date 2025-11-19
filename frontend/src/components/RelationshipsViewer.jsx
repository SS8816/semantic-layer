/**
 * RelationshipsViewer Component
 * Displays table relationships in a collapsible section below metadata
 */
import React, { useState, useEffect } from "react";
import "./RelationshipsViewer.css";

const RelationshipsViewer = ({ catalog, schema, tableName }) => {
  const [relationships, setRelationships] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedRelationships, setExpandedRelationships] = useState(new Set());

  useEffect(() => {
    fetchRelationships();
  }, [catalog, schema, tableName]);

  const fetchRelationships = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `http://localhost:8000/api/relationships/${catalog}/${schema}/${tableName}`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch relationships");
      }

      const data = await response.json();
      setRelationships(data);
    } catch (err) {
      console.error("Error fetching relationships:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleRelationship = (relId) => {
    const newExpanded = new Set(expandedRelationships);
    if (newExpanded.has(relId)) {
      newExpanded.delete(relId);
    } else {
      newExpanded.add(relId);
    }
    setExpandedRelationships(newExpanded);
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "foreign_key":
        return "";
      case "semantic":
        return "";
      case "name_based":
        return "";
      default:
        return "";
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case "foreign_key":
        return "Foreign Keys";
      case "semantic":
        return "Semantic";
      case "name_based":
        return "Name-Based";
      default:
        return "Other";
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return "confidence-high";
    if (confidence >= 0.75) return "confidence-medium";
    return "confidence-low";
  };

  if (loading) {
    return (
      <div className="relationships-container">
        <div className="relationships-loading">Loading relationships...</div>
      </div>
    );
  }

  if (error) {
    return null; // Don't show anything if error (table might not have relationships)
  }

  if (!relationships || relationships.total_count === 0) {
    return null; // Don't show section if no relationships
  }

  return (
    <div className="relationships-container">
      <div
        className="relationships-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="relationships-title">
          <span className="relationships-icon"></span>
          <span className="relationships-text">
            Relationships Found ({relationships.total_count})
          </span>
        </div>
        <button className="relationships-toggle">
          {isExpanded ? "▼" : "▶"}
        </button>
      </div>

      {isExpanded && (
        <div className="relationships-content">
          {Object.entries(relationships.relationships_by_type).map(
            ([type, rels]) => (
              <div key={type} className="relationship-type-group">
                <div className="relationship-type-header">
                  <span className="type-icon">{getTypeIcon(type)}</span>
                  <span className="type-label">{getTypeLabel(type)}</span>
                  <span className="type-count">({rels.length})</span>
                </div>

                <div className="relationship-list">
                  {rels.map((rel) => {
                    const relId = rel.relationship_id;
                    const isRelExpanded = expandedRelationships.has(relId);

                    // Determine if this is outgoing or incoming
                    const isOutgoing =
                      rel.source_table === relationships.table_name;
                    const displayColumn = isOutgoing
                      ? rel.source_column
                      : rel.target_column;
                    const relatedTable = isOutgoing
                      ? rel.target_table
                      : rel.source_table;
                    const relatedColumn = isOutgoing
                      ? rel.target_column
                      : rel.source_column;
                    const direction = isOutgoing ? "→" : "←";

                    return (
                      <div key={relId} className="relationship-item">
                        <div
                          className="relationship-summary"
                          onClick={() => toggleRelationship(relId)}
                        >
                          <div className="relationship-path">
                            <span className="column-name">{displayColumn}</span>
                            <span className="relationship-arrow">
                              {direction}
                            </span>
                            <span className="related-table">
                              {relatedTable}
                            </span>
                            <span className="related-column">
                              .{relatedColumn}
                            </span>
                          </div>

                          <div className="relationship-meta">
                            {rel.relationship_subtype && (
                              <span className="relationship-subtype">
                                {rel.relationship_subtype}
                              </span>
                            )}
                            <span
                              className={`confidence-badge ${getConfidenceColor(rel.confidence)}`}
                            >
                              {Math.round(rel.confidence * 100)}%
                            </span>
                            <button className="expand-button">
                              {isRelExpanded ? "−" : "+"}
                            </button>
                          </div>
                        </div>

                        {isRelExpanded && (
                          <div className="relationship-details">
                            <div className="detail-row">
                              <strong>Reasoning:</strong>
                              <p>{rel.reasoning}</p>
                            </div>
                            <div className="detail-row">
                              <strong>Detected:</strong>
                              <span>
                                {new Date(rel.detected_at).toLocaleString()}
                              </span>
                            </div>
                            <div className="detail-row">
                              <strong>Method:</strong>
                              <span>{rel.detected_by}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ),
          )}
        </div>
      )}
    </div>
  );
};

export default RelationshipsViewer;
