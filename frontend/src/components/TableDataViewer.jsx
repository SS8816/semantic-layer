import React, { useState, useEffect } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from '@tanstack/react-table';
import { ChevronDown, ChevronRight, Database, MapPin, Calendar, Hash, Type, Globe } from 'lucide-react';
import api from '../services/api';
import { Card, Spinner, Badge } from './ui';

// Get semantic icon based on column name patterns
const getColumnIcon = (columnName) => {
  const lowerName = columnName.toLowerCase();

  if (lowerName.includes('lat') || lowerName.includes('lon') || lowerName.includes('coord') || lowerName.includes('geometry')) {
    return <MapPin className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />;
  }
  if (lowerName.includes('date') || lowerName.includes('time') || lowerName.includes('timestamp')) {
    return <Calendar className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />;
  }
  if (lowerName.includes('id') || lowerName.includes('key') || lowerName.includes('uuid')) {
    return <Hash className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />;
  }
  if (lowerName.includes('country') || lowerName.includes('city') || lowerName.includes('state') || lowerName.includes('region')) {
    return <Globe className="h-3.5 w-3.5 text-orange-600 dark:text-orange-400" />;
  }

  return <Type className="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />;
};

const TableDataViewer = ({ tableName, metadata }) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [limit] = useState(100);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (tableName && isExpanded) {
      fetchTableData();
    }
  }, [tableName, isExpanded]);

  const fetchTableData = async () => {
    try {
      setLoading(true);
      setError(null);

      const parts = tableName.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid table name format. Expected: catalog.schema.table');
      }

      const [catalog, schema, table] = parts;
      const response = await api.getTableData(catalog, schema, table, limit);

      const formattedData = response.data.map((row, idx) => {
        const rowObj = { _row_id: idx };
        response.columns.forEach((col, colIdx) => {
          rowObj[col] = row[colIdx];
        });
        return rowObj;
      });

      const columnDefs = response.columns.map((col) => ({
        accessorKey: col,
        header: col,
        cell: (info) => {
          const value = info.getValue();
          if (value === null || value === undefined) {
            return <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded text-xs font-mono">NULL</span>;
          }
          if (typeof value === 'string' && value.length > 50) {
            return <span title={value} className="cursor-help">{value.substring(0, 50)}...</span>;
          }
          return value;
        },
      }));

      setColumns(columnDefs);
      setData(formattedData);
    } catch (err) {
      console.error('Error fetching table data:', err);
      setError('Failed to load table data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (!tableName) {
    return null;
  }

  return (
    <Card className="transition-theme">
      {/* Header */}
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
          <Database className="h-5 w-5 text-primary-600 dark:text-primary-400" />
          <div className="text-left">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              Sample Data
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              View first {limit} rows from the table
            </p>
          </div>
        </div>
        {!isExpanded && data.length > 0 && (
          <Badge variant="primary">{data.length} rows loaded</Badge>
        )}
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {loading && (
            <div className="p-12 flex flex-col items-center justify-center">
              <Spinner size="lg" />
              <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">Loading table data...</p>
            </div>
          )}

          {error && (
            <div className="p-6 text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 mb-3">
                <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <p className="text-sm text-red-600 dark:text-red-400 mb-4">{error}</p>
              <button
                onClick={fetchTableData}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <>
              <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Showing <span className="font-semibold text-gray-900 dark:text-gray-100">{data.length}</span> rows
                </span>
                <Badge variant="info">{columns.length} columns</Badge>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                    {table.getHeaderGroups().map((headerGroup) => (
                      <tr key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <th
                            key={header.id}
                            className="px-4 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap"
                          >
                            <div className="flex items-center gap-2">
                              {getColumnIcon(header.column.columnDef.header)}
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                            </div>
                          </th>
                        ))}
                      </tr>
                    ))}
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {table.getRowModel().rows.map((row, idx) => (
                      <tr
                        key={row.id}
                        className={`hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                          idx % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50/50 dark:bg-gray-800/50'
                        }`}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <td
                            key={cell.id}
                            className="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                          >
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </Card>
  );
};

export default TableDataViewer;
