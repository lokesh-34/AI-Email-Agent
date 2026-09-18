// ============================================================
// FIREBASE MESSAGING SERVICE WORKER
// ============================================================
// Handles background push notifications when the app
// is not in focus or the browser tab is closed.
// ============================================================

importScripts('https://www.gstatic.com/firebasejs/11.8.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.8.1/firebase-messaging-compat.js');


// Firebase config (must be hardcoded in service worker)
const firebaseConfig = {
  apiKey: 'AIzaSyCTML-Q_bB71sCfHWTLYVG02eFyoJhAQgE',
  authDomain: 'ai-agent-3744b.firebaseapp.com',
  projectId: 'ai-agent-3744b',
  storageBucket: 'ai-agent-3744b.firebasestorage.app',
  messagingSenderId: '49646870001',
  appId: '1:49646870001:web:197b776cf21d7915bfb850',
};

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();


// ============================================================
// BACKGROUND MESSAGE HANDLER
// ============================================================

messaging.onBackgroundMessage((payload) => {
  console.log('[SW] Background message received:', payload);

  const title = payload.notification?.title || '📬 New Email Activity';
  const body = payload.notification?.body || 'You have new email updates.';

  const options = {
    body: body,
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: 'email-copilot-notification',
    renotify: true,
    data: payload.data || {},
    actions: [
      { action: 'open', title: 'Open App' },
      { action: 'dismiss', title: 'Dismiss' },
    ],
  };

  self.registration.showNotification(title, options);
});


// ============================================================
// NOTIFICATION CLICK HANDLER
// ============================================================

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const urlToOpen = event.notification.data?.click_action
    || self.location.origin;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Focus existing tab if open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus();
          }
        }
        // Otherwise open new tab
        return clients.openWindow(urlToOpen);
      })
  );
});
