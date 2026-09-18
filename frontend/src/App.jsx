import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Notifications from './pages/Notifications';
import Tasks from './pages/Tasks';
import Drafts from './pages/Drafts';
import Calendar from './pages/Calendar';
import EmailDetail from './pages/EmailDetail';
import Assistant from './pages/Assistant';
import LoginPage from './pages/LoginPage';
import Toast from './components/Toast';
import { registerPushToken } from './api/api';
import { requestNotificationPermission, onForegroundMessage } from './firebase';


// ============================================================
// AUTH HELPERS
// ============================================================

function getStoredAuth() {
  const token = localStorage.getItem('auth_token');
  const email = localStorage.getItem('auth_email');
  const name = localStorage.getItem('auth_name');
  const picture = localStorage.getItem('auth_picture');

  if (token && email) {
    return { token, email, name: name || '', picture: picture || '' };
  }
  return null;
}

function storeAuth(token, email, name, picture) {
  localStorage.setItem('auth_token', token);
  localStorage.setItem('auth_email', email);
  localStorage.setItem('auth_name', name || '');
  localStorage.setItem('auth_picture', picture || '');
}

function clearAuth() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_email');
  localStorage.removeItem('auth_name');
  localStorage.removeItem('auth_picture');
}


// ============================================================
// PUSH NOTIFICATION SETUP
// ============================================================

async function setupPushNotifications() {
  try {
    const fcmToken = await requestNotificationPermission();

    if (fcmToken) {
      // Register token with backend
      await registerPushToken(fcmToken);
      console.log('Push notifications enabled.');
    }
  } catch (error) {
    console.warn('Push notification setup failed:', error);
  }
}


// ============================================================
// APP
// ============================================================

export default function App() {
  const [auth, setAuth] = useState(null);
  const [checking, setChecking] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    // Check for token in URL (from Google OAuth callback)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlEmail = params.get('email');
    const urlName = params.get('name');
    const urlPicture = params.get('picture');

    if (urlToken && urlEmail) {
      storeAuth(urlToken, urlEmail, urlName, urlPicture);
      setAuth({
        token: urlToken,
        email: urlEmail,
        name: urlName || '',
        picture: urlPicture || '',
      });
      // Clean URL
      window.history.replaceState({}, '', '/');
    } else {
      // Check localStorage
      const stored = getStoredAuth();
      if (stored) {
        setAuth(stored);
      }
    }

    setChecking(false);
  }, []);

  // Setup push notifications after authentication
  useEffect(() => {
    if (!auth) return;

    // Request permission and register FCM token
    setupPushNotifications();

    // Listen for foreground messages and show as toast
    const unsubscribe = onForegroundMessage((payload) => {
      const title = payload.notification?.title || 'New Notification';
      const body = payload.notification?.body || '';
      setToast({
        message: `${title}: ${body}`,
        type: 'info',
      });
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [auth]);

  const handleLogout = () => {
    clearAuth();
    setAuth(null);
  };

  // Still checking auth
  if (checking) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-spinner" style={{ width: 40, height: 40 }}></div>
        </div>
      </div>
    );
  }

  // Not authenticated → show login
  if (!auth) {
    return <LoginPage />;
  }

  // Authenticated → show app
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar
          user={auth}
          onLogout={handleLogout}
        />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/drafts" element={<Drafts />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/email/:messageId" element={<EmailDetail />} />
            <Route path="/assistant" element={<Assistant />} />
          </Routes>
        </main>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </BrowserRouter>
  );
}
