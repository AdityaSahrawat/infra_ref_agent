export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

export type Incident = {
	id: string;
	alert_name: string;
	severity: string;
	instance: string;
	status: string;
	started_at: string;
	received_at: string;
	ended_at?: string | null;
	created_at: string;
	root_cause?: string | null;
	llm_confidence?: number | null;
	recommended_action?: string | null;
	metrics_summary?: string;
	raw_alert?: Record<string, JsonValue>;
};

export type Action = {
	id: string;
	incident_id?: string;
	action_type: string;
	action_payload: Record<string, JsonValue>;
	status: string;
	executed_at?: string | null;
	error_message?: string | null;
};
