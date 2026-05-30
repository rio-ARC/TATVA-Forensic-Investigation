// ── Case Files — TypeScript Interfaces ─────────────────────────────────────

/** Payload sent to POST /api/cases */
export interface CaseCreatePayload {
  case_id: string;
  title: string;
  description?: string;
  investigator?: string;
  metadata?: Record<string, unknown>;
}

/** Shape of each item returned by GET /api/cases */
export interface CaseListItem {
  case_id: string;
  title: string;
  status: string;
  investigator: string;
  created_at: string | null;
}

/** Status of a file in the local upload queue */
export type UploadStatus = 'queued' | 'uploading' | 'uploaded' | 'error';

/** A single file item in the evidence upload queue */
export interface EvidenceUploadItem {
  /** Unique local key for React list reconciliation */
  key: string;
  /** Original File object from the browser */
  file: File;
  /** Display filename */
  filename: string;
  /** Derived file extension / type */
  file_type: string;
  /** Upload lifecycle state */
  status: UploadStatus;
  /** Upload progress 0–100 */
  progress: number;
  /** SHA-256 hash returned by the server after upload */
  file_hash?: string;
  /** Error message if status === 'error' */
  error?: string;
}

/** Cognitive configuration toggles stored inside case metadata */
export interface CognitiveConfig {
  anomaly: boolean;
  gnn: boolean;
  intel: boolean;
  temporal: boolean;
}
