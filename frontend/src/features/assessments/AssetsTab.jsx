import { Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { listAssets } from '../../api/assets';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import LoadingState from '../../components/LoadingState';
import { apiErrorMessage } from '../../utils/apiError';
import { assetIdentity, titleCase } from '../../utils/formatters';

export default function AssetsTab({ assessmentId }) {
  const [state, setState] = useState({ loading: true, error: '', assets: [] });
  async function load() {
    setState((current) => ({ ...current, loading: true, error: '' }));
    try { const page = await listAssets({ assessment: assessmentId }); setState({ loading: false, error: '', assets: page.items }); }
    catch (error) { setState({ loading: false, error: apiErrorMessage(error, 'Unable to load assets.'), assets: [] }); }
  }
  useEffect(() => { load(); }, [assessmentId]);
  if (state.loading) return <LoadingState label="Loading assets" />;
  if (state.error) return <ErrorState message={state.error} onRetry={load} />;
  if (!state.assets.length) return <EmptyState title="No assets recorded" message="Assets appear after authorised scanner reports are imported or created through the API." />;
  return <Card><CardContent sx={{ p: 0 }}><Table><TableHead><TableRow><TableCell>Name</TableCell><TableCell>Type</TableCell><TableCell>Host/IP/URL</TableCell><TableCell>Environment</TableCell><TableCell>Criticality</TableCell><TableCell>Internet exposed</TableCell></TableRow></TableHead><TableBody>{state.assets.map((asset) => <TableRow key={asset.id}><TableCell>{asset.display_name || assetIdentity(asset)}</TableCell><TableCell>{titleCase(asset.asset_type)}</TableCell><TableCell>{asset.hostname || asset.ip_address || asset.base_url || 'Not set'}</TableCell><TableCell>{titleCase(asset.environment)}</TableCell><TableCell>{titleCase(asset.criticality)}</TableCell><TableCell>{asset.internet_exposed ? 'Yes' : 'No'}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card>;
}
