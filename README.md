# Gaming Sessions Django Application

A Django application for managing gaming account sessions with role-based access control and automatic data retention.

## Features

- **Account Management**: Store account details including nick, country, email, phone
- **Payment Information**: Track withdrawal passwords and minimum balances
- **Play Sessions**: Record daily gaming activity with automatic 60-day retention
- **Web Interface**: Full-featured web UI for managing sessions and accounts
- **Role-Based Access Control**:
  - Regular users can only view/edit sessions they created (within 60 days)
  - Superusers can view/edit all sessions including historical data beyond 60 days
  - Only superusers can create and manage accounts
- **REST API**: Full CRUD operations via Django REST Framework
- **Docker Support**: Containerized application with PostgreSQL database

## Project Structure

```
gaming_sessions/
├── config/                 # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/              # Main application
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── permissions.py     # Custom permissions
│   ├── admin.py           # Django admin config
│   ├── urls.py            # App URLs
│   └── tests.py           # Unit tests
├── docker-compose.yml     # Docker composition
├── Dockerfile            # Docker image definition
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md            # This file
```

## Database Schema

### Models

1. **AccountDetail** (acc_details table)
   - nick (unique)
   - country
   - email (unique)
   - phone
   - user (OneToOne with Django User)

2. **Payment** (payment table)
   - withdraw_pass
   - min_balance
   - account (OneToOne with AccountDetail)

3. **PlaySession** (play_sessions table)
   - account (ForeignKey to AccountDetail)
   - session_date
   - is_active
   - notes
   - created_by (ForeignKey to User)
   - Automatic 60-day retention via custom manager

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- Git (optional)

### Installation

1. **Clone or download the project**:
   ```bash
   cd gaming_sessions
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the SECRET_KEY for production.

3. **Build and start Docker containers**:
   ```bash
   docker-compose up --build
   ```

4. **Run migrations** (in a new terminal):
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**:
   - Web Interface: http://localhost:8000/
   - Django Admin: http://localhost:8000/admin
   - API Root: http://localhost:8000/api/

## Web Interface

The application includes a full web interface for managing sessions and accounts.

### For Regular Users

After logging in at http://localhost:8000/login, regular users can:

1. **Dashboard**: View overview of their sessions and statistics
2. **Sessions List**: View all their sessions (within 60 days)
3. **Create Session**: Add new gaming sessions for any account
4. **Edit/Delete Sessions**: Modify or remove sessions they created
5. **Filter Sessions**: Filter by account, date range

### For Superusers

Superusers have additional capabilities:

1. **Manage Accounts**: Create, edit, and delete gaming accounts
2. **View All Sessions**: See sessions created by all users
3. **Historical Data**: Access sessions older than 60 days
4. **Account Sessions**: View complete session history for any account

### Navigation

- **Dashboard** (`/`): Overview with statistics and quick actions
- **Sessions** (`/sessions/`): List and manage gaming sessions
- **Accounts** (`/accounts/`): Manage accounts (superuser only)
- **Login/Logout**: Authentication pages

## API Endpoints

### Accounts
- `GET /api/accounts/` - List all accounts
- `POST /api/accounts/` - Create new account
- `GET /api/accounts/{id}/` - Get account details
- `PUT /api/accounts/{id}/` - Update account
- `DELETE /api/accounts/{id}/` - Delete account

### Payments
- `GET /api/payments/` - List all payments
- `POST /api/payments/` - Create payment info
- `GET /api/payments/{id}/` - Get payment details
- `PUT /api/payments/{id}/` - Update payment
- `DELETE /api/payments/{id}/` - Delete payment

### Play Sessions
- `GET /api/sessions/` - List sessions (filtered by user role)
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{id}/` - Get session details
- `PUT /api/sessions/{id}/` - Update session (if owner or superuser)
- `DELETE /api/sessions/{id}/` - Delete session (if owner or superuser)
- `GET /api/sessions/my_sessions/` - Get current user's sessions
- `GET /api/sessions/old_sessions/` - Get sessions older than 60 days (superuser only)
- `GET /api/sessions/by_account/?account_id=X` - Get sessions for specific account
- `GET /api/sessions/date_range/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get sessions in date range

## Usage Examples

### Creating a Play Session (via API)

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "account": 1,
    "session_date": "2026-01-27",
    "is_active": true,
    "notes": "Regular gaming session"
  }'
```

### Getting Sessions by Date Range

```bash
curl http://localhost:8000/api/sessions/date_range/?start_date=2026-01-01&end_date=2026-01-27
```

## Permission System

### Regular Users
- Can create sessions for any account
- Can only view/edit/delete sessions they created
- Cannot see sessions older than 60 days
- Cannot access `/api/sessions/old_sessions/` endpoint

### Superusers
- Can view/edit/delete all sessions
- Can see sessions beyond the 60-day retention period
- Can access `/api/sessions/old_sessions/` endpoint
- Full access to Django Admin interface

## Data Retention

The application automatically filters play sessions to show only the last 60 days of data for regular users. This is implemented through a custom model manager (`PlaySessionManager`).

To access all sessions including old ones (superuser only):
```python
PlaySession.objects.all_including_old()
```

## Running Tests

```bash
docker-compose exec web python manage.py test
```

## Management Commands

### Create migrations
```bash
docker-compose exec web python manage.py makemigrations
```

### Apply migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run development server
```bash
docker-compose exec web python manage.py runserver 0.0.0.0:8000
```

## Stopping the Application

```bash
docker-compose down
```

To remove volumes (database data):
```bash
docker-compose down -v
```

## Production Considerations

Before deploying to production:

1. Change `SECRET_KEY` in `.env`
2. Set `DEBUG=False` in `.env`
3. Update `ALLOWED_HOSTS` in `.env`
4. Use a production WSGI server (Gunicorn is included)
5. Set up proper database backups
6. Configure HTTPS/SSL
7. Set up static file serving (use collectstatic)

## License

This project is provided as-is for educational purposes.
