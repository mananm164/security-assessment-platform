export function formatDate(value) {
  if (!value) return 'Not set';
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium' }).format(new Date(value));
}

export function formatDateTime(value) {
  if (!value) return 'Not recorded';
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export function titleCase(value) {
  if (!value) return 'Unknown';
  return String(value).replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

export function assetIdentity(asset) {
  if (!asset) return 'Unmapped';
  return asset.display_name || asset.hostname || asset.ip_address || asset.base_url || `Asset #${asset.id}`;
}
