import json
import os
import webbrowser
from pathlib import Path

def main():
    # Paths
    current_dir = Path(__file__).parent
    json_path = current_dir / "summary.json"
    html_path = current_dir / "summary_report.html"

    if not json_path.exists():
        print(f"Error: {json_path} does not exist. Please run 'python -m graph_summary.summarize' first.")
        return

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract sections
    generated_at = data.get("generated_at", "N/A")
    overview = data.get("overview", {})
    topology = data.get("topology", {})
    key_actors = data.get("key_actors", [])
    financial = data.get("financial_summary", {})
    comm_summary = data.get("communication_summary", {})
    profiles = data.get("entity_profiles", [])

    # Pre-generate lists/tables
    # Key Actors Table
    actors_rows = []
    for rank, actor in enumerate(key_actors, 1):
        actors_rows.append(f"""
        <tr class="border-b border-outline/20 hover:bg-surface/30">
            <td class="px-6 py-4 text-sm text-gray-400 font-bold mono">{rank}</td>
            <td class="px-6 py-4 text-sm text-white font-semibold">{actor.get('name', 'N/A')}</td>
            <td class="px-6 py-4 text-sm text-gray-300 mono">{actor.get('master_type', 'N/A')}</td>
            <td class="px-6 py-4 text-sm text-gold font-bold mono">{actor.get('composite_score', 0.0):.4f}</td>
            <td class="px-6 py-4 text-sm text-gray-300 mono">{actor.get('degree_centrality', 0.0):.4f}</td>
            <td class="px-6 py-4 text-sm text-gray-300 mono">{actor.get('betweenness_centrality', 0.0):.4f}</td>
            <td class="px-6 py-4 text-sm text-gray-300 mono">{actor.get('pagerank', 0.0):.4f}</td>
            <td class="px-6 py-4 text-sm text-sky-400 font-semibold mono">{actor.get('source_count', 0)}</td>
        </tr>
        """)
    actors_table_html = "".join(actors_rows)

    # Financial Flows
    flows_list = []
    for flow in financial.get("top_flows", []):
        flow_name = flow.get("flow", "")
        amt = flow.get("total_amount", 0)
        cnt = flow.get("transfer_count", 0)
        methods = ", ".join(flow.get("methods", []))
        
        flows_list.append(f"""
        <div class="flex items-center justify-between p-4 bg-darkBg/60 rounded border border-outline/20 mb-3 text-sm">
            <div class="flex items-center gap-3">
                <div class="h-8 w-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400">
                    <i class="fa-solid fa-arrow-right-arrow-left text-xs"></i>
                </div>
                <div>
                    <p class="font-semibold text-white">{flow_name}</p>
                    <p class="text-xs text-gray-400 mono">Method: {methods} | Count: {cnt}</p>
                </div>
            </div>
            <div class="text-right">
                <span class="font-bold text-emerald-400 mono">Rs. {amt:,}</span>
            </div>
        </div>
        """)
    flows_html_str = "".join(flows_list)

    # Entity Profiles Searchable Cards
    profile_cards = []
    for prof in profiles:
        m_id = prof.get("master_id", "")
        name = prof.get("name", "Unknown")
        m_type = prof.get("master_type", "")
        resolved = prof.get("resolved_values", [])
        deg = prof.get("degree_centrality", 0.0)
        bet = prof.get("betweenness_centrality", 0.0)
        pr = prof.get("pagerank", 0.0)
        src_cnt = prof.get("source_count", 0)
        rel_cnt = prof.get("relation_count", 0)
        rel_types = prof.get("relation_types", [])
        
        resolved_str = ", ".join(resolved)
        rel_types_str = ", ".join(rel_types)
        
        profile_cards.append(f"""
        <div class="profile-card panel p-6 rounded-lg border border-outline/20" data-name="{name.lower()} {m_id.lower()} {m_type.lower()}">
            <div class="flex justify-between items-start mb-3">
                <div>
                    <span class="text-[10px] bg-gold/10 text-gold border border-gold/30 px-2 py-0.5 rounded font-bold mono uppercase">{m_type}</span>
                    <h4 class="text-lg font-semibold mt-2 text-white">{name}</h4>
                </div>
                <span class="text-xs text-gray-500 mono">{m_id}</span>
            </div>
            
            <div class="text-xs text-gray-400 mb-4">
                <span class="font-bold mono block mb-1">RESOLVED ALIASES:</span>
                <p class="text-gray-300 italic">"{resolved_str}"</p>
            </div>

            <div class="grid grid-cols-3 gap-2 text-center text-xs bg-darkBg/60 p-3 rounded border border-outline/20 mb-4">
                <div>
                    <p class="text-gray-500 font-bold mono uppercase">Degree</p>
                    <p class="text-white font-bold mono mt-0.5">{deg:.4f}</p>
                </div>
                <div>
                    <p class="text-gray-500 font-bold mono uppercase">Betweenness</p>
                    <p class="text-white font-bold mono mt-0.5">{bet:.4f}</p>
                </div>
                <div>
                    <p class="text-gray-500 font-bold mono uppercase">PageRank</p>
                    <p class="text-white font-bold mono mt-0.5">{pr:.4f}</p>
                </div>
            </div>

            <div class="text-xs text-gray-400">
                <div class="flex justify-between mb-1.5">
                    <span>Relations: <strong class="text-white mono">{rel_cnt}</strong></span>
                    <span>Sources: <strong class="text-white mono">{src_cnt}</strong></span>
                </div>
                <span class="font-bold mono block mb-1">RELATION PATTERNS:</span>
                <p class="text-gray-300 mono text-[10px]">{rel_types_str}</p>
            </div>
        </div>
        """)
    profile_cards_html_str = "".join(profile_cards)

    # Generate Chart Data
    entity_counts = overview.get("entity_type_counts", {})
    relation_counts = overview.get("relation_type_counts", {})
    comm_types = comm_summary.get("by_type", {})
    active_comm = comm_summary.get("most_active_communicators", [])

    # Assemble HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TATVA | Network Analysis & Graph Summary Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Custom styling for premium look -->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;500;700&display=swap');
        body {{
            font-family: 'Geist', sans-serif;
            background-color: #0a0a0b;
            color: #e5e2e3;
        }}
        .mono {{
            font-family: 'JetBrains Mono', monospace;
        }}
        .gold-glow {{
            box-shadow: 0 0 20px rgba(254, 183, 0, 0.12);
        }}
        .panel {{
            background: rgba(28, 27, 28, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(136, 145, 157, 0.2);
        }}
        .scanline {{
            background: linear-gradient(
                rgba(18, 16, 16, 0) 50%, 
                rgba(0, 0, 0, 0.25) 50%
            ), linear-gradient(
                90deg, 
                rgba(255, 0, 0, 0.06), 
                rgba(0, 255, 0, 0.02), 
                rgba(0, 0, 255, 0.06)
            );
            background-size: 100% 4px, 6px 100%;
        }}
    </style>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        gold: '#feb700',
                        darkBg: '#0a0a0b',
                        surface: '#131314',
                        outline: '#3f4852',
                        crimson: '#ff6e68',
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="scanline min-h-screen pb-12">
    
    <!-- Top Nav -->
    <header class="border-b border-outline/30 bg-surface/80 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <span class="text-2xl font-black tracking-widest text-gold">TATVA</span>
                <span class="text-xs bg-gold/10 text-gold border border-gold/30 px-2 py-0.5 rounded uppercase tracking-wider font-semibold mono">Network Summary</span>
            </div>
            <div class="text-right text-xs text-gray-400 mono">
                REPORT_GEN: {generated_at}
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 mt-8">
        <!-- Summary Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="panel p-6 rounded-lg flex items-center justify-between gold-glow">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Total Nodes (Entities)</p>
                    <h3 class="text-3xl font-bold text-white mt-1">{overview.get("total_entities", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-gold/10 flex items-center justify-center border border-gold/20 text-gold">
                    <i class="fa-solid fa-circle text-lg"></i>
                </div>
            </div>
            
            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Total Edges (Relations)</p>
                    <h3 class="text-3xl font-bold text-white mt-1">{overview.get("total_relations", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400">
                    <i class="fa-solid fa-share-nodes text-lg"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Network Density</p>
                    <h3 class="text-3xl font-bold text-white mt-1 mono">{topology.get("density", 0.0) * 100:.2f}%</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
                    <i class="fa-solid fa-chart-line text-lg"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Avg Clustering Coeff</p>
                    <h3 class="text-3xl font-bold text-white mt-1 mono">{topology.get("average_clustering", 0.0):.4f}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400">
                    <i class="fa-solid fa-circle-nodes text-lg"></i>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="panel p-2 rounded-lg mb-6 flex flex-wrap gap-2 justify-center md:justify-start">
            <button onclick="showTab('dashboard')" class="tab-btn active px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-gold text-black">Dashboard</button>
            <button onclick="showTab('key-actors')" class="tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20 text-white">Key Actors</button>
            <button onclick="showTab('financial-flows')" class="tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20 text-white">Financial Summary</button>
            <button onclick="showTab('entity-profiles')" class="tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20 text-white">Entity Directory</button>
        </div>

        <!-- TABS CONTENT -->

        <!-- TAB: DASHBOARD -->
        <div id="tab-dashboard" class="tab-content grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Left Panel: Topology Summary -->
            <div class="panel p-6 rounded-lg">
                <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-network-wired text-gold mr-2"></i>Network Topology</h4>
                <div class="grid grid-cols-2 gap-4 text-sm mb-6">
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10">
                        <span class="text-gray-400 mono text-xs">Weakly Connected:</span>
                        <p class="text-white font-bold mono mt-1">{str(topology.get("is_weakly_connected", False)).upper()}</p>
                    </div>
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10">
                        <span class="text-gray-400 mono text-xs">Components count:</span>
                        <p class="text-white font-bold mono mt-1">{topology.get("weakly_connected_components", 0)}</p>
                    </div>
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10">
                        <span class="text-gray-400 mono text-xs">Largest Comp Size:</span>
                        <p class="text-white font-bold mono mt-1">{topology.get("largest_component_size", 0)} nodes</p>
                    </div>
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10">
                        <span class="text-gray-400 mono text-xs">Avg Degree:</span>
                        <p class="text-white font-bold mono mt-1">{topology.get("avg_degree", 0.0):.2f}</p>
                    </div>
                </div>
                
                <h5 class="text-sm font-bold text-gray-300 mb-3">DATA CHANNELS INGESTED</h5>
                <div class="flex flex-wrap gap-2">
                    {" ".join([f'<span class="bg-surface border border-outline/30 px-2.5 py-1 rounded text-white mono text-xs">{src}</span>' for src in overview.get("data_sources_present", [])])}
                </div>
            </div>

            <!-- Right Panel: Entity breakdown charts -->
            <div class="panel p-6 rounded-lg">
                <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-chart-pie text-gold mr-2"></i>Entity Breakdown</h4>
                <div class="relative h-64">
                    <canvas id="entityChart"></canvas>
                </div>
            </div>

            <!-- Bottom Left: Relation types charts -->
            <div class="panel p-6 rounded-lg">
                <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-chart-bar text-gold mr-2"></i>Relationship Breakdown</h4>
                <div class="relative h-64">
                    <canvas id="relationChart"></canvas>
                </div>
            </div>

            <!-- Bottom Right: Comm breakdown charts -->
            <div class="panel p-6 rounded-lg">
                <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-phone-volume text-gold mr-2"></i>Communications Summary</h4>
                <div class="grid grid-cols-2 gap-4 mb-4 text-xs">
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10 text-center">
                        <span class="text-gray-400 mono block">Total Call Logs</span>
                        <span class="text-lg font-bold text-sky-400 mono mt-1">{comm_summary.get("total_communications", 0)} logs</span>
                    </div>
                    <div class="p-3 bg-darkBg/60 rounded border border-outline/10 text-center">
                        <span class="text-gray-400 mono block">Avg Call Duration</span>
                        <span class="text-lg font-bold text-sky-400 mono mt-1">{comm_summary.get("avg_call_duration_seconds", 0.0):.1f} sec</span>
                    </div>
                </div>
                <div class="relative h-48">
                    <canvas id="commChart"></canvas>
                </div>
            </div>
        </div>

        <!-- TAB: KEY ACTORS -->
        <div id="tab-key-actors" class="tab-content hidden panel rounded-lg overflow-hidden">
            <div class="p-6 border-b border-outline/20">
                <h4 class="text-lg font-bold text-white"><i class="fa-solid fa-crown text-gold mr-2"></i>Centrality-Scored Key Actors</h4>
                <p class="text-xs text-gray-400 mt-1">Suspect nodes ranked by network centrality measures and pagerank scores.</p>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-outline/20">
                    <thead class="bg-surface/50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Rank</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Name</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Master Type</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Composite Score</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Degree Cent</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Betweenness</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">PageRank</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider mono">Sources In</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-outline/10">
                        {actors_table_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- TAB: FINANCIAL SUMMARY -->
        <div id="tab-financial-flows" class="tab-content hidden grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="panel p-6 rounded-lg flex flex-col justify-between">
                <div>
                    <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-wallet text-gold mr-2"></i>Financial Volume</h4>
                    <div class="grid grid-cols-3 gap-4 text-center mt-4 mb-6">
                        <div class="p-4 bg-darkBg/60 rounded border border-outline/15">
                            <span class="text-gray-400 mono text-xs uppercase block">Total Volume</span>
                            <span class="text-xl font-bold text-emerald-400 mono mt-1">Rs. {financial.get("total_volume", 0):,}</span>
                        </div>
                        <div class="p-4 bg-darkBg/60 rounded border border-outline/15">
                            <span class="text-gray-400 mono text-xs uppercase block">Transfers</span>
                            <span class="text-xl font-bold text-white mono mt-1">{financial.get("transfer_count", 0)}</span>
                        </div>
                        <div class="p-4 bg-darkBg/60 rounded border border-outline/15">
                            <span class="text-gray-400 mono text-xs uppercase block">Accounts</span>
                            <span class="text-xl font-bold text-white mono mt-1">{financial.get("unique_accounts_involved", 0)}</span>
                        </div>
                    </div>
                    <p class="text-xs text-gray-400 leading-relaxed italic">
                        Notice: Smurfing transfers consist of rapid payments split under Rs. 10,000 threshold to evade reporting triggers. Re-aggregation occurs at specific intermediary nodes before hawala withdrawal.
                    </p>
                </div>
            </div>

            <div class="panel p-6 rounded-lg">
                <h4 class="text-lg font-bold text-white border-b border-outline/20 pb-3 mb-4"><i class="fa-solid fa-chart-line text-gold mr-2"></i>Top Transaction Paths</h4>
                <div class="max-h-96 overflow-y-auto custom-scrollbar pr-2">
                    {flows_html_str}
                </div>
            </div>
        </div>

        <!-- TAB: ENTITY DIRECTORY -->
        <div id="tab-entity-profiles" class="tab-content hidden">
            <div class="panel p-4 rounded-lg mb-6 flex justify-between items-center">
                <div class="relative w-full md:w-96">
                    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><i class="fa-solid fa-search"></i></span>
                    <input type="text" id="directorySearch" onkeyup="filterDirectory()" placeholder="SEARCH MASTER DIRECTORY..." 
                        class="w-full bg-darkBg border border-outline/40 rounded py-2 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-gold text-sm mono">
                </div>
            </div>
            <div id="directoryGrid" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {profile_cards_html_str}
            </div>
        </div>

    </main>

    <script>
        // Tab switching logic
        function showTab(tabId) {{
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => {{
                content.classList.add('hidden');
            }});

            const targetTab = document.getElementById('tab-' + tabId);
            if (targetTab) {{
                if (tabId === 'financial-flows' || tabId === 'dashboard') {{
                    targetTab.classList.remove('hidden');
                    targetTab.classList.add('grid');
                }} else {{
                    targetTab.classList.remove('hidden');
                }}
            }}

            // Highlight active button
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => {{
                btn.className = "tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20 text-white";
            }});

            const eventTarget = window.event ? window.event.target : null;
            if (eventTarget) {{
                eventTarget.className = "tab-btn active px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-gold text-black";
            }}
        }}

        // Directory filtering
        function filterDirectory() {{
            const val = document.getElementById('directorySearch').value.toLowerCase();
            const cards = document.querySelectorAll('.profile-card');
            
            cards.forEach(card => {{
                const searchName = card.getAttribute('data-name');
                if (searchName.includes(val)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        // Render Charts using CDN Chart.js
        window.addEventListener('load', () => {{
            // Chart 1: Entity Types
            const ctxEntity = document.getElementById('entityChart').getContext('2d');
            new Chart(ctxEntity, {{
                type: 'bar',
                data: {{
                    labels: {list(entity_counts.keys())},
                    datasets: [{{
                        label: 'Entity Count',
                        data: {list(entity_counts.values())},
                        backgroundColor: 'rgba(254, 183, 0, 0.6)',
                        borderColor: '#feb700',
                        borderWidth: 1.5,
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ color: 'rgba(136, 145, 157, 0.15)' }}, ticks: {{ color: '#bec7d4' }} }},
                        x: {{ grid: {{ display: false }}, ticks: {{ color: '#bec7d4' }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Chart 2: Relation Types
            const ctxRelation = document.getElementById('relationChart').getContext('2d');
            new Chart(ctxRelation, {{
                type: 'bar',
                data: {{
                    labels: {list(relation_counts.keys())},
                    datasets: [{{
                        label: 'Relations',
                        data: {list(relation_counts.values())},
                        backgroundColor: 'rgba(56, 189, 248, 0.6)',
                        borderColor: '#38bdf8',
                        borderWidth: 1.5,
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ beginAtZero: true, grid: {{ color: 'rgba(136, 145, 157, 0.15)' }}, ticks: {{ color: '#bec7d4' }} }},
                        y: {{ grid: {{ display: false }}, ticks: {{ color: '#bec7d4' }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Chart 3: Communication Types
            const ctxComm = document.getElementById('commChart').getContext('2d');
            new Chart(ctxComm, {{
                type: 'doughnut',
                data: {{
                    labels: {list(comm_types.keys())},
                    datasets: [{{
                        data: {list(comm_types.values())},
                        backgroundColor: [
                            'rgba(14, 165, 233, 0.7)',
                            'rgba(245, 158, 11, 0.7)',
                            'rgba(239, 68, 68, 0.7)'
                        ],
                        borderColor: '#131314',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'right',
                            labels: {{ color: '#bec7d4', font: {{ family: 'JetBrains Mono', size: 10 }} }}
                        }}
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    # Save HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated Graph Summary Report at: {html_path.resolve()}")

    # Open
    webbrowser.open("file://" + str(html_path.resolve()))

if __name__ == "__main__":
    main()
