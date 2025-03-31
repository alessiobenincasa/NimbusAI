# Gitlab configuration with complex password
external_url 'http://localhost'
gitlab_rails['initial_root_password'] = 'N1mbu$AI_2025@complex'
gitlab_rails['store_initial_root_password'] = true
gitlab_rails['display_initial_root_password'] = true 