const localApiUrl = "http://127.0.0.1:8002";
const vercelBackendPath = "/_/backend";

function normalizeUrl(url: string) {
  return url.replace(/\/$/, "");
}

function vercelDeploymentUrl() {
  const vercelUrl = process.env.VERCEL_URL?.trim();
  if (!vercelUrl) {
    return "";
  }
  return `https://${vercelUrl}`;
}

export function getApiUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredUrl) {
    const normalizedUrl = normalizeUrl(configuredUrl);
    if (normalizedUrl.startsWith("/")) {
      const deploymentUrl = vercelDeploymentUrl();
      return deploymentUrl ? `${deploymentUrl}${normalizedUrl}` : normalizedUrl;
    }
    return normalizedUrl;
  }
  if (process.env.NODE_ENV !== "production") {
    return localApiUrl;
  }
  const deploymentUrl = vercelDeploymentUrl();
  if (deploymentUrl) {
    return `${deploymentUrl}${vercelBackendPath}`;
  }
  if (typeof window !== "undefined") {
    return vercelBackendPath;
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
