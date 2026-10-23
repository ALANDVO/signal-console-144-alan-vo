import { ReactNode } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';

export function Layout({ children }: { children?: ReactNode }) {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuthStore();

  const navLinks = [
    { path: '/skills', label: 'Skills' },
    { path: '/evaluations', label: 'Evaluations' },
    { path: '/drift', label: 'Drift Reports' },
    { path: '/audit', label: 'Audit Logs' },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        padding: '0 var(--spacing-md)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div className="container" style={{ height: '64px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link to="/" style={{ fontWeight: 700, fontSize: '1.25rem', color: 'var(--color-primary)', textDecoration: 'none' }}>
            Signal Console
          </Link>
          
          <nav style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
            {isAuthenticated && (
              <>
                <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                  {navLinks.map((link) => (
                    <Link
                      key={link.path}
                      to={link.path}
                      style={{
                        padding: 'var(--spacing-xs) var(--spacing-sm)',
                        borderRadius: 'var(--radius-sm)',
                        fontWeight: 500,
                        fontSize: '0.875rem',
                        color: location.pathname.startsWith(link.path) ? 'var(--color-primary)' : 'var(--color-text-muted)',
                        background: location.pathname.startsWith(link.path) ? 'var(--color-bg)' : 'transparent',
                        textDecoration: 'none',
                      }}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    {user?.name || user?.user_id}
                  </span>
                  <span className="badge badge-info" style={{ fontSize: '0.7rem', textTransform: 'capitalize' }}>
                    {user?.roles[0] || 'viewer'}
                  </span>
                  <button onClick={logout} className="btn btn-ghost" style={{ fontSize: '0.875rem' }}>
                    Logout
                  </button>
                </div>
              </>
            )}
          </nav>
        </div>
      </header>

      <main style={{ flex: 1, padding: 'var(--spacing-lg) 0' }}>
        <div className="container">
          {children ?? <Outlet />}
        </div>
      </main>

      <footer style={{
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        padding: 'var(--spacing-md) 0',
        marginTop: 'auto',
      }}>
        <div className="container" style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          Signal Console - AI Agent Skills Platform | Alan Vo <span>alanvo@gmail.com</span>
        </div>
      </footer>
    </div>
  );
}