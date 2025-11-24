"""
Generate interactive HTML visualization of Neptune graph
"""

import json
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from app.config import settings
from datetime import datetime


def execute_query(query):
    """Execute an OpenCypher query on Neptune Analytics"""
    endpoint = settings.neptune_endpoint
    base_url = f"https://{endpoint}"
    url = f"{base_url}/opencypher"

    body = {"query": query}
    body_json = json.dumps(body)
    headers = {'Content-Type': 'application/json'}

    session = boto3.Session()
    credentials = session.get_credentials()

    request = AWSRequest(method='POST', url=url, data=body_json, headers=headers)
    SigV4Auth(credentials, 'neptune-graph', 'us-east-1').add_auth(request)

    response = requests.post(url, data=body_json, headers=dict(request.headers), verify=True)

    if response.status_code != 200:
        print(f"HTTP {response.status_code}: {response.reason}")
        print(f"Response body: {response.text}")

    response.raise_for_status()

    return response.json().get('results', [])


def fetch_graph_data():
    """Fetch all nodes and relationships from Neptune"""

    print("Fetching graph data from Neptune...")
    print()

    # Fetch all nodes
    print("  Fetching nodes...")
    nodes_query = """
    MATCH (n)
    RETURN id(n) as id,
           labels(n) as labels,
           n.name as name,
           n.column_name as column_name,
           n.full_name as full_name,
           n.column_type as column_type,
           n.row_count as row_count,
           n.column_count as column_count,
           n.table_embedding_json IS NOT NULL as has_table_embedding,
           n.column_embedding_json IS NOT NULL as has_column_embedding
    """

    nodes_raw = execute_query(nodes_query)

    # Process nodes
    nodes = []
    for node in nodes_raw:
        node_id = node['id']
        labels = node.get('labels', ['Unknown'])
        label = labels[0] if labels else 'Unknown'

        # Determine display name
        name = node.get('name') or node.get('full_name') or node.get('column_name') or 'Unknown'

        # Determine color based on type
        if label == 'Table':
            color = '#4A90E2'  # Blue for tables
            shape = 'box'
            size = 30
        elif label == 'Column':
            color = '#50C878'  # Green for columns
            shape = 'ellipse'
            size = 20
        else:
            color = '#FFA500'  # Orange for unknown
            shape = 'diamond'
            size = 25

        # Check if has embeddings
        has_embedding = node.get('has_table_embedding') or node.get('has_column_embedding')
        if has_embedding:
            color = color  # Keep color
            border_width = 3
            border_color = '#FFD700'  # Gold border for nodes with embeddings
        else:
            border_width = 1
            border_color = '#999999'

        # Tooltip info
        tooltip = f"<b>{label}</b><br>"
        tooltip += f"Name: {name}<br>"

        if label == 'Table':
            tooltip += f"Rows: {node.get('row_count', 'N/A')}<br>"
            tooltip += f"Columns: {node.get('column_count', 'N/A')}<br>"
            tooltip += f"Has Embedding: {'✅' if has_embedding else '❌'}"
        elif label == 'Column':
            tooltip += f"Type: {node.get('column_type', 'N/A')}<br>"
            tooltip += f"Has Embedding: {'✅' if has_embedding else '❌'}"

        nodes.append({
            'id': node_id,
            'label': name if len(name) < 30 else name[:27] + '...',
            'title': tooltip,
            'color': {
                'background': color,
                'border': border_color
            },
            'shape': shape,
            'size': size,
            'borderWidth': border_width,
            'font': {'size': 12}
        })

    print(f"  ✅ Fetched {len(nodes)} nodes")

    # Fetch all relationships
    print("  Fetching relationships...")
    edges_query = """
    MATCH (source)-[r]->(target)
    RETURN id(source) as source_id,
           id(target) as target_id,
           type(r) as rel_type,
           r.confidence as confidence,
           r.relationship_type as relationship_type
    """

    edges_raw = execute_query(edges_query)

    # Process edges
    edges = []
    for edge in edges_raw:
        rel_type = edge['rel_type']

        # Color based on relationship type
        if rel_type == 'HAS_COLUMN':
            color = '#888888'  # Gray
            width = 2
            dashes = False
        elif rel_type == 'RELATED_TO':
            color = '#FF6B6B'  # Red
            width = 3
            dashes = False
        elif rel_type == 'RELATES_TO':
            color = '#9B59B6'  # Purple
            width = 2
            dashes = True
        else:
            color = '#95A5A6'  # Light gray
            width = 1
            dashes = True

        # Tooltip
        tooltip = f"<b>{rel_type}</b><br>"
        if edge.get('confidence'):
            tooltip += f"Confidence: {edge['confidence']:.2f}<br>"
        if edge.get('relationship_type'):
            tooltip += f"Type: {edge['relationship_type']}"

        edges.append({
            'from': edge['source_id'],
            'to': edge['target_id'],
            'label': rel_type,
            'title': tooltip,
            'color': color,
            'width': width,
            'dashes': dashes,
            'arrows': 'to',
            'font': {'size': 10, 'align': 'middle'}
        })

    print(f"  ✅ Fetched {len(edges)} relationships")
    print()

    return nodes, edges


def generate_html(nodes, edges):
    """Generate HTML with vis.js visualization"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Neptune Graph Visualization - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f0f0f0;
        }}

        #header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}

        #controls {{
            background: white;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            background: white;
            margin: 10px;
        }}

        #legend {{
            background: white;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .legend-item {{
            display: inline-block;
            margin: 10px 20px;
        }}

        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border: 1px solid #333;
        }}

        .stats {{
            background: white;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stat-item {{
            display: inline-block;
            margin: 10px 20px;
            font-size: 16px;
        }}

        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #4A90E2;
        }}

        button {{
            background: #4A90E2;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}

        button:hover {{
            background: #357ABD;
        }}
    </style>
</head>
<body>

<div id="header">
    <h1>🌐 Neptune Analytics Graph Visualization</h1>
    <p>Interactive visualization of cai-semantic-graph</p>
    <p style="font-size: 12px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>

<div class="stats">
    <div class="stat-item">
        <div class="stat-number">{len(nodes)}</div>
        <div>Nodes</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">{len(edges)}</div>
        <div>Relationships</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">{sum(1 for n in nodes if '✅' in n.get('title', ''))}</div>
        <div>With Embeddings</div>
    </div>
</div>

<div id="legend">
    <strong>Legend:</strong>
    <div class="legend-item">
        <span class="legend-color" style="background: #4A90E2;"></span>
        <span>Table Node</span>
    </div>
    <div class="legend-item">
        <span class="legend-color" style="background: #50C878;"></span>
        <span>Column Node</span>
    </div>
    <div class="legend-item">
        <span class="legend-color" style="background: #888888;"></span>
        <span>HAS_COLUMN</span>
    </div>
    <div class="legend-item">
        <span class="legend-color" style="background: #FF6B6B;"></span>
        <span>RELATED_TO</span>
    </div>
    <div class="legend-item">
        <span class="legend-color" style="background: #9B59B6;"></span>
        <span>RELATES_TO</span>
    </div>
    <div class="legend-item">
        <span style="border: 3px solid #FFD700; display: inline-block; width: 20px; height: 20px; margin-right: 5px; vertical-align: middle;"></span>
        <span>Has Embedding (Gold Border)</span>
    </div>
</div>

<div id="controls">
    <button onclick="network.fit()">Fit to Screen</button>
    <button onclick="resetZoom()">Reset Zoom</button>
    <button onclick="network.stabilize()">Re-stabilize</button>
    <button onclick="togglePhysics()">Toggle Physics</button>
    <button onclick="exportGraph()">Export as JSON</button>
</div>

<div id="mynetwork"></div>

<script type="text/javascript">
    // Graph data
    var nodes = new vis.DataSet({json.dumps(nodes, indent=2)});
    var edges = new vis.DataSet({json.dumps(edges, indent=2)});

    // Create network
    var container = document.getElementById('mynetwork');
    var data = {{
        nodes: nodes,
        edges: edges
    }};

    var options = {{
        nodes: {{
            font: {{
                size: 14,
                color: '#333'
            }}
        }},
        edges: {{
            smooth: {{
                type: 'continuous',
                roundness: 0.5
            }}
        }},
        physics: {{
            enabled: true,
            stabilization: {{
                iterations: 200
            }},
            barnesHut: {{
                gravitationalConstant: -8000,
                centralGravity: 0.3,
                springLength: 200,
                springConstant: 0.04,
                damping: 0.09
            }}
        }},
        interaction: {{
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true
        }}
    }};

    var network = new vis.Network(container, data, options);

    // Event handlers
    network.on("click", function (params) {{
        if (params.nodes.length > 0) {{
            var nodeId = params.nodes[0];
            var node = nodes.get(nodeId);
            console.log("Clicked node:", node);
        }}
    }});

    // Control functions
    function resetZoom() {{
        network.moveTo({{
            scale: 1.0,
            position: {{x:0, y:0}}
        }});
    }}

    var physicsEnabled = true;
    function togglePhysics() {{
        physicsEnabled = !physicsEnabled;
        network.setOptions({{physics: {{enabled: physicsEnabled}}}});
    }}

    function exportGraph() {{
        var graphData = {{
            nodes: nodes.get(),
            edges: edges.get()
        }};
        var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(graphData, null, 2));
        var downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "neptune_graph.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    }}

    console.log("Graph loaded:", nodes.length, "nodes,", edges.length, "edges");
</script>

</body>
</html>
"""

    return html


def main():
    """Main function to generate visualization"""

    print("="*80)
    print("NEPTUNE GRAPH VISUALIZATION GENERATOR")
    print("="*80)
    print()

    # Fetch data
    nodes, edges = fetch_graph_data()

    # Generate HTML
    print("Generating HTML visualization...")
    html = generate_html(nodes, edges)

    # Write to file
    output_file = "neptune_graph_visualization.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Visualization saved to: {output_file}")
    print()
    print("="*80)
    print("DONE!")
    print("="*80)
    print()
    print(f"Open {output_file} in your browser to view the interactive graph!")
    print()
    print("Features:")
    print("  - Hover over nodes/edges to see details")
    print("  - Click and drag to move nodes")
    print("  - Scroll to zoom")
    print("  - Gold borders = nodes with embeddings")
    print("  - Different colors for Tables, Columns, and relationship types")


if __name__ == "__main__":
    main()
