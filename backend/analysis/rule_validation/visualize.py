import json
import os
import webbrowser
from pathlib import Path

def main():
    # Paths
    current_dir = Path(__file__).parent
    json_path = current_dir / "flags.json"
    html_path = current_dir / "flags_report.html"

    if not json_path.exists():
        print(f"Error: {json_path} does not exist. Please run 'python -m rule_validation.validate' first.")
        return

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract summary
    generated_at = data.get("generated_at", "N/A")
    total_flags = data.get("total_flags", 0)
    severity = data.get("severity_summary", {})
    flags = data.get("flags", {})

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TATVA | Rule Validation Report</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
            box-shadow: 0 0 20px rgba(255, 191, 0, 0.15);
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
                        gold: '#ffbf00',
                        darkBg: '#0a0a0b',
                        surface: '#131314',
                        outline: '#3f4852',
                        crimson: '#ff6e68',
                        amberAccent: '#feb700'
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
                <span class="text-xs bg-gold/10 text-gold border border-gold/30 px-2 py-0.5 rounded uppercase tracking-wider font-semibold mono">Rule Validation Engine</span>
            </div>
            <div class="text-right text-xs text-gray-400 mono">
                REPORT_GEN: {generated_at}
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 mt-8">
        <!-- Dashboard Metrics Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="panel p-6 rounded-lg flex items-center justify-between gold-glow">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Total Flagged Rules</p>
                    <h3 class="text-3xl font-bold text-white mt-1">{total_flags}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-gold/10 flex items-center justify-center border border-gold/20 text-gold">
                    <i class="fa-solid fa-triangle-exclamation text-xl"></i>
                </div>
            </div>
            
            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Critical Alerts</p>
                    <h3 class="text-3xl font-bold text-red-500 mt-1">{severity.get("CRITICAL", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 text-red-500">
                    <i class="fa-solid fa-skull-crossbones text-xl"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">High Severity</p>
                    <h3 class="text-3xl font-bold text-amberAccent mt-1">{severity.get("HIGH", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-amberAccent/10 flex items-center justify-center border border-amberAccent/20 text-amberAccent">
                    <i class="fa-solid fa-circle-exclamation text-xl"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Medium Severity</p>
                    <h3 class="text-3xl font-bold text-sky-400 mt-1">{severity.get("MEDIUM", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-sky-400/10 flex items-center justify-center border border-sky-400/20 text-sky-400">
                    <i class="fa-solid fa-circle-info text-xl"></i>
                </div>
            </div>
        </div>

        <!-- Search Bar -->
        <div class="panel p-4 rounded-lg mb-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div class="relative w-full md:w-96">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><i class="fa-solid fa-search"></i></span>
                <input type="text" id="searchInput" onkeyup="filterFlags()" placeholder="SEARCH FOR SUSPECT OR RULE..." 
                    class="w-full bg-darkBg border border-outline/40 rounded py-2 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-gold text-sm mono">
            </div>
            <div class="flex gap-2 w-full md:w-auto overflow-x-auto pb-1">
                <button onclick="filterType('all')" class="type-tab-btn active px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-gold text-black">ALL</button>
                <button onclick="filterType('smurfing')" class="type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20">Smurfing</button>
                <button onclick="filterType('forensic_hits')" class="type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20">Forensic Hits</button>
                <button onclick="filterType('communication_bursts')" class="type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20">Bursts</button>
                <button onclick="filterType('colocations')" class="type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20">Colocations</button>
                <button onclick="filterType('cross_source_corroboration')" class="type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20">Corroboration</button>
            </div>
        </div>

        <!-- Flags Containers -->
        <div id="flagsGrid" class="grid grid-cols-1 gap-6">
            
            <!-- SMURFING SECTION -->
            {"".join([f'''
            <div class="flag-card smurfing panel p-6 rounded-lg border-l-4 border-red-500" data-name="{item.get('account_name', '')} smurfing">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded font-bold mono uppercase">CRITICAL ALERT // SMURFING</span>
                        <h4 class="text-xl font-semibold mt-2 text-white">{item.get('account_name', 'Unknown sender')} <span class="text-sm text-gray-400 font-normal">({item.get('account_id', '')})</span></h4>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-gray-400 mono">Total Volume</p>
                        <h5 class="text-lg font-bold text-red-400 mono">Rs. {item.get('total_amount', 0):,}</h5>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-4">{item.get('description', '')}</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-darkBg/60 p-4 rounded border border-outline/20">
                    <div>
                        <span class="text-gray-400 mono">Time window:</span> <span class="text-white mono">{item.get('time_window', '')} ({item.get('duration_minutes', 0)} mins)</span>
                    </div>
                    <div>
                        <span class="text-gray-400 mono">Transfer Count:</span> <span class="text-white mono">{item.get('transfer_count', 0)} splits</span>
                    </div>
                    <div class="md:col-span-2 mt-2">
                        <span class="text-gray-400 font-bold mono block mb-1">Mule Accounts Involved:</span>
                        <div class="flex flex-wrap gap-2">
                            {" ".join([f'<span class="bg-surface border border-outline/30 px-2.5 py-1 rounded text-white mono">{rec}</span>' for rec in item.get('recipients', [])])}
                        </div>
                    </div>
                </div>
            </div>
            ''' for item in flags.get("smurfing", [])])}

            <!-- FORENSIC HITS SECTION -->
            {"".join([f'''
            <div class="flag-card forensic_hits panel p-6 rounded-lg border-l-4 border-amberAccent" data-name="{item.get('source', '')} {item.get('target', '')} {item.get('signal', '')} forensic">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-[10px] bg-amberAccent/10 text-amberAccent border border-amberAccent/20 px-2 py-0.5 rounded font-bold mono uppercase">{item.get('severity', 'HIGH')} ALERT // FORENSIC HIT ({item.get('channel', 'unknown')})</span>
                        <h4 class="text-lg font-semibold mt-2 text-white">{item.get('source', 'Unknown')} &rarr; {item.get('target', 'Unknown')}</h4>
                    </div>
                    <div class="text-right text-xs text-gray-400 mono">
                        {item.get('timestamp', '')}
                    </div>
                </div>
                <div class="bg-darkBg/60 p-4 rounded border border-outline/20 mb-4">
                    <p class="text-xs text-gray-500 font-semibold mono mb-1">SIGNAL FLAGGED: {item.get('signal', '').upper()}</p>
                    <p class="text-sm italic text-gray-200">"{item.get('text_snippet', '')}"</p>
                </div>
                <p class="text-xs text-gray-400 mono">Description: {item.get('description', '')}</p>
            </div>
            ''' for item in flags.get("forensic_hits", [])])}

            <!-- COMMUNICATION BURSTS SECTION -->
            {"".join([f'''
            <div class="flag-card communication_bursts panel p-6 rounded-lg border-l-4 border-sky-400" data-name="{" ".join(item.get('actors', []))} burst">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-[10px] bg-sky-400/10 text-sky-400 border border-sky-400/20 px-2 py-0.5 rounded font-bold mono uppercase">MEDIUM ALERT // COMMUNICATION BURST</span>
                        <h4 class="text-lg font-semibold mt-2 text-white">{" &harr; ".join(item.get('actors', []))}</h4>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-gray-400 mono">Window</p>
                        <p class="text-sm font-bold text-sky-400 mono">{item.get('window', '')}</p>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-4">{item.get('description', '')}</p>
                <div class="text-xs bg-darkBg/60 p-3 rounded border border-outline/20 flex gap-6">
                    <div>
                        <span class="text-gray-400 mono">Interaction Count:</span> <span class="text-white font-bold mono">{item.get('count', 0)} times</span>
                    </div>
                </div>
            </div>
            ''' for item in flags.get("communication_bursts", [])])}

            <!-- COLOCATIONS SECTION -->
            {"".join([f'''
            <div class="flag-card colocations panel p-6 rounded-lg border-l-4 border-amberAccent" data-name="{" ".join(item.get('persons', []))} {item.get('location', '')} colocation rendezvous">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-[10px] bg-amberAccent/10 text-amberAccent border border-amberAccent/20 px-2 py-0.5 rounded font-bold mono uppercase">{item.get('severity', 'HIGH')} ALERT // RENDEZVOUS EVENT</span>
                        <h4 class="text-lg font-semibold mt-2 text-white"><i class="fa-solid fa-location-dot text-gold mr-2"></i>{item.get('location', 'Unknown Location')}</h4>
                    </div>
                    <div class="text-right">
                        <span class="text-xs text-amberAccent bg-amberAccent/10 px-2 py-1 rounded border border-amberAccent/25 font-bold mono">CO-LOCATION</span>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-4">{item.get('description', '')}</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-darkBg/60 p-4 rounded border border-outline/20">
                    <div>
                        <span class="text-gray-400 font-bold mono block mb-1">Actors Present:</span>
                        <div class="flex flex-wrap gap-1.5 mt-1">
                            {" ".join([f'<span class="bg-surface border border-outline/30 px-2 py-0.5 rounded text-white font-medium">{p}</span>' for p in item.get('persons', [])])}
                        </div>
                    </div>
                    <div>
                        <span class="text-gray-400 font-bold mono block mb-1">Observation Timestamps:</span>
                        <div class="flex flex-wrap gap-1.5 mt-1">
                            {" ".join([f'<span class="bg-gold/10 border border-gold/20 text-gold px-2 py-0.5 rounded font-semibold mono">{t}</span>' for t in item.get('timestamps', [])])}
                        </div>
                    </div>
                </div>
            </div>
            ''' for item in flags.get("colocations", [])])}

            <!-- CROSS-SOURCE CORROBORATION SECTION -->
            {"".join([f'''
            <div class="flag-card cross_source_corroboration panel p-6 rounded-lg border-l-4 border-sky-400" data-name="{item.get('entity_name', '')} corroboration">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="text-[10px] bg-sky-400/10 text-sky-400 border border-sky-400/20 px-2 py-0.5 rounded font-bold mono uppercase">{item.get('severity', 'MEDIUM')} ALERT // CROSS-SOURCE CORROBORATION</span>
                        <h4 class="text-lg font-semibold mt-2 text-white">{item.get('entity_name', '')} <span class="text-xs text-gray-400 font-normal">({item.get('entity_type', '')})</span></h4>
                    </div>
                    <div class="text-right">
                        <span class="text-xs text-sky-400 bg-sky-400/10 px-2 py-1 rounded border border-sky-400/25 font-bold mono">{item.get('source_count', 0)} sources</span>
                    </div>
                </div>
                <p class="text-sm text-gray-300 mb-4">{item.get('description', '')}</p>
                <div class="text-xs bg-darkBg/60 p-3 rounded border border-outline/20">
                    <span class="text-gray-400 font-bold mono block mb-1">Corroborated Data Channels:</span>
                    <div class="flex flex-wrap gap-1.5 mt-1">
                        {" ".join([f'<span class="bg-surface border border-outline/30 px-2 py-0.5 rounded text-white mono">{src}</span>' for src in item.get('sources', [])])}
                    </div>
                </div>
            </div>
            ''' for item in flags.get("cross_source_corroboration", [])])}

        </div>
    </main>

    <!-- Simple client-side javascript for filtering -->
    <script>
        let currentFilter = 'all';

        function filterFlags() {{
            const searchVal = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.flag-card');

            cards.forEach(card => {{
                const content = card.getAttribute('data-name').toLowerCase();
                const textContent = card.innerText.toLowerCase();
                const matchesSearch = content.includes(searchVal) || textContent.includes(searchVal);
                
                let matchesType = true;
                if (currentFilter !== 'all') {{
                    matchesType = card.classList.contains(currentFilter);
                }}

                if (matchesSearch && matchesType) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        function filterType(type) {{
            currentFilter = type;
            
            // Highlight active button
            const buttons = document.querySelectorAll('.type-tab-btn');
            buttons.forEach(btn => {{
                btn.className = "type-tab-btn px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-surface border border-outline/30 hover:bg-outline/20 text-white";
            }});

            // Find clicked button
            const eventTarget = window.event ? window.event.target : null;
            if (eventTarget) {{
                eventTarget.className = "type-tab-btn active px-4 py-2 rounded text-xs tracking-wider uppercase font-bold mono bg-gold text-black";
            }}

            filterFlags();
        }}
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated Rule Validation Report at: {html_path.resolve()}")

    # Open in browser
    webbrowser.open("file://" + str(html_path.resolve()))

if __name__ == "__main__":
    main()
