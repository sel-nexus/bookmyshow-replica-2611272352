/** Provide development configuration without a baked-in host. */
export const environment = { apiBaseUrl: (globalThis as { __env?: { API_BASE_URL?: string } }).__env?.API_BASE_URL ?? '' };
