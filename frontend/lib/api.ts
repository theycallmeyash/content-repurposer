const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL ?? "http://127.0.0.1:8788";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export interface ScrapeSummary {
  posts: number;
  comments: number;
  collected_tweets: number;
  analysis?: {
    tone_vectors?: Array<{ k: string; v: number }>;
    highlights?: string[];
    top_tweets?: Array<Record<string, unknown>>;
    bottom_tweets?: Array<Record<string, unknown>>;
    raw?: Record<string, unknown>;
  };
}

export interface RepurposedContent {
  core_analysis: string;
  twitter_thread: string[];
  linkedin_post: string;
  instagram_caption: string;
  tldr: string;
}

export function analyzeXProfile(username: string, limit = 50) {
  return apiFetch<ScrapeSummary>("/profile/x/analyze", {
    method: "POST",
    body: { username, limit },
  });
}

export function repurposeContent(input: {
  content: string;
  provider: string;
  api_key?: string;
  trends?: { platform: string; keywords: string[] };
}) {
  return apiFetch<RepurposedContent>("/repurpose", {
    method: "POST",
    body: input,
  });
}

export function extractContent(input: { source: string; input_type: "text" | "blog" | "youtube" }) {
  return apiFetch<{ content: string; characters: number }>("/extract", {
    method: "POST",
    body: input,
  });
}

export function getXAuthStatus() {
  return apiFetch<{ cookies_present: boolean; cookies_path: string }>("/auth/x/status");
}

export function importXCookies(cookiesJson: string) {
  return apiFetch<{ ok: boolean; message: string; cookies_path: string }>("/auth/x/cookies", {
    method: "POST",
    body: { cookies_json: cookiesJson },
  });
}
