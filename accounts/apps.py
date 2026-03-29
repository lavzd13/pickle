from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth.models import User
        from django.db.models.signals import pre_delete
        from django.dispatch import receiver

        @receiver(pre_delete, sender=User)
        def prevent_superuser_delete(sender, instance, **kwargs):
            if instance.is_superuser:
                raise PermissionError(f'Cannot delete superuser "{instance.username}". Remove superuser status first.')
