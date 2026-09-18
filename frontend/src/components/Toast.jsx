import { useState, useEffect } from 'react';

export default function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onClose) onClose();
    }, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  if (!message) return null;

  return (
    <div className={`toast toast-${type}`} onClick={onClose}>
      {type === 'success' && '✅ '}
      {type === 'error' && '❌ '}
      {type === 'info' && 'ℹ️ '}
      {message}
    </div>
  );
}
