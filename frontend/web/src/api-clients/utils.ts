export function buildAuthHeaders(token: string | null): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}
