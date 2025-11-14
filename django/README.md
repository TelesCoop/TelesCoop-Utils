# Projets Django

## ÉLéments utiles pour vos projets Django

* Ajout de la backup avec [TelesCoop-Backup](https://github.com/TelesCoop/telescoop-backup/)
* Ajout du `health-check` :
    * Mettre le fichier `health-check/health_check.py` dans votre dossier `views`
    * Fichier `urls.py`:
    ```py
    from xx.views.health_check import health_check
    ...
    path("api/health-check", health_check, name="health-check")
    ```