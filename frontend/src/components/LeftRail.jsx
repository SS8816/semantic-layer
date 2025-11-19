import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import TableSelector from './TableSelector';
import { Button } from './ui';

const LeftRail = ({ onTableSelect, selectedTable, isCollapsed, onToggleCollapse }) => {
  return (
    <>
      {/* Collapse/Expand Button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-4 z-10 p-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full shadow-md hover:shadow-lg transition-all"
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        ) : (
          <ChevronLeft className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        )}
      </button>

      {/* Left Rail Content */}
      <aside
        className={`
          flex-shrink-0 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700
          transition-all duration-300 ease-in-out overflow-hidden
          ${isCollapsed ? 'w-0' : 'w-80'}
        `}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide">
              Table Browser
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Select a catalog, schema, and table to explore
            </p>
          </div>

          {/* Table Selector */}
          <div className="flex-1 overflow-y-auto p-4">
            <TableSelector
              onTableSelect={onTableSelect}
              selectedTable={selectedTable}
            />
          </div>
        </div>
      </aside>
    </>
  );
};

export default LeftRail;
