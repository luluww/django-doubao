SECRET_KEY = "test-secret-key-for-django-doubao"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "doubao",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
DOUBAO_API_KEY = "test-api-key-do-not-use-in-production"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    },
]
MIDDLEWARE = []
ROOT_URLCONF = "tests.test_urls"
