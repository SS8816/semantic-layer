/**
 * TableDataViewer Component
 * Displays sample data from the selected table
 */
import React, { useState, useEffect } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from "@tanstack/react-table";
import api from "../services/api";
import "./TableDataViewer.css";

const TableDataViewer = ({ tableName }) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [limit] = useState(100); // Show 100 rows by default

  useEffect(() => {
    if (tableName) {
      fetchTableData();
    }
  }, [tableName]);

  const fetchTableData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Parse the 3-part table name
      const parts = tableName.split(".");
      if (parts.length !== 3) {
        throw new Error(
          "Invalid table name format. Expected: catalog.schema.table",
        );
      }

      const [catalog, schema, table] = parts;

      // Call API with 3 separate parameters
      const response = await api.getTableData(catalog, schema, table, limit);

      // Convert data to proper format
      const formattedData = response.data.map((row, idx) => {
        const rowObj = { _row_id: idx };
        response.columns.forEach((col, colIdx) => {
          rowObj[col] = row[colIdx];
        });
        return rowObj;
      });

      // Create column definitions
      const columnDefs = response.columns.map((col) => ({
        accessorKey: col,
        header: col,
        cell: (info) => {
          const value = info.getValue();
          // Format null values
          if (value === null || value === undefined) {
            return <span className="null-value">NULL</span>;
          }
          // Truncate long strings
          if (typeof value === "string" && value.length > 50) {
            return <span title={value}>{value.substring(0, 50)}...</span>;
          }
          return value;
        },
      }));

      setColumns(columnDefs);
      setData(formattedData);
    } catch (err) {
      console.error("Error fetching table data:", err);
      setError("Failed to load table data. Please try again.");
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
    return (
      <div className="table-data-viewer empty">
        <p>Select a table to view data</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="table-data-viewer loading">
        <div className="loader"></div>
        <p>Loading table data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="table-data-viewer error">
        <p>{error}</p>
        <button onClick={fetchTableData} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="table-data-viewer">
      <div className="viewer-header">
        <h2 className="viewer-title">Table Data</h2>
        <span className="row-count">
          Showing {data.length} of {data.length} rows
        </span>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id}>
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TableDataViewer;
