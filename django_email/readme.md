# Gérer l'envoi d'email depuis Django

> /!\ On n'utilise pas `requests.post` directement mais `django.core.email` afin de changer de provider facilement.

L'exemple donné ici utilise `Mailgun` et [`Anymail`](https://anymail.dev/en/stable/) pour son intégration.

Pour `Mailgun` il faut définir un `Sending`>`Domains` sur https://app.eu.mailgun.com (credentials dans le Bitwarden).

Pour la gestion des secrets (la clef API), on utilise la `ansible-vault`. Dans le deploy, il faut (1) modifier le template `ansible settings.ini.j2` et (2) ajouter la variable `vault_mailgun_api_key` dans `cross_env_vars.vault.yml` 
.L'ajout de variable se fait à l'aide de `ansible-vault edit group_vars/all/cross_env_vault.yml`, qui utilise par défaut `vim`. Si tu manques de goût et veut utiliser `nano`, rajouter `export EDITOR=nano`.