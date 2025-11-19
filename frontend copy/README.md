# Metadata Explorer - Frontend

React-based frontend application for the Metadata Explorer project. Provides a clean, minimalistic, and functional interface for exploring table data and metadata.

## Features

- 🔍 **Searchable Table Selector**: Quickly find and select tables
- 📊 **Table Data Viewer**: View sample data from selected tables
- 📋 **Metadata Viewer**: Explore detailed column metadata
- ✏️ **Alias Editor**: Edit column aliases inline
- 🔔 **Schema Change Alerts**: Get notified when table schemas change
- 🎨 **Clean UI**: Minimalistic and functional design
- 📱 **Responsive**: Works on desktop and mobile devices

## Prerequisites

- Node.js 16+ and npm
- Backend API running (see backend README)

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file in the frontend directory:

```bash
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## Available Scripts

### `npm start`

Runs the app in development mode with hot reload.

### `npm run build`

Builds the app for production to the `build` folder.

### `npm test`

Launches the test runner in interactive watch mode.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # React components
│   │   ├── TableSelector.jsx           # Table dropdown selector
│   │   ├── TableSelector.css
│   │   ├── SchemaChangeAlert.jsx       # Schema change notification
│   │   ├── SchemaChangeAlert.css
│   │   ├── TableDataViewer.jsx         # Table data display
│   │   ├── TableDataViewer.css
│   │   ├── MetadataViewer.jsx          # Metadata display
│   │   ├── MetadataViewer.css
│   │   ├── AliasEditor.jsx             # Inline alias editor
│   │   └── AliasEditor.css
│   ├── services/
│   │   └── api.js          # API client
│   ├── App.jsx             # Main app component
│   ├── App.css             # Main app styles
│   ├── index.js            # React entry point
│   └── index.css           # Global styles
├── package.json
└── README.md
```

## Components

### TableSelector

Searchable dropdown for selecting tables. Shows:
- Table name
- Schema status (with badge if changed)
- Row count

### SchemaChangeAlert

Alert banner that appears when schema changes are detected. Shows:
- New columns
- Removed columns
- Type changes
- Refresh metadata button

### TableDataViewer

Displays sample data from the selected table using TanStack Table:
- Shows up to 100 rows by default
- Scrollable table with fixed header
- Null values highlighted
- Long text truncated with tooltips

### MetadataViewer

Displays comprehensive metadata for all columns:
- Column cards with detailed information
- Inline alias editing
- Statistics (min, max, avg)
- Tags (country, city, state, lat, lon)
- Cardinality and null percentage
- Raw JSON view (collapsible)

### AliasEditor

Inline editor for column aliases:
- Add new aliases
- Remove existing aliases
- Save/Cancel actions
- Keyboard shortcuts (Enter to add)

## API Integration

The frontend communicates with the backend API through the `api.js` service:

```javascript
import api from './services/api';

// Get all tables
const tables = await api.getTables();

// Get table data
const data = await api.getTableData('my_table', 1000);

// Get metadata
const metadata = await api.getMetadata('my_table');

// Refresh metadata
await api.refreshMetadata('my_table');

// Update aliases
await api.updateColumnAlias('my_table', 'my_column', ['Alias 1', 'Alias 2']);
```

## Styling

The app uses:
- CSS modules for component-specific styles
- Flexbox and Grid for layouts
- CSS custom properties for theming
- Responsive design patterns

Color palette:
- Primary: `#667eea` to `#764ba2` (gradient)
- Success: `#10b981`
- Warning: `#f59e0b`
- Error: `#dc2626`
- Neutral grays for text and borders

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Tips

### Hot Reload

The dev server supports hot reload. Changes to components will reflect immediately without page refresh.

### Debugging

Open React DevTools in your browser for component inspection and profiling.

### API Mocking

For local development without backend, you can mock API responses in `api.js`:

```javascript
// Mock mode for development
const MOCK_MODE = false;

if (MOCK_MODE) {
  return {
    tables: [...],
    // ... mock data
  };
}
```

## Production Build

### Build

```bash
npm run build
```

Creates an optimized production build in the `build/` directory.

### Serve

You can serve the build using any static file server:

```bash
# Using serve
npx serve -s build

# Using nginx (example config)
server {
  listen 80;
  root /path/to/frontend/build;
  index index.html;
  
  location / {
    try_files $uri /index.html;
  }
  
  location /api {
    proxy_pass http://backend:8000;
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` |

## Troubleshooting

### CORS Errors

If you see CORS errors, ensure:
1. Backend is running
2. Backend CORS settings include frontend URL
3. `REACT_APP_API_URL` is correct

### API Connection Failed

Check:
1. Backend is running on correct port
2. Network connectivity
3. Firewall settings
4. Environment variables

### Build Errors

Try:
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
```

## Performance

The app is optimized for performance:
- Code splitting (automatic with Create React App)
- Lazy loading of large components
- Memoization where appropriate
- Efficient re-rendering with React hooks

## Accessibility

The app follows basic accessibility guidelines:
- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Color contrast compliance

## Future Enhancements

Potential improvements:
- Dark mode toggle
- Export metadata to CSV/JSON
- Advanced filtering and searching
- Column comparison view
- Metadata history/versioning
- User preferences/settings
- Bulk operations

## License

Internal company tool - not for public distribution

## Support

For questions or issues, contact the development team.