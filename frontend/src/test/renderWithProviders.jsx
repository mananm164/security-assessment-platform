import { ThemeProvider } from '@mui/material';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../auth/AuthContext';
import { theme } from '../theme/theme';

export function renderWithProviders(ui, { route = '/', authValue } = {}) {
  const defaultAuth = {
    user: { email: 'consultant@example.test', role: 'CONSULTANT' },
    isAuthenticated: true,
    ready: true,
    login: vi.fn(),
    logout: vi.fn(),
  };
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[route]}>
        <AuthContext.Provider value={authValue || defaultAuth}>{ui}</AuthContext.Provider>
      </MemoryRouter>
    </ThemeProvider>,
  );
}
