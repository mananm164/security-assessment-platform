export const RAW_DATA_ROLES = new Set(['ADMIN', 'CONSULTANT', 'MANAGER']);
export const WRITE_ROLES = new Set(['ADMIN', 'CONSULTANT']);

export function canSeeRawScannerData(role) {
  return RAW_DATA_ROLES.has(role);
}

export function canWriteTechnicalRecords(role) {
  return WRITE_ROLES.has(role);
}
