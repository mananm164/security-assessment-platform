export function apiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const status = error?.response?.status;
  if (status === 401) return 'Your session has expired. Please sign in again.';
  if (status === 403) return 'You are not allowed to perform this action.';
  if (status === 404) return 'The requested record could not be found.';
  if (status >= 500) return 'The service is unavailable. Please try again later.';
  return fallback;
}
