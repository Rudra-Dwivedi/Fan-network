# Fan Network

A social platform that matches people by taste across movies, music, and sports, and helps groups decide what to watch or listen to together using a hybrid recommendation engine.

---

## Features

- **Personalized Recommendations & Social Matching**:
  - Item rating system ($1-5$ stars) across movies, music tracks, and sports teams.
  - Cosine similarity matching (`/recommend/people`) to discover members with identical tastes.
  - Social graph with follow/unfollow capabilities and public user profiles (`/recommend/user/<username>`).

- **Group Pick Engine**:
  - Multi-user joint recommendation aggregation (`/recommend/group`).
  - Supports configurable strategies: **Average** (maximum group satisfaction) and **Least Misery** (minimizes worst-case disappointment).
  - Clean member picker filtered strictly to community members you actively follow.

- **High-Definition Media Resolution**:
  - Automated artwork fetching: 1000px+ official theatrical studio posters (IMDb CDN), $1000 \times 1000$ Apple Music square covers, and transparent sports crests (TheSportsDB).
  - High-DPI / Retina anti-aliasing and optimized aspect ratios.

- **User Profile Photos**:
  - Every member can upload custom profile photos (PNG, JPG, WEBP) or link external image URLs (`/auth/profile`).
  - Photos display seamlessly across navigation, public profiles, feed posts, group picks, and admin moderation tables.
  - One-click removal reverts to initial-based colored avatars.

- **Community Feed & Sentiment Analysis**:
  - Live feed (`/feed/`) with polarity scoring and sentiment classification.
  - Admin announcements pinned to the top of the feed.

- **Admin Governance & Moderation**:
  - Dedicated administrative portal (`/admin/dashboard`) backed by Role-Based Access Control (RBAC).
  - **User Directory**: Search, inspect detailed activity profiles, suspend/reactivate accounts, and manage admin roles.
  - **Moderation**: Filter and purge abusive posts and spam ratings.
  - **Catalog Management**: Add, delete, and automatically resolve high-definition artwork for movies, songs, and teams.
  - **Activity Stream**: Real-time event log tracking registrations, posts, and ratings.

---

## Quick Start

### 1. Clone & Install Dependencies

```bash
git clone <repository-url>
cd fan_network
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```
*The SQLite database schema initializes automatically on first startup.*
Open **http://127.0.0.1:5000** in your browser. You can create accounts anytime via **Join free** (`/auth/register`).

### 3. Create an Administrator Account

```bash
python create_admin.py
```
*Follow the interactive prompts to create an administrator account for access to the Admin Portal (`/admin/login`).*

---

## Project Structure

```
fan_network/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── db.py                # Database connection & schema migrations
│   ├── schema.sql           # SQLite schema definitions
│   ├── auth_utils.py        # RBAC decorators (login_required, admin_required)
│   ├── routes/
│   │   ├── auth.py          # Registration, login, logout, and profile photo settings
│   │   ├── admin.py         # Admin dashboard, users, posts, ratings, and catalog
│   │   ├── items.py         # Browse catalog & rate items
│   │   ├── recommend.py     # Discover similar people, public profiles, and group picks
│   │   ├── feed.py          # Community feed and pinned announcements
│   │   └── settings.py      # API key configurations
│   ├── services/
│   │   ├── recommender.py   # Taste vectors, cosine similarity, group aggregation
│   │   ├── sentiment.py     # Sentiment analysis scorer
│   │   ├── image_fetcher.py # HD artwork discovery service (IMDb, iTunes, TheSportsDB)
│   │   ├── item_media.py    # Media resolution helper
│   │   ├── settings_store.py# API key storage
│   │   ├── tmdb_client.py   # TMDB client
│   │   ├── spotify_client.py# Spotify search client
│   │   └── sports_client.py # Sports API client
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       ├── style.css        # Responsive CSS theme
│       └── avatars/         # Uploaded user profile photos
├── config.py                # App configuration
├── create_admin.py          # CLI admin creation tool
├── requirements.txt         # Python package dependencies
├── run.py                   # Development server runner
└── README.md                # Documentation
```

---

## License

MIT License.
