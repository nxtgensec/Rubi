const localApiUrl = "http://127.0.0.1:8002";

export function getApiUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV !== "production") {
    return localApiUrl;
  }
  return "";
}

export function apiPath(path: string) {
  const apiUrl = getApiUrl();
  if (!apiUrl) {
    return "";
  }
  return `${apiUrl}${path}`;
}

export function isApiConfigured() {
  return Boolean(getApiUrl());
}
