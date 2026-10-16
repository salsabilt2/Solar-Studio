export type Panel = {
  id: number;
  company_id: number | null;
  maker: string;
  model: string;
  rated_w: number;
  area_m2: number;
  temp_coefficient: number;
  datasheet_url: string | null;
  published: boolean;
};

export type Setup = {
  id: number;
  project_id: number;
  panel_id: number;
  label: string;
  latitude: number;
  longitude: number;
  location_name: string;
  orientation: number;
  tilt: number;
  panel_count: number;
  roof_area_m2: number | null;
  loss_pct: number;
  rated_kw: number;
  area_m2: number;
  created_at: string;
  panel: Panel;
};

export type Project = {
  id: number;
  name: string;
  status: "active" | "completed";
  created_at: string;
  completed_at: string | null;
  setups: Setup[];
};

export type User = {
  id: number;
  email: string;
  name: string;
  role: "user" | "company" | "admin";
  tier: "free" | "unlimited";
  company_name: string | null;
};

export type Daily = {
  date: string;
  kwh: number;
  cloud_pct: number;
  hours: number;
};
export type Estimate = {
  daily: Daily[];
  day_curve: { hour: number; kwh: number }[];
  total_kwh: number;
  rated_kw: number;
  area_m2: number;
  timezone: string;
  source: string;
  model: string;
};

export type Report = {
  id: number;
  setup_id: number;
  start_date: string;
  end_date: string;
  status: string;
  email_status: string;
  error: string | null;
  total_kwh: number | null;
  daily: Daily[] | null;
  snapshot: {
    setup: Setup;
    source: string;
    model: string;
    rated_kw: number;
    area_m2: number;
  } | null;
  created_at: string;
};

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : `Request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}

export function json(method: string, body: unknown): RequestInit {
  return { method, body: JSON.stringify(body) };
}

export function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
  window.scrollTo(0, 0);
}
