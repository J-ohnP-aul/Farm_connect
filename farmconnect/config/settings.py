"""
Django settings for the Local Farm Map V1 prototype.

Design sources: design/database/database-design.md and
design/system/system-design.md. Values marked "my call" there are
surfaced below as named settings so they are easy to change in one place.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-r9z5$j1^%vo7r$lp(d%6o@=_+9tk=gx#_)zfc&0cv4clt6(3e4'
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
# SDD §4: six project apps; core imports nothing app-specific.

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # Local Farm Map apps
    'core',
    'accounts',
    'farms',
    'products',
    'listings',
    'discovery',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Server-rendered HTML: Jinja2 for project pages (SRS 7.1 — "Django's default
# template language shall not be assumed"); the Django backend is kept for
# the admin and auth views.

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'config.jinja2.environment',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database — SQLite + SpatiaLite prototype (C2); PostGIS upgrade path per
# database-design.md §10.

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Authentication — my call (database-design.md §4.3): phone-as-username with
# password auth; OTP is a V2 layer, not a V1 schema change.

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization — English-only copy in V1 (SDD §6), i18n enabled so a
# Kiswahili fast-follow is a translation task, not a retrofit.

LANGUAGE_CODE = 'en'

USE_I18N = True
USE_TZ = True

# Pilot locale — database-design.md §9: expiry is midnight in the pilot's
# local calendar; Africa/Nairobi is the working assumption pending the
# pilot-area decision.

TIME_ZONE = 'Africa/Nairobi'

# Static files (SDD §6): Tailwind compiled at build time into one stylesheet;
# no runtime CDN.

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---- Local Farm Map pilot settings (single place for the "my call" values) ----

# Search radius when the buyer shares GPS location; per-place overrides live
# in Place.search_radius_m (database-design.md §5.5).
DEFAULT_SEARCH_RADIUS_M = 15_000

# Initial map view before/without any results, so tiles always render.
# Kisii University area — the working pilot location.
DEFAULT_MAP_CENTER = (-0.6771, 34.1563)  # (lat, lng) — Kisii University
DEFAULT_MAP_ZOOM = 13

# Grid-snap precision for approximate pins: round each coordinate to 2 dp
# (~1.1 km cells) — database-design.md §4.1.
GRID_SNAP_DECIMALS = 2

# SpatiaLite has no geography type, so distance checks transform to a local
# UTM zone (database-design.md §10). Kenya straddles 36°E: 32736 west of it,
# 32737 east (e.g. Nairobi). Kisii (34.16°E) is west of the boundary.
PILOT_UTM_SRID = 32736

# Only listings this many days old may be tidied by the optional cleanup
# command — visibility always comes from the query filter (SRS 5.4).
LISTING_RETENTION_DAYS = 90
