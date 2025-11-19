/**
 * API Client for Metadata Explorer Backend
 */
import axios from 'axios';

// Base URL for API - configure based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for long-running queries
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    console.error('[API Response Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * API Service
 */
const api = {
  // ========== Catalog Endpoints ==========
  
  /**
   * Get all available catalogs
   */
  getCatalogs: async () => {
    const response = await apiClient.get('/api/catalogs');
    return response.data;
  },

  /**
   * Get schemas in a specific catalog
   */
  getSchemasInCatalog: async (catalog) => {
    const response = await apiClient.get(`/api/catalogs/${catalog}/schemas`);
    return response.data;
  },

  /**
   * Get tables in a specific catalog.schema (from Starburst - ALL tables)
   */
  getTablesInSchema: async (catalog, schema) => {
    const response = await apiClient.get(`/api/catalogs/${catalog}/schemas/${schema}/tables`);
    return response.data;
  },

  // ========== Table Endpoints ==========
  
  /**
   * Get all tables WITH metadata (from DynamoDB only)
   */
  getTables: async () => {
    const response = await apiClient.get('/api/tables');
    return response.data;
  },

  /**
   * Get sample data from a table
   */
  getTableData: async (catalog, schema, tableName, limit = 1000) => {
    const response = await apiClient.get(`/api/table-data/${catalog}/${schema}/${tableName}`, {
      params: { limit },
    });
    return response.data;
  },

  // ========== Metadata Endpoints ==========

  /**
   * Get complete metadata for a table
   * @param {string} catalog - Catalog name
   * @param {string} schema - Schema name  
   * @param {string} tableName - Table name
   */
  getMetadata: async (catalog, schema, tableName) => {
    const response = await apiClient.get(`/api/metadata/${catalog}/${schema}/${tableName}`);
    return response.data;
  },

  /**
   * Refresh metadata for a table
   */
  refreshMetadata: async (catalog, schema, tableName) => {
    const response = await apiClient.post(`/api/refresh-metadata/${catalog}/${schema}/${tableName}`);
    return response.data;
  },

  /**
   * Update column aliases
   */
  updateColumnAlias: async (catalog, schema, tableName, columnName, aliases) => {
    const response = await apiClient.patch(
      `/api/column/${catalog}/${schema}/${tableName}/${columnName}/alias`,
      { aliases }
    );
    return response.data;
  },

  /**
   * Update column metadata (description, column_type, semantic_type)
   */
  updateColumnMetadata: async (catalog, schema, tableName, columnName, updates) => {
    const response = await apiClient.patch(
      `/api/column/${catalog}/${schema}/${tableName}/${columnName}/metadata`,
      updates
    );
    return response.data;
  },

  // ========== Admin Endpoints ==========

  /**
   * Generate metadata for tables
   */
  generateMetadata: async (tableName = null, catalog = 'here_explorer', schema = 'explorer_datasets', forceRefresh = false) => {
    const response = await apiClient.post('/api/admin/generate-metadata', 
      {
        table_name: tableName,
        force_refresh: forceRefresh,
      },
      {
        params: { catalog, schema },
      }
    );
    return response.data;
  },

  /**
   * Get task status
   */
  getTaskStatus: async (taskId) => {
    const response = await apiClient.get(`/api/admin/task-status/${taskId}`);
    return response.data;
  },
};

export default api;