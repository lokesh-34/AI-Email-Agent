# 📧 AI Email Copilot

An AI-powered email assistant that reads Gmail emails, understands them, identifies actions/deadlines/events/replies, stores structured information in MongoDB, automatically creates Google Calendar events, generates email reply drafts, and provides a web application where you can review, edit, approve, and send AI-generated emails — all protected behind Google OAuth authentication.

---

## Architecture

```
                         ┌──────────────────────────────────┐
                         │         Google OAuth 2.0          │
                         │    (Web App — JWT Auth Flow)      │
                         └──────────┬───────────────────────┘
                                    │
                                    ▼
Gmail ──► Email Collector ──► AI Understanding ──► Structured Data ──► MongoDB
                                    │
                              AI Decision Layer
                        ┌──────────┼──────────┐
                        ▼          ▼          ▼
                    Task DB    Calendar   Reply Draft
                                              │
                                    React Web App (Vite)
                                              │
                                       User Review
                                              │
                                    User Approval ──► Gmail Send
```

---

## ✨ Features

- **Google OAuth 2.0** — Secure web-based authentication with JWT tokens
- **Gmail Integration** — Read emails via Gmail API, send replies with threading
- **Automatic Email Processing** — Background watcher polls Gmail every 60s and auto-processes new emails
- **AI Email Understanding** — Groq LLM analyzes emails into structured JSON
- **Smart Reply Intelligence** — AI determines which emails actually need replies
- **General-Purpose** — Handles job, interview, invoice, banking, security, personal, and 20+ email categories
- **Task Management** — Automatic task extraction with priority and deadlines
- **Google Calendar** — Auto-create events with timezone handling and duplicate protection
- **Email Drafts** — AI-generated reply drafts with edit, approve, and send flow
- **Human-in-the-Loop** — AI never sends email without explicit user approval
- **Semantic Search** — Vector similarity search using sentence-transformers
- **Hybrid Search** — Combined keyword + semantic search
- **AI Agent Chat** — Conversational interface with rich markdown rendering (tables, lists, code)
- **Dashboard** — Stats, notifications, and quick actions
- **Idempotent Pipeline** — Safe to re-run without duplicates

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | React 18, Vite |
| Auth | Google OAuth 2.0 (Web), JWT |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Database | MongoDB Atlas |
| Email | Gmail API |
| Calendar | Google Calendar API |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Search | MongoDB Vector Search |
| Markdown | react-markdown + remark-gfm |

---

## 📁 Folder Structure

```
EmailAgent/
├── backend/
│   ├── api.py                # FastAPI application entry point
│   ├── models.py             # Pydantic request/response models
│   ├── user_store.py         # User token storage (MongoDB)
│   └── routes/
│       ├── auth.py           # Google OAuth login/callback/logout
│       ├── dashboard.py      # Dashboard statistics
│       ├── tasks.py          # Task CRUD
│       ├── drafts.py         # Draft CRUD + send
│       ├── emails.py         # Email retrieval
│       ├── calendar.py       # Calendar events
│       ├── processing.py     # Email processing trigger
│       ├── agent.py          # AI agent chat
│       └── notifications.py  # Derived notifications
│
├── frontend/
│   ├── src/
│   │   ├── api/api.js        # API service with auth headers
│   │   ├── components/       # Sidebar, Toast, SendConfirmationModal
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx     # Google OAuth login page
│   │   │   ├── Dashboard.jsx     # Stats and quick actions
│   │   │   ├── Tasks.jsx         # Task list with filters
│   │   │   ├── Drafts.jsx        # Draft management
│   │   │   ├── Calendar.jsx      # Calendar events
│   │   │   ├── Notifications.jsx # Notification feed
│   │   │   ├── EmailDetail.jsx   # Full email view
│   │   │   └── Assistant.jsx     # AI chat with markdown rendering
│   │   ├── index.css         # Design system (dark theme)
│   │   ├── App.jsx           # Router + auth guard
│   │   └── main.jsx          # Entry point
│   └── ...
│
├── tests/
│   └── test_email_copilot.py # Test suite
│
├── gmail_reader.py           # Gmail reading
├── gmail_sender.py           # Gmail sending with threading
├── email_parser.py           # AI email parsing (Groq)
├── task_manager.py           # Task creation logic
├── database.py               # MongoDB operations + vector search
├── embedding.py              # Sentence-transformer embeddings
├── agent.py                  # AI agent with tool calling
├── agent_tools.py            # Agent tools (search, query, etc.)
├── google_calendar.py        # Calendar integration
├── main.py                   # Email processing pipeline
├── credentials.json          # Google OAuth credentials (DO NOT COMMIT)
├── token.json                # OAuth token (DO NOT COMMIT)
├── .env                      # Environment variables (DO NOT COMMIT)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## 🚀 Setup

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Gmail API**
   - **Google Calendar API**
4. Go to **APIs & Services → Credentials**
5. Create **OAuth 2.0 Client ID** → choose **Web application**
6. Add the following **Authorized redirect URI**:
   ```
   http://localhost:8000/api/auth/google/callback
   ```
7. Download the credentials JSON and save as `credentials.json` in the `EmailAgent/` directory

> **⚠️ Important:** You must use **Web application** type (not Desktop app). The redirect URI must exactly match `http://localhost:8000/api/auth/google/callback`.

