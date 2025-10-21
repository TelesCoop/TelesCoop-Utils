# TelesCoop Utils

Utilitaires à réutiliser dans nos projets ou utiles indépendamment.

- `api.ts`. Utilitaire pour avoir des requêtes faciles à utiliser, et qui gère les états de chargements, des alertes en cas de succès/échecs et un message général de chargement. A utiliser avec `loadingStore.ts` et `alertStore.ts`.
- `base64FileUpload.vue` : composant Vue ou morceaux de code à utiliser dans une page / composant Vue pour faire un upload de fichier en base64. Conçu pour fonctionner avec un back qui utiliser `base64FileField.py`
- `pay-slip-splitter/` : script Python qui découpe un PDF contenant toutes les fiches de paie du mois en fichiers PDF individuels pour chaque employé. Télécharge automatiquement la liste des employés depuis GitHub et nomme les fichiers au format `[YYYY-MM] [Nom Prénom].pdf`. Voir le [README dédié](pay-slip-splitter/README.md) pour plus de détails.
- `script_to_copy_google_files.py` : script Python pour cloner récursivement un dossier Google Drive (avec tous ses sous-dossiers et fichiers) vers un autre emplacement. Supporte les drives partagés et nécessite l'authentification OAuth Google.
- `.bashrc` : un bon bashrc qui permet notamment :
  - l'affiche de la branche courante et de l'env virtuel Python dans la ligne dans le bash, ex `[demometre] maxime@maxime-P14s:~/repos/demometre/demometre-backend (documents)*`
  - un historique sans limite qui affiche l'heure des commandes (pratique pour retrouver ce que l'on a fait)
- `django_disable_migrations_for_tests.py`: usually for tests, Django creates a test table by going through all migrations. Creating the test database is much faster if migrations are ignored, in this case the test DB is created by looking at the current state of `models.py`. A `TestRunner` is added so that objects can be created before tests, as this can be necessary for some projets (for example here, creating a `Locale` for a `wagtail` project).
- `frontend_rich_text_field.py` : champ texte à utiliser dans un modèle pour que son contenu soit automatiquement validé par Bleach pour éviter les attaque XSS
- `.gitignore` : un `.gitignore` classique, avec des morceaux dédiés au back et au front
- `.inputrc` : permet que dans le bas, quand on appuie une ou plusieurs fois vers flèche du haut / flèche du bas, on navigue dans les dernières entrées qui correspondent, par exemple `python man` + flèche du haut complète en `python manage.py runserver`
- `jupyter_custom_custom.js` : cf `Notebook like a boss - Python hacks.ipynb`
- `loadingStore.ts` : store Pinia à utiliser dans un projet Vue3 qui permet d'indiquer l'état de chargement des requêtes et un éventuel message général de chargement. À utiliser avec `api.ts`.
- `Notebook like a boss - Python hacks.ipynb` : un fichier Jupyter Notebook qui propose des astuces pour être plus efficaces
