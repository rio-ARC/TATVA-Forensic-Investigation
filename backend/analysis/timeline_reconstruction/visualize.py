import json
import os
import webbrowser
from pathlib import Path

def main():
    # Paths
    current_dir = Path(__file__).parent
    json_path = current_dir / "timeline.json"
    html_path = current_dir / "timeline_report.html"

    if not json_path.exists():
        print(f"Error: {json_path} does not exist. Please run 'python -m timeline_reconstruction.reconstruct' first.")
        return

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract info
    generated_at = data.get("generated_at", "N/A")
    window = data.get("incident_window", {})
    stats = data.get("stats", {})
    scenes = data.get("scenes", [])

    # Map source type to custom color and icon
    def get_source_badge(source_type):
        s = source_type.lower()
        if "chat" in s:
            return "bg-green-500/10 text-green-400 border-green-500/20", "fa-solid fa-comments"
        elif "email" in s:
            return "bg-blue-500/10 text-blue-400 border-blue-500/20", "fa-solid fa-envelope"
        elif "bank" in s or "trans" in s:
            return "bg-amber-500/10 text-amber-400 border-amber-500/20", "fa-solid fa-money-bill-transfer"
        elif "gps" in s or "tracker" in s or "tower" in s:
            return "bg-purple-500/10 text-purple-400 border-purple-500/20", "fa-solid fa-location-crosshairs"
        elif "fir" in s:
            return "bg-red-500/10 text-red-400 border-red-500/20", "fa-solid fa-file-invoice"
        else:
            return "bg-gray-500/10 text-gray-400 border-gray-500/20", "fa-solid fa-circle-question"

    # Pre-generate scenes html
    scenes_html = []
    for s_idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", f"SCENE_{s_idx+1:02d}")
        label = scene.get("label", "Scene Activity")
        start = scene.get("window_start", "")
        end = scene.get("window_end", "")
        event_count = scene.get("event_count", 0)
        dominant_sources = scene.get("dominant_source_types", [])
        active_actors = scene.get("active_actors", [])
        events = scene.get("events", [])

        # Breakdown stats
        breakdown = scene.get("action_breakdown", {})
        breakdown_str = ", ".join([f"{k} ({v})" for k, v in breakdown.items()])

        # Build list of events in this scene
        events_list_html = []
        for e in events:
            ts = e.get("timestamp", "")
            action = e.get("action", "")
            from_actor = e.get("from", "")
            to_actor = e.get("to", "")
            src_type = e.get("source_type", "")
            conf = e.get("confidence", 1.0)
            desc = e.get("description", "")
            attrs = e.get("attributes", {})

            badge_class, icon_class = get_source_badge(src_type)

            # Check for specific flags (e.g. email/chat forensic hit)
            flag_html = ""
            forensic_signals = attrs.get("forensic_signals", {})
            active_signals = [k for k, v in forensic_signals.items() if v]
            if active_signals:
                flag_html = f"""
                <div class="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 mono uppercase">
                    <i class="fa-solid fa-flag animate-pulse"></i> FLAGGED: {', '.join(active_signals).upper()}
                </div>
                """

            events_list_html.append(f"""
            <div class="event-item relative pl-8 pb-6 border-l border-outline/30 last:border-l-0" data-actors="{from_actor.lower()} {to_actor.lower()}">
                <!-- Bullet Icon -->
                <span class="absolute -left-3 top-0 h-6 w-6 rounded-full bg-darkBg border border-outline/40 flex items-center justify-center text-[10px] text-gray-400">
                    <i class="{icon_class}"></i>
                </span>
                
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div class="mono text-xs text-gold font-semibold">{ts}</div>
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 border rounded text-[10px] mono uppercase {badge_class}">{src_type}</span>
                        <span class="text-[10px] text-gray-500 mono">CONF: {int(conf * 100)}%</span>
                    </div>
                </div>
                
                <p class="text-sm text-gray-200 mt-1 font-medium">{desc}</p>
                {flag_html}
            </div>
            """)

        events_html_str = "".join(events_list_html)
        actors_badges = " ".join([f'<span class="bg-surface/80 border border-outline/30 px-2 py-0.5 rounded text-xs text-gray-300">{act}</span>' for act in active_actors])
        sources_badges = " ".join([f'<span class="px-2 py-0.5 border rounded text-[10px] mono uppercase {get_source_badge(src)[0]}">{src}</span>' for src in dominant_sources])

        scenes_html.append(f"""
        <div class="scene-card panel rounded-lg border border-outline/20 overflow-hidden mb-6" data-actors="{" ".join(active_actors).lower()}">
            <!-- Scene Header Accordion Trigger -->
            <button onclick="toggleScene('{scene_id}')" class="w-full text-left p-6 flex justify-between items-center bg-surface/40 hover:bg-surface/80 transition-colors">
                <div class="flex-grow">
                    <div class="flex flex-wrap items-center gap-3">
                        <span class="text-xs bg-gold/10 text-gold border border-gold/30 px-2.5 py-0.5 rounded font-bold mono uppercase">{scene_id}</span>
                        <span class="text-xs text-gray-400 mono"><i class="fa-regular fa-clock mr-1"></i>{start} - {end}</span>
                        <span class="text-xs bg-sky-400/10 text-sky-400 border border-sky-400/20 px-2 py-0.5 rounded font-bold mono">{event_count} EVENTS</span>
                    </div>
                    <h3 class="text-xl font-semibold text-white mt-2">{label}</h3>
                </div>
                <div class="text-gray-400 text-lg ml-4">
                    <i id="icon-{scene_id}" class="fa-solid fa-chevron-down transform transition-transform duration-200"></i>
                </div>
            </button>
            
            <!-- Scene Body -->
            <div id="body-{scene_id}" class="hidden border-t border-outline/20 p-6 bg-darkBg/30">
                
                <!-- Scene Meta Grid -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6 pb-6 border-b border-outline/20 text-xs">
                    <div>
                        <span class="text-gray-400 font-bold mono block mb-2">ACTIVE ACTORS</span>
                        <div class="flex flex-wrap gap-1.5">{actors_badges}</div>
                    </div>
                    <div>
                        <span class="text-gray-400 font-bold mono block mb-2">DOMINANT DATA SOURCES</span>
                        <div class="flex flex-wrap gap-1.5">{sources_badges}</div>
                    </div>
                    <div>
                        <span class="text-gray-400 font-bold mono block mb-2">ACTION BREAKDOWN</span>
                        <p class="text-gray-300 leading-relaxed font-semibold">{breakdown_str}</p>
                    </div>
                </div>

                <!-- Event Timeline List -->
                <div class="relative mt-2">
                    {events_html_str}
                </div>

            </div>
        </div>
        """)

    scenes_html_str = "".join(scenes_html)

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TATVA | Timeline Reconstruction Console</title>
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
                <span class="text-xs bg-gold/10 text-gold border border-gold/30 px-2 py-0.5 rounded uppercase tracking-wider font-semibold mono">Temporal Reconstruction</span>
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
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Total Temporal Events</p>
                    <h3 class="text-3xl font-bold text-white mt-1">{stats.get("total_events", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-gold/10 flex items-center justify-center border border-gold/20 text-gold">
                    <i class="fa-solid fa-list-ol text-lg"></i>
                </div>
            </div>
            
            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Identified Scenes</p>
                    <h3 class="text-3xl font-bold text-white mt-1">{stats.get("total_scenes", 0)}</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400">
                    <i class="fa-solid fa-clapperboard text-lg"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Incident Duration</p>
                    <h3 class="text-xl font-bold text-white mt-2.5 mono">{int(window.get("duration_minutes", 0) // 60)}h {int(window.get("duration_minutes", 0) % 60)}m</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-purple-500/10 flex items-center justify-center border border-purple-500/20 text-purple-400">
                    <i class="fa-solid fa-hourglass-half text-lg"></i>
                </div>
            </div>

            <div class="panel p-6 rounded-lg flex items-center justify-between">
                <div>
                    <p class="text-xs uppercase tracking-widest text-gray-400 mono">Peak Scene Activity</p>
                    <h3 class="text-xl font-bold text-crimson mt-2.5 mono">{stats.get("peak_activity_scene", "N/A")} ({stats.get("peak_activity_count", 0)} ev)</h3>
                </div>
                <div class="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 text-crimson">
                    <i class="fa-solid fa-fire text-lg"></i>
                </div>
            </div>
        </div>

        <!-- Filter & Search Panel -->
        <div class="panel p-4 rounded-lg mb-6 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div class="relative w-full md:w-96">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><i class="fa-solid fa-search"></i></span>
                <input type="text" id="actorSearch" onkeyup="filterScenes()" placeholder="FILTER TIMELINE BY ACTOR..." 
                    class="w-full bg-darkBg border border-outline/40 rounded py-2 pl-10 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-gold text-sm mono">
            </div>
            <div class="flex gap-3 text-xs mono text-gray-400">
                <span>Start: <strong class="text-white">{window.get("start", "N/A")}</strong></span>
                <span>&rarr;</span>
                <span>End: <strong class="text-white">{window.get("end", "N/A")}</strong></span>
            </div>
        </div>

        <!-- Scenes Accordion List -->
        <div id="scenesContainer">
            {scenes_html_str}
        </div>
    </main>

    <script>
        function toggleScene(sceneId) {{
            const body = document.getElementById('body-' + sceneId);
            const icon = document.getElementById('icon-' + sceneId);
            
            if (body.classList.contains('hidden')) {{
                body.classList.remove('hidden');
                icon.classList.add('rotate-180');
            }} else {{
                body.classList.add('hidden');
                icon.classList.remove('rotate-180');
            }}
        }}

        function filterScenes() {{
            const searchVal = document.getElementById('actorSearch').value.toLowerCase();
            const scenes = document.querySelectorAll('.scene-card');

            scenes.forEach(scene => {{
                // Check if scene matches actor
                const actorsAttr = scene.getAttribute('data-actors');
                
                // Also search event descriptions inside the scene
                const textContent = scene.innerText.toLowerCase();

                const matches = actorsAttr.includes(searchVal) || textContent.includes(searchVal);
                
                if (matches) {{
                    scene.style.display = 'block';
                }} else {{
                    scene.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""

    # Save
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated Reconstructed Timeline Report at: {html_path.resolve()}")

    # Open
    webbrowser.open("file://" + str(html_path.resolve()))

if __name__ == "__main__":
    main()
