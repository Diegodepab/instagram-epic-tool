export type ConnectionType = 'follows' | 'followed_by' | 'mutual' | 'blocks';
export type RelationshipKind = 'root' | 'mutual' | 'follower_only' | 'following_only';

export interface GraphNode {
  id: string;
  username: string;
  group: 0 | 1 | 2 | 3;
  is_expanded: boolean;
  degree: number;
  metadata: { relation?: RelationshipKind; [key: string]: unknown };
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  index?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  connection_type: ConnectionType;
  weight: number;
  since_timestamp?: number | null;
  sources?: string[];
}

export interface APIConnectionEdge {
  source_id: string;
  target_id: string;
  connection_type: ConnectionType;
  weight: number;
  since_timestamp?: number | null;
  sources?: string[];
}

export interface APIGraphPayload {
  nodes: GraphNode[];
  edges: APIConnectionEdge[];
  metadata: Record<string, unknown>;
}

export interface InternalGraphState {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface ProfileSummary {
  username: string;
  followers: number;
  following: number;
  mutuals: number;
  followers_only: number;
  following_only: number;
}

export interface ImportResponse {
  session_id: string;
  summary: ProfileSummary;
  graph: APIGraphPayload;
  expires_in_seconds: number;
  warnings: string[];
  imported_profiles: string[];
}

export type RelationshipCategory = 'all' | 'followers' | 'following' | 'mutuals' | 'followers_only' | 'following_only';

export interface RelationshipItem {
  username: string;
  relationship: 'mutuals' | 'followers_only' | 'following_only';
  known_connections: number;
}

export interface RelationshipPage {
  items: RelationshipItem[];
  total: number;
  offset: number;
  limit: number;
}

export interface LabStatus {
  instagrapi: { available: boolean; enabled: boolean; mode: string; limits: { relationships: number; media: number } };
  instagram_bruter: { available: boolean; enabled: boolean; mode: string };
}

export interface DefensiveAssessment {
  repository: string;
  mode: 'static_only';
  executed: false;
  network_access: false;
  classification: string;
  summary: { python_files: number; functions: number; classes: number };
  indicator_counts: Record<string, number>;
  files: Array<{ path: string; sha256: string; functions: number; classes: number }>;
}

export interface OwnAccountResult {
  username: string;
  full_name: string;
  is_private: boolean;
  follower_count: number;
  following_count: number;
  followers_sample: string[];
  following_sample: string[];
  media_sample: Array<{ id: string; code: string; media_type: number }>;
  limits_applied: { relationships: number; media: number };
}

// ---------------------------------------------------------------------------
// Live Scan types
// ---------------------------------------------------------------------------

export interface LiveProfileItem {
  username: string;
  full_name: string;
  is_private: boolean;
  profile_pic_b64: string | null;
}

export interface LiveProfilePreview {
  username: string;
  full_name: string;
  is_private: boolean;
  profile_pic_b64: string | null;
  follower_count: number;
  following_count: number;
  followers: LiveProfileItem[];
  following: LiveProfileItem[];
  followers_complete: boolean;
  following_complete: boolean;
}

export interface LiveScanResult {
  scan_id: string;
  preview: LiveProfilePreview;
  warnings: string[];
}

export interface LiveCommitResponse extends ImportResponse {
  // Commit returns a standard ImportResponse
}