### 2. OAuth Scopes

The application requests these scopes during login:

| Scope | Purpose |
|-------|---------|
| `openid` | OpenID Connect authentication |
| `userinfo.email` | Read user email address |
| `userinfo.profile` | Read user name and picture |
| `gmail.readonly` | Read emails |
| `gmail.send` | Send emails |
| `calendar` | Manage calendar events |

### 3. MongoDB Atlas Setup

1. Create a free cluster at [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a database user
3. Whitelist your IP in **Network Access**
4. Get the connection URI
5. Create a **Vector Search Index** named `vector_index` on the `tasks` collection with:
   - Field: `embedding`
   - Dimensions: `384`
   - Similarity: `cosine`

### 4. Groq Setup

1. Get an API key from [Groq Console](https://console.groq.com/)
2. The app uses model `openai/gpt-oss-120b`

### 5. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# AI
GROQ_API_KEY=your_groq_api_key

# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net

# Google OAuth (from credentials.json)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# JWT
JWT_SECRET=your-secure-random-secret
JWT_EXPIRY_HOURS=24
```

### 6. Install Dependencies

**Python (Backend):**

```bash
pip install fastapi uvicorn groq pymongo python-dotenv sentence-transformers google-auth google-auth-oauthlib google-api-python-client beautifulsoup4 PyJWT requests httpx pytest
```

**Node.js (Frontend):**

```bash
cd frontend
npm install
```

---

## ▶️ Running

### Backend

> **⚠️ Must be run from the `EmailAgent/` root directory — not from `backend/`**

```bash
cd EmailAgent
python -m uvicorn backend.api:app --reload
```

The API will be available at **http://localhost:8000**

### Frontend

```bash
cd EmailAgent/frontend
npm run dev
```

The UI will be available at **http://localhost:5173**

### Authentication Flow

1. Open **http://localhost:5173** in your browser
2. Click **"Sign in with Google"**
3. Authorize the app in Google's consent screen
4. You'll be redirected back to the dashboard, authenticated

---

## 🧪 Testing

```bash
cd EmailAgent
python -m pytest tests/ -v
```

---

## 📡 API Endpoints

### Public (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/auth/google/login` | Initiate Google OAuth |
| GET | `/api/auth/google/callback` | OAuth callback (Google redirects here) |

### Protected (JWT Required)

All protected endpoints require `Authorization: Bearer <jwt_token>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/logout` | Sign out (removes stored tokens) |
| GET | `/api/dashboard` | Dashboard statistics |
| GET | `/api/notifications` | Derived notifications |
| GET | `/api/tasks` | List tasks (`?status=pending`) |
| GET | `/api/tasks/{message_id}` | Get single task |
| POST | `/api/tasks/{message_id}/complete` | Mark task complete |
| GET | `/api/emails/{message_id}` | Get original email |
| GET | `/api/drafts` | List drafts (`?status=draft`) |
| GET | `/api/drafts/{draft_id}` | Get single draft |
| PUT | `/api/drafts/{draft_id}` | Update draft body/subject |
| POST | `/api/drafts/{draft_id}/approve` | Approve draft |
| POST | `/api/drafts/{draft_id}/send` | Send email via Gmail |
| POST | `/api/drafts/{draft_id}/reject` | Reject draft |
| GET | `/api/calendar/events` | Upcoming calendar events |
| POST | `/api/process-emails` | Process new emails from inbox |
| POST | `/api/agent/chat` | Chat with AI agent |

---

## 📋 Example Workflow

1. **Open Dashboard** → Click **"Process Emails"**
2. **AI processes inbox** → Creates tasks, calendar events, and reply drafts
3. **Dashboard shows** → `3 Pending Tasks`, `1 High Priority`, `2 Draft Replies`
4. **Open Drafts** → See AI-generated reply to recruiter
5. **Edit if needed** → Modify recipient/subject/body
6. **Click "Review & Send"** → Confirmation modal appears
7. **Click "Send Email"** → Email sent via Gmail with proper threading
8. **Draft status** → Changes to "sent" with Gmail message ID
9. **Chat with Assistant** → Ask "Show my pending tasks" → rendered as formatted table

---

## 🔒 Security

- **Google OAuth 2.0** web application flow with JWT session tokens
- OAuth tokens stored securely in MongoDB (per-user)
- CORS restricted to `localhost:5173` and `localhost:3000`
- All protected routes require valid JWT via `Authorization: Bearer` header
- Email sending requires **explicit user approval** through the UI
- Only drafts stored in MongoDB can be sent
- All API inputs validated with Pydantic
- No secrets logged

---

## ⚠️ Known Limitations

- Email processing is synchronous (can be slow for many emails)
- Groq free tier has rate limits (auto-retries with backoff)
- Embedding model loads at startup (first request may be slow)
- MongoDB Atlas free tier has connection limits
- `.env` values are overridden by system environment variables — use `load_dotenv(override=True)` if needed

---

## 🔮 Future Improvements

- Background processing with Celery/APScheduler
- Multiple Gmail account support
- Email thread visualization
- Draft regeneration with AI
- Smart notification scheduling
- Mobile-responsive sidebar toggle
- WebSocket real-time updates
- Email attachment handling

---

## 📜 License

This project is for academic/personal use.
