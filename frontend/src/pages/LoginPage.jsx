import { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check for auth error in URL params
    const params = new URLSearchParams(window.location.search);
    const authError = params.get('auth_error');
    if (authError) {
      setError(`Authentication failed: ${authError.replace(/_/g, ' ')}`);
      // Clean URL
      window.history.replaceState({}, '', '/');
    }
  }, []);

  const handleGoogleLogin = () => {
    setLoading(true);
    setError('');
    // Redirect to backend Google OAuth endpoint
    window.location.href = `${API_URL}/api/auth/google/login`;
  };

  return (
    <div className="login-page">
      <div className="login-container">

        {/* Animated background orbs */}
        <div className="login-bg-orb login-bg-orb-1"></div>
        <div className="login-bg-orb login-bg-orb-2"></div>
        <div className="login-bg-orb login-bg-orb-3"></div>

        <div className="login-card">
          {/* Logo / Brand */}
          <div className="login-brand">
            <div className="login-logo">
              <span className="login-logo-icon">✉️</span>
              <div className="login-logo-pulse"></div>
            </div>
            <h1 className="login-title">AI Email Copilot</h1>
            <p className="login-subtitle">
              Your intelligent email assistant powered by AI
            </p>
          </div>

          {/* Features */}
          <div className="login-features">
            <div className="login-feature">
              <span className="login-feature-icon">📧</span>
              <span>Smart email analysis</span>
            </div>
            <div className="login-feature">
              <span className="login-feature-icon">🤖</span>
              <span>AI-generated replies</span>
            </div>
            <div className="login-feature">
              <span className="login-feature-icon">📅</span>
              <span>Automatic scheduling</span>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="login-error">
              <span>⚠️</span> {error}
            </div>
          )}

          {/* Google Sign In Button */}
          <button
            className="login-google-btn"
            onClick={handleGoogleLogin}
            disabled={loading}
            id="google-login-button"
          >
            {loading ? (
              <div className="login-spinner"></div>
            ) : (
              <>
                <svg className="login-google-icon" viewBox="0 0 24 24" width="20" height="20">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google
              </>
            )}
          </button>

          <p className="login-note">
            Connect your Gmail account to get started.
            Your emails are processed securely and never shared.
          </p>
        </div>

        {/* Footer */}
        <div className="login-footer">
          Powered by Groq AI &bull; Google Gmail API
        </div>
      </div>
    </div>
  );
}
