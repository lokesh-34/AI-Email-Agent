// ============================================================
// FIREBASE INITIALIZATION
// ============================================================
//
// Initialize Firebase app and messaging for push notifications.
//
// Configuration is loaded from environment variables:
//   VITE_FIREBASE_API_KEY
//   VITE_FIREBASE_AUTH_DOMAIN
//   VITE_FIREBASE_PROJECT_ID
//   VITE_FIREBASE_MESSAGING_SENDER_ID
//   VITE_FIREBASE_APP_ID
//   VITE_FIREBASE_VAPID_KEY
// ============================================================

import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';


// ============================================================
// CONFIG
// ============================================================

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY;


// ============================================================
// INITIALIZE
// ============================================================

let app = null;
let messaging = null;

try {
  app = initializeApp(firebaseConfig);
  messaging = getMessaging(app);
} catch (error) {
  console.warn('Firebase initialization failed:', error);
}


// ============================================================
// REQUEST PERMISSION & GET TOKEN
// ============================================================

export async function requestNotificationPermission() {
  /**
   * Request browser notification permission and get
   * an FCM device token.
   *
   * Returns the FCM token string, or null if denied.
   */

  if (!messaging) {
    console.warn('Firebase messaging not initialized.');
    return null;
  }

  try {
    const permission = await Notification.requestPermission();

    if (permission !== 'granted') {
      console.log('Notification permission denied.');
      return null;
    }

    // Register the service worker
    const registration = await navigator.serviceWorker.register(
      '/firebase-messaging-sw.js'
    );

    // Get FCM token
    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: registration,
    });

    if (token) {
      console.log('FCM Token obtained:', token.substring(0, 20) + '...');
      return token;
    } else {
      console.warn('No FCM token received.');
      return null;
    }

  } catch (error) {
    console.error('Error getting notification permission:', error);
    return null;
  }
}


// ============================================================
// FOREGROUND MESSAGE HANDLER
// ============================================================

export function onForegroundMessage(callback) {
  /**
   * Listen for messages when the app is in the foreground.
   * These won't show as system notifications automatically,
   * so we handle them in the UI (e.g., show a toast).
   */

  if (!messaging) return null;

  return onMessage(messaging, (payload) => {
    console.log('Foreground message received:', payload);
    callback(payload);
  });
}


export { messaging };
