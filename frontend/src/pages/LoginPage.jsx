import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { Alert, Box, Button, Card, CardContent, IconButton, InputAdornment, Stack, TextField, Typography } from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import AuthLayout from '../layouts/AuthLayout';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/assessments', { replace: true });
    } catch {
      setError('Unable to sign in with the supplied credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <Card sx={{ mx: 'auto', maxWidth: 460 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" component="h1">SARP</Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>Security Assessment & Risk Management Platform</Typography>
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Stack spacing={2.5}>
              {error ? <Alert severity="error" aria-live="polite">{error}</Alert> : null}
              <TextField label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
              <TextField label="Password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" slotProps={{ input: { endAdornment: <InputAdornment position="end"><IconButton aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((value) => !value)} edge="end">{showPassword ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment> } }} />
              <Button type="submit" variant="contained" size="large" disabled={loading || !email || !password}>{loading ? 'Signing in...' : 'Sign in'}</Button>
              <Typography variant="caption" color="text.secondary">Use fictional demo data only. Browser refresh clears the in-memory session.</Typography>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}
