// ============================================================
// API SERVICE
// ============================================================

const API_URL = import.meta.env.VITE_API_URL || 'https://ai-email-agent-duvi.onrender.com';


// ============================================================
// AUTH TOKEN HELPER
// ============================================================

function getAuthHeaders() {
  const token = localStorage.getItem('auth_token');
  if (token) {
    return { 'Authorization': `Bearer ${token}` };
  }
  return {};
}


// ============================================================
// BASE REQUEST
// ============================================================

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  // Handle 401 — redirect to login
  if (response.status === 401) {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_email');
    localStorage.removeItem('auth_name');
    localStorage.removeItem('auth_picture');
    window.location.href = '/';
    throw new Error('Session expired. Please sign in again.');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `Request failed with status ${response.status}`
    }));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}


// ============================================================
// API FUNCTIONS
// ============================================================

// Dashboard
export const getDashboard = () => request('/api/dashboard');

// Notifications
export const getNotifications = () => request('/api/notifications');

// Tasks
export const getTasks = (status) => {
  const query = status ? `?status=${status}` : '';
  return request(`/api/tasks${query}`);
};

export const getTask = (messageId) => request(`/api/tasks/${messageId}`);

export const completeTask = (messageId) =>
  request(`/api/tasks/${messageId}/complete`, { method: 'POST' });

// Emails
export const getEmail = (messageId) => request(`/api/emails/${messageId}`);

// Drafts
export const getDrafts = (status) => {
  const query = status ? `?status=${status}` : '';
  return request(`/api/drafts${query}`);
};

export const getDraft = (draftId) => request(`/api/drafts/${draftId}`);

export const updateDraft = (draftId, data) =>
  request(`/api/drafts/${draftId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const approveDraft = (draftId) =>
  request(`/api/drafts/${draftId}/approve`, { method: 'POST' });

export const sendDraft = (draftId) =>
  request(`/api/drafts/${draftId}/send`, { method: 'POST' });

export const rejectDraft = (draftId) =>
  request(`/api/drafts/${draftId}/reject`, { method: 'POST' });

// Calendar
export const getCalendarEvents = (maxResults = 20) =>
  request(`/api/calendar/events?max_results=${maxResults}`);

// Processing
export const processEmails = (maxResults = 10) =>
  request(`/api/process-emails?max_results=${maxResults}`, { method: 'POST' });

// Agent
export const agentChat = (message, conversationHistory = []) =>
  request('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_history: conversationHistory }),
  });

// Health
export const healthCheck = () => request('/api/health');

// Auth
export const getMe = () => request('/api/auth/me');

export const logout = () =>
  request('/api/auth/logout', { method: 'POST' });

// Push Notifications
export const registerPushToken = (token) =>
  request('/api/push/register', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });

export const unregisterPushToken = (token) =>
  request('/api/push/unregister', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });

export const testPushNotification = () =>
  request('/api/push/test', { method: 'POST' });
