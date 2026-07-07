function firstDetail(data) {
  if (!data) return '';
  if (typeof data === 'string') return data;
  if (Array.isArray(data)) return firstDetail(data[0]);
  if (typeof data === 'object') {
    if (data.detail) return firstDetail(data.detail);
    const first = Object.values(data)[0];
    return firstDetail(first);
  }
  return '';
}

export function apiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const status = error?.response?.status;
  if (status === 401) return 'Your session has expired. Please sign in again.';
  if (status === 403) return 'You are not allowed to perform this action.';
  if (status === 404) return 'The requested record could not be found.';
  if (status === 410) return firstDetail(error?.response?.data) || 'This preview has expired. Upload the report again.';
  if (status === 400) return firstDetail(error?.response?.data) || fallback;
  if (status >= 500) return 'The service is unavailable. Please try again later.';
  return fallback;
}
