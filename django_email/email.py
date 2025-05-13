from django.conf import settings
from django.core.mail import send_mail
send_mail(
            "Sujet de l'email",
            f"Corps de l'email"
            settings.DEFAULT_FROM_EMAIL,
            [settings.RECIPIENT_EMAIL],
        )