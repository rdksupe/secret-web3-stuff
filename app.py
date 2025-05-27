from flask import Flask, render_template, request, jsonify
import networkx as nx
import json
import plotly
from datetime import datetime
from main import get_wallet_transactions
from llm_utils import summarize_profile, generate_handle, analyze_entities
from collections import Counter
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# Split endpoints for incremental loading
@app.route('/analyze/profile', methods=['POST'])
def analyze_profile():
    """Handle basic wallet profile analysis"""
    data = request.get_json()
    wallet_address = data.get('wallet_address', '')
    
    if not wallet_address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    try:
        # Get the basic profile data without LLM enhancements
        profile = create_basic_profile(wallet_address)
        return jsonify({'profile': profile})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/llm-insights', methods=['POST'])
def analyze_llm_insights():
    """Handle LLM-based insights (potentially slow)"""
    data = request.get_json()
    wallet_address = data.get('wallet_address', '')
    
    if not wallet_address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    try:
        # Get transactions
        txs = get_wallet_transactions(wallet_address, limit=100)
        
        # Create a minimal profile for LLM context
        profile = create_basic_profile(wallet_address)
        
        # Generate LLM insights
        insights = {
            "health_summary": summarize_profile(profile),
            "social_handle": generate_handle(profile),
            "entity_insights": analyze_entities(txs)
        }
        
        return jsonify(insights)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/network-graph', methods=['POST'])
def analyze_network():
    """Generate network visualization"""
    data = request.get_json()
    wallet_address = data.get('wallet_address', '')
    
    if not wallet_address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    try:
        txs = get_wallet_transactions(wallet_address, limit=100)
        # Return the serialized figure directly
        graph_data = visualize_function_transitions(txs)
        return jsonify({'graph': graph_data})
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return jsonify({
            'error': f'Graph error: {str(e)}', 
            'traceback': traceback_str
        }), 500

@app.route('/analyze/timeline', methods=['POST'])
def analyze_timeline():
    """Generate timeline visualization"""
    data = request.get_json()
    wallet_address = data.get('wallet_address', '')
    
    if not wallet_address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    try:
        txs = get_wallet_transactions(wallet_address, limit=100)
        timeline_json = generate_timeline_data(txs)
        return jsonify({'timeline': timeline_json})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Split create_wallet_profile into basic and LLM parts
def create_basic_profile(wallet_address):
    """Generate a basic wallet profile without LLM enhancements"""
    # Get transactions
    txs = get_wallet_transactions(wallet_address, limit=100)
    if not txs:
        return {'error': 'No transactions found for this wallet address'}
    
    # Basic profile calculation logic
    tx_count = len(txs)
    
    # Get first transaction time
    ts_list = [datetime.fromisoformat(tx["Timestamp"]).timestamp() for tx in txs]
    first_ts = min(ts_list)
    age_days = (datetime.now().timestamp() - first_ts) / 86400
    
    # Count transaction types
    tx_types = Counter()
    for tx in txs:
        fn = tx.get("Function","")
        if "transfer" in fn: tx_types["Transfer"]+=1
        elif "swap" in fn: tx_types["Swap"]+=1
        elif any(x in fn for x in ("pool","lend","borrow")): tx_types["DeFi"]+=1
        elif "nft" in fn.lower(): tx_types["NFT"]+=1
        else: tx_types["Other"]+=1
    
    # Determine persona
    persona = "Unclassified"
    if tx_count==0: persona="Inactive"
    elif tx_types.get("DeFi",0) > tx_count*0.3: persona="Active DeFi User"
    elif tx_count>50: persona="Active Trader"
    elif tx_types.get("NFT",0) > tx_count*0.3: persona="NFT Collector"
    elif age_days>30 and tx_count<10: persona="Long-term Holder"
    
    # Count function usage
    func_counter = Counter(tx.get("Function","") for tx in txs)
    top_functions = [{"name": fn, "count": ct} for fn, ct in func_counter.most_common()]
    
    # Build the profile
    return {
        "address": wallet_address,
        "wallet_age_days": int(age_days),
        "total_transactions": tx_count,
        "primary_activity": tx_types.most_common(1)[0][0] if tx_types else "None",
        "persona": persona,
        "tx_type_counts": dict(tx_types),
        "top_functions": top_functions,
        "transactions": txs[:20]  # Keep only a subset for display
    }

# Remove the original create_wallet_profile function as it's now split

def visualize_function_transitions(txs):
    print(f"Visualizing function transitions for {len(txs)} transactions")
    
    # fetch formatted txs
    funcs = [tx['Function'] for tx in txs if tx['Function']]
    
    # build transition graph
    G = nx.DiGraph()
    for a, b in zip(funcs, funcs[1:]):
        G.add_edge(a, b, weight=G[a][b]['weight']+1 if G.has_edge(a, b) else 1)
    
    # get position layout
    pos = nx.spring_layout(G, k=0.5, seed=42)
    
    # create edge traces
    edge_x = []
    edge_y = []
    edge_weights = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(edge[2]['weight'])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    # create node traces
    node_x = []
    node_y = []
    node_text = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        marker=dict(
            size=20,
            color='skyblue',
            line_width=2))
    
    # create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0,l=0,r=0,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    ))
    
    # Don't parse as JSON before returning, just return the figure object
    # Return the figure's data and layout directly
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def generate_timeline_data(transactions):
    """Generate timeline visualization for Plotly"""
    if not transactions:
        return json.dumps({})
    
    df = pd.DataFrame(transactions)
    if 'Timestamp' not in df.columns:
        return json.dumps({})
    
    # Convert to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Create the timeline figure
    fig = go.Figure()
    
    # Add a scatter trace for each function type
    for function in df['Function'].unique():
        subset = df[df['Function'] == function]
        fig.add_trace(go.Scatter(
            x=subset['Timestamp'],
            y=[function] * len(subset),
            mode='markers',
            name=function,
            marker=dict(size=10),
            hovertemplate='%{x}<br>%{y}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Transaction Timeline",
        xaxis_title="Date",
        yaxis_title="Function",
        height=400
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
