import { useAuthStore } from '../hooks/useAuth';

export function LoginPage() {
  const { demoLogin } = useAuthStore();

  const handleDemoLogin = async () => {
    try {
      await demoLogin();
    } catch (error) {
      console.error('Demo login failed:', error);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: 'calc(100vh - 200px)' 
    }}>
      <div className="card" style={{ maxWidth: '400px', width: '100%' }}>
        <h1 style={{ textAlign: 'center', marginBottom: 'var(--spacing-lg)' }}>Signal Console</h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-xl)' }}>
          Production-grade engineering skills platform for AI coding agents
        </p>
        
        <div className="alert alert-info" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <strong>Demo Mode</strong> - Click below to log in as a demo user with viewer, analyst, and operator roles.
        </div>

        <button 
          onClick={handleDemoLogin}
          className="btn btn-primary"
          style={{ width: '100%', padding: 'var(--spacing-md)', fontSize: '1rem' }}
        >
          Demo Login
        </button>

        <div style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', background: 'var(--color-bg)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          <h4 style={{ marginBottom: 'var(--spacing-sm)' }}>OIDC Configuration</h4>
          <p style={{ color: 'var(--color-text-muted)' }}>
            For production, configure Keycloak OIDC with the following environment variables:
          </p>
          <ul style={{ marginTop: 'var(--spacing-sm)', paddingLeft: 'var(--spacing-lg)', color: 'var(--color-text-muted)' }}>
            <li>OIDC_ISSUER_URL</li>
            <li>OIDC_CLIENT_ID</li>
            <li>OIDC_CLIENT_SECRET</li>
            <li>OIDC_REDIRECT_URI</li>
          </ul>
        </div>
      </div>
    </div>
  );
}