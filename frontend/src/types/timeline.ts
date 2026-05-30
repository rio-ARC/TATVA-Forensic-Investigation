export interface ReconstructedEvent {
  timestamp: string;
  action: string;
  from: string;
  from_id: string;
  to?: string;
  to_id?: string;
  source_type: string;
  confidence: number;
  description: string;
  attributes?: Record<string, any>;
}

export interface TimelineScene {
  scene_id: string;
  window_start: string;
  window_end: string;
  label: string;
  event_count: number;
  action_breakdown: Record<string, number>;
  dominant_source_types: string[];
  active_actors: string[];
  events: ReconstructedEvent[];
}

export interface ReconstructedTimeline {
  generated_at: string;
  incident_window: {
    start: string;
    end: string;
    duration_minutes: number;
  };
  stats: {
    total_events: number;
    total_scenes: number;
    action_type_counts: Record<string, number>;
    source_type_counts: Record<string, number>;
    peak_activity_scene: string;
    peak_activity_count: number;
  };
  total_events: number;
  total_scenes: number;
  scenes: TimelineScene[];
}
