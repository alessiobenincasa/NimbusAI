# Configuration GitLab simplifiée
external_url 'http://localhost'

# Configuration du mot de passe root - simple mais sécurisé
gitlab_rails['initial_root_password'] = 'Admin123!'
gitlab_rails['store_initial_root_password'] = true
gitlab_rails['display_initial_root_password'] = true

# Réduire la mémoire pour les environnements de dev
unicorn['worker_processes'] = 2
unicorn['worker_timeout'] = 60
sidekiq['concurrency'] = 5
postgresql['shared_buffers'] = "256MB"

# Désactiver les services non essentiels pour une démo
pages_external_url "http://localhost:8090"
gitlab_pages['enable'] = false
registry_external_url "http://localhost:5000"
registry['enable'] = false
prometheus['enable'] = false 