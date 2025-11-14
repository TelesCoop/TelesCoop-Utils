INSTALLED_APPS = [
    "anymail",
]

if IS_LOCAL_DEV:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

else:
    ANYMAIL = {
        "MAILGUN_API_KEY": config.getstr("mail.api_key"),
        "MAILGUN_SENDER_DOMAIN": "mail.senderdomain.fr",
        "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",
    }
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    DEFAULT_FROM_EMAIL = "no-reply@telescoop.fr"
    SERVER_EMAIL = "no-reply@telescoop.fr"
    RECIPIENT_EMAIL = "Molly Maguire <molly.maguire@telescoop.fr>"