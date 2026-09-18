import { useState, useEffect } from 'react';
import { getCalendarEvents } from '../api/api';

export default function Calendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    try {
      const data = await getCalendarEvents(20);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load calendar events:', err);
    } finally {
      setLoading(false);
    }
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading calendar events...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Calendar</h2>
        <p>Upcoming events from your emails</p>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h3>No upcoming events</h3>
          <p>Calendar events are automatically created when emails contain meetings, interviews, or scheduled activities.</p>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event, i) => (
            <div key={event.event_id || i} className="event-card">
              <div className="event-title">📅 {event.title || 'Untitled Event'}</div>

              <div className="event-info">
                🕐 {formatDateTime(event.start)}
              </div>

              {event.end && (
                <div className="event-info">
                  🏁 {formatDateTime(event.end)}
                </div>
              )}

              {event.location && (
                <div className="event-info">
                  📍 {event.location}
                </div>
              )}

              {event.description && (
                <div className="event-info" style={{ marginTop: '8px', lineHeight: '1.5' }}>
                  {event.description}
                </div>
              )}

              {event.html_link && (
                <a
                  href={event.html_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="event-link"
                >
                  🔗 Open in Google Calendar
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
