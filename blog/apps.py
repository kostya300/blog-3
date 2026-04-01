from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "blog"
    default_app_config = 'accounts.apps.AccountsConfig'