/**
 * API Client for Metadata Explorer Backend
 */
import axios from "axios";

// Base URL for API - configure based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60 second timeout for long-running queries
});

// Request interceptor for adding auth token and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add bearer token to Authorization header
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(
      `[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`,
    );
    return response;
  },
  (error) => {
    console.error(
      "[API Response Error]",
      error.response?.data || error.message,
    );

    // Handle 401 errors by clearing token and redirecting to login
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      // Only redirect if not already on login page
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  },
);

/**
 * API Service
 */
const api = {
  // ========== Catalog Endpoints ==========

  /**
   * Login with username and password
   */
  login: async (username, password) => {
    const response = await apiClient.post("/api/auth/login", {
      username,
      password,
    });
    return response.data;
  },

  /**
   * Logout
   */
  logout: async () => {
    const response = await apiClient.post("/api/auth/logout");
    return response.data;
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    const response = await apiClient.get("/api/auth/me");
    return response.data;
  },
  /**
   * Get all available catalogs
   */
  getCatalogs: async () => {
    const response = await apiClient.get("/api/catalogs");
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
    const response = await apiClient.get(
      `/api/catalogs/${catalog}/schemas/${schema}/tables`,
    );
    return response.data;
  },

  // ========== Table Endpoints ==========

  /**
   * Get all tables WITH metadata (from DynamoDB only)
   */
  getTables: async () => {
    const response = await apiClient.get("/api/tables");
    return response.data;
  },

  /**
   * Get all enriched tables (tables with metadata)
   */
  getEnrichedTables: async () => {
    const response = await apiClient.get("/api/enriched-tables");
    return response.data;
  },

  /**
   * Get sample data from a table
   */
  getTableData: async (catalog, schema, tableName, limit = 1000) => {
    const response = await apiClient.get(
      `/api/table-data/${catalog}/${schema}/${tableName}`,
      {
        params: { limit },
      },
    );
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
    const response = await apiClient.get(
      `/api/metadata/${catalog}/${schema}/${tableName}`,
    );
    return response.data;
  },

  /**
   * Get only the relationship detection status for a table (lightweight)
   * @param {string} catalog - Catalog name
   * @param {string} schema - Schema name
   * @param {string} tableName - Table name
   */
  getRelationshipStatus: async (catalog, schema, tableName) => {
    const response = await apiClient.get(
      `/api/relationship-status/${catalog}/${schema}/${tableName}`,
    );
    return response.data;
  },

  /**
   * Refresh metadata for a table
   */
  refreshMetadata: async (catalog, schema, tableName) => {
    const response = await apiClient.post(
      `/api/refresh-metadata/${catalog}/${schema}/${tableName}`,
    );
    return response.data;
  },

  /**
   * Update column aliases
   */
  updateColumnAlias: async (
    catalog,
    schema,
    tableName,
    columnName,
    aliases,
  ) => {
    const response = await apiClient.patch(
      `/api/column/${catalog}/${schema}/${tableName}/${columnName}/alias`,
      { aliases },
    );
    return response.data;
  },

  /**
   * Update column metadata (description, column_type, semantic_type)
   */
  updateColumnMetadata: async (
    catalog,
    schema,
    tableName,
    columnName,
    updates,
  ) => {
    const response = await apiClient.patch(
      `/api/column/${catalog}/${schema}/${tableName}/${columnName}/metadata`,
      updates,
    );
    return response.data;
  },

  // ========== Relationship Endpoints ==========

  /**
   * Get relationships for a table
   * @param {string} catalog - Catalog name
   * @param {string} schema - Schema name
   * @param {string} tableName - Table name
   */
  getRelationships: async (catalog, schema, tableName) => {
    const response = await apiClient.get(
      `/api/relationships/${catalog}/${schema}/${tableName}`,
    );
    return response.data;
  },

  // ========== Admin Endpoints ==========

  /**
   * Generate metadata for tables
   */
  generateMetadata: async (
    tableName = null,
    catalog = "here_explorer",
    schema = "explorer_datasets",
    forceRefresh = false,
  ) => {
    const response = await apiClient.post(
      "/api/admin/generate-metadata",
      {
        table_name: tableName,
        force_refresh: forceRefresh,
      },
      {
        params: { catalog, schema },
      },
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

  // ========== Semantic Search Endpoints ==========

  /**
   * Perform semantic search using natural language query
   * @param {string} query - Natural language query
   * @param {number} threshold - Similarity threshold (0-1), default 0.40
   * @param {string} mode - Search mode ('analytics' or 'datamining'), default 'datamining'
   * @param {boolean} includeRelationships - Include relationships in response, default true
   */
  semanticSearch: async (query, threshold = 0.40, mode = 'datamining', includeRelationships = true) => {
    const response = await apiClient.post('/api/search/semantic', {
      query,
      threshold,
      mode,
      include_relationships: includeRelationships,
    });
    return response.data;
  },
};

export default api;
