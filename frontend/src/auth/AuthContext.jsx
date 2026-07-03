import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, obtainToken } from '../api/auth';
import { setAccessToken, setUnauthorizedHandler } from '../api/client';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState({ user: null, access: null, refresh: null });
  const [ready, setReady] = useState(true);
  const navigate = useNavigate();

  const logout = useCallback(() => {
    setAccessToken(null);
    setSession({ user: null, access: null, refresh: null });
    navigate('/login', { replace: true });
  }, [navigate]);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  const login = useCallback(async (email, password) => {
    setReady(false);
    try {
      const token = await obtainToken(email, password);
      setAccessToken(token.access);
      const user = await getCurrentUser();
      setSession({ user, access: token.access, refresh: token.refresh });
      return user;
    } finally {
      setReady(true);
    }
  }, []);

  const value = useMemo(() => ({
    user: session.user,
    isAuthenticated: Boolean(session.user && session.access),
    ready,
    login,
    logout,
  }), [login, logout, ready, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
