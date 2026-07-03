import AssessmentIcon from '@mui/icons-material/AssignmentOutlined';
import DashboardIcon from '@mui/icons-material/DashboardOutlined';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import { AppBar, Box, Chip, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from '@mui/material';
import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { titleCase } from '../utils/formatters';

const drawerWidth = 240;

function NavigationContent({ onNavigate }) {
  const location = useLocation();
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0f172a', color: '#e2e8f0' }}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ color: 'white' }}>SARP</Typography>
        <Typography variant="caption" sx={{ color: '#94a3b8' }}>Consultant workspace</Typography>
      </Box>
      <List sx={{ px: 1 }}>
        <ListItemButton component={Link} to="/dashboard" selected={location.pathname.startsWith('/dashboard')} onClick={onNavigate} sx={{ borderRadius: 2, color: 'inherit', '&.Mui-selected': { bgcolor: 'rgba(37,99,235,0.2)', color: 'white' } }}>
          <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}><DashboardIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItemButton>
        <ListItemButton component={Link} to="/assessments" selected={location.pathname.startsWith('/assessments')} onClick={onNavigate} sx={{ borderRadius: 2, color: 'inherit', '&.Mui-selected': { bgcolor: 'rgba(37,99,235,0.2)', color: 'white' } }}>
          <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Assessments" />
        </ListItemButton>
      </List>
    </Box>
  );
}

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="fixed" color="inherit" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider', ml: { md: `${drawerWidth}px` }, width: { md: `calc(100% - ${drawerWidth}px)` } }}>
        <Toolbar sx={{ minHeight: 64 }}>
          <IconButton aria-label="Open navigation" edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 2, display: { md: 'none' } }}><MenuIcon /></IconButton>
          <Typography sx={{ flexGrow: 1 }} color="text.secondary">Security Assessment & Risk Management Platform</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'right' }}>
              <Typography variant="body2">{displayName}</Typography>
              <Chip size="small" label={titleCase(user?.role)} variant="outlined" />
            </Box>
            <IconButton aria-label="Sign out" onClick={logout}><LogoutIcon /></IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)} ModalProps={{ keepMounted: true }} sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: drawerWidth } }}>
          <NavigationContent onNavigate={() => setMobileOpen(false)} />
        </Drawer>
        <Drawer variant="permanent" sx={{ display: { xs: 'none', md: 'block' }, '& .MuiDrawer-paper': { width: drawerWidth, border: 0 } }} open>
          <NavigationContent />
        </Drawer>
      </Box>
      <Box component="main" sx={{ flexGrow: 1, pt: '64px', minWidth: 0 }}>
        <Box sx={{ maxWidth: 1440, mx: 'auto', p: { xs: 2, md: 3 } }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
