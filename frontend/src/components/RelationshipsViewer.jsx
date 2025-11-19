import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Link as LinkIcon, ArrowRight, Info } from 'lucide-react';
import { Card, Badge, Spinner } from './ui';

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
        `http://localhost:8000/api/relationships/${catalog}/${schema}/${tableName}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch relationships');
      }

      const data = await response.json();
      setRelationships(data);
    } catch (err) {
      console.error('Error fetching relationships:', err);
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

  const getTypeLabel = (type) => {
    switch (type) {
      case 'foreign_key':
        return 'Foreign Keys';
      case 'semantic':
        return 'Semantic';
      case 'name_based':
        return 'Name-Based';
      default:
        return 'Other';
    }
  };

  const getTypeVariant = (type) => {
    switch (type) {
      case 'foreign_key':
        return 'primary';
      case 'semantic':
        return 'info';
      case 'name_based':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'danger';
  };

  if (loading) {
    return (
      <Card className="mt-6">
        <div className="p-8 flex items-center justify-center">
          <Spinner size="md" />
          <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
            Loading relationships...
          </span>
        </div>
      </Card>
    );
  }

  if (error || !relationships || relationships.total_count === 0) {
    return null; // Don't show section if error or no relationships
  }

  return (
    <Card className="mt-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          )}
          <LinkIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <div className="text-left">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              Table Relationships
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Discovered relationships with other tables
            </p>
          </div>
        </div>
        <Badge variant="primary">{relationships.total_count} relationships</Badge>
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          <div className="p-6 space-y-6">
            {Object.entries(relationships.relationships_by_type).map(([type, rels]) => (
              <div key={type} className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={getTypeVariant(type)}>
                    {getTypeLabel(type)}
                  </Badge>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {rels.length} {rels.length === 1 ? 'relationship' : 'relationships'}
                  </span>
                </div>

                <div className="space-y-2">
                  {rels.map((rel) => {
                    const relId = rel.relationship_id;
                    const isRelExpanded = expandedRelationships.has(relId);

                    const isOutgoing = rel.source_table === relationships.table_name;
                    const displayColumn = isOutgoing ? rel.source_column : rel.target_column;
                    const relatedTable = isOutgoing ? rel.target_table : rel.source_table;
                    const relatedColumn = isOutgoing ? rel.target_column : rel.source_column;

                    return (
                      <div
                        key={relId}
                        className="bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
                      >
                        <button
                          onClick={() => toggleRelationship(relId)}
                          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <ArrowRight className={`h-4 w-4 flex-shrink-0 ${
                              isOutgoing
                                ? 'text-blue-600 dark:text-blue-400'
                                : 'text-green-600 dark:text-green-400 transform rotate-180'
                            }`} />
                            <div className="flex items-center gap-2 flex-1 min-w-0 text-sm">
                              <code className="font-mono text-gray-900 dark:text-gray-100 font-medium">
                                {displayColumn}
                              </code>
                              <ArrowRight className="h-3 w-3 text-gray-400 flex-shrink-0" />
                              <span className="text-gray-700 dark:text-gray-300 truncate">
                                {relatedTable}
                              </span>
                              <span className="text-gray-500 dark:text-gray-400">.</span>
                              <code className="font-mono text-gray-700 dark:text-gray-300 truncate">
                                {relatedColumn}
                              </code>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                            {rel.relationship_subtype && (
                              <Badge variant="default" size="sm">
                                {rel.relationship_subtype}
                              </Badge>
                            )}
                            <Badge variant={getConfidenceColor(rel.confidence)} size="sm">
                              {Math.round(rel.confidence * 100)}%
                            </Badge>
                            <ChevronDown
                              className={`h-4 w-4 text-gray-400 transition-transform ${
                                isRelExpanded ? '' : '-rotate-90'
                              }`}
                            />
                          </div>
                        </button>

                        {isRelExpanded && (
                          <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 space-y-3 text-sm">
                            <div>
                              <div className="flex items-start gap-2">
                                <Info className="h-4 w-4 text-primary-600 dark:text-primary-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                                    Reasoning:
                                  </p>
                                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                                    {rel.reasoning}
                                  </p>
                                </div>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-gray-600 dark:text-gray-400">
                              <div>
                                <span className="font-medium">Detected:</span>{' '}
                                {new Date(rel.detected_at).toLocaleString()}
                              </div>
                              <div>
                                <span className="font-medium">Method:</span>{' '}
                                <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                                  {rel.detected_by}
                                </code>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default RelationshipsViewer;
