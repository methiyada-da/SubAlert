# SubAlert

> **Project Status: Work in Progress / In Development**

## Project Status

SubAlert is still under active development. Some features are incomplete and the current codebase should be treated as a portfolio mini project rather than a production-ready service.

ระบบยังอยู่ระหว่างพัฒนา และบางฟีเจอร์ยังไม่สมบูรณ์

## About the Project

SubAlert is a Django web application for keeping subscription and free-trial information in one place. It helps each signed-in user review active services, upcoming billing dates, and trial end dates, with an early-stage notification interface and LINE account integration.

## Current Features

- User registration, login, and logout
- Profile editing and password changes
- Paid-subscription and free-trial management
- Calendar-aware billing-date calculation
- Per-user dashboard and subscription search/filtering
- Ownership checks for subscription detail, update, deactivate, conversion, and deletion
- Linking a LINE account to an already authenticated SubAlert account
- Signed LINE webhook handling for follow and unfollow events
- Sending a LINE test message for a connected account
- In-app notification list and mark-all-read action for existing notification records

## In Development / Planned Features

- Automatic notification scheduling
- End-to-end reminder generation and delivery for billing and trial deadlines
- Delivery retry and operational monitoring for notifications

These workflows are not complete in the current source and are not presented as finished features.

## Tech Stack

- Python 3.13
- Django 6.1
- SQLite for local development
- HTML, CSS, and vanilla JavaScript
- LINE Login and LINE Messaging APIs
- `python-dotenv` for local environment configuration

## Project Structure

```text
accounts/       Authentication, profiles, password management, and LINE linking
config/         Django project settings and root URL configuration
dashboard/      Per-user dashboard
notifications/  Notification model, top-bar display, and read state
subscriptions/  Subscription models, forms, views, date logic, and URLs
static/         CSS and JavaScript assets
templates/      Shared and app-specific Django templates
```

## Installation

1. Clone the repository and enter the project directory.
2. Create and activate a Python virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and replace the safe placeholders with local values.
5. Apply migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the local development server:

   ```bash
   python manage.py runserver
   ```

The default example configuration supports local HTTP development on `127.0.0.1` and `localhost`.

## Environment Variables

The application recognizes the following variables. Secret values must be stored only in a local or deployment environment, never committed to Git.

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS
SECURE_HSTS_PRELOAD
EMAIL_BACKEND
LINE_LOGIN_CHANNEL_ID
LINE_LOGIN_CHANNEL_SECRET
LINE_CALLBACK_URL
LINE_MESSAGING_CHANNEL_SECRET
LINE_MESSAGING_CHANNEL_ACCESS_TOKEN
```

`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are comma-separated lists. Boolean values accept `1`, `true`, `yes`, or `on` as true values. The console email backend is the local default; a deployed environment must configure an appropriate production backend.

## LINE Integration

The current LINE flow links a LINE account to a SubAlert user who is already logged in. It is **not** a replacement for signing in to SubAlert with LINE.

Create the relevant channels in the LINE Developers Console, provide the channel credentials through environment variables, and configure `LINE_CALLBACK_URL` to match the registered callback exactly. Production must use a stable HTTPS callback URL; temporary tunnel addresses should only be used during development.

The webhook endpoint verifies the LINE signature before updating the linked account's follow status. LINE access tokens and channel secrets must never be committed.

## Testing

The project currently has 88 automated Django tests covering authentication, profile management, LINE integration, subscriptions, dashboard isolation, and existing notification behavior.

Run the checks with:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Known Limitations

- Notification scheduling and automatic reminder delivery are not implemented end to end.
- The default database is intended for local development, not production deployment.
- Production hosting, email delivery, HTTPS, and public host configuration must be supplied by the deployment environment.
- Automated tests do not yet cover browser-level JavaScript behavior.
- The UI and styles are still evolving while the project is in development.

## Security / Privacy

- `.env`, local SQLite databases, virtual environments, caches, logs, uploads, and generated static output are excluded from version control.
- Repository examples contain variable names and safe placeholders only.
- Production deployments must use a new strong `DJANGO_SECRET_KEY`, HTTPS-only cookies, HTTPS redirect, HSTS, a stable host name, and a production email backend.
- Do not publish local databases because they may contain account, email, LINE user ID, session, and subscription data.

## Author / My Responsibilities

**Author:** Methiyada

SubAlert is an individual mini project. I am responsible for requirements and data modeling, Django backend development, authentication and authorization, subscription workflows, LINE integration, UI implementation, automated tests, and project documentation.
