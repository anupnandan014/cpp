from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Creates default admin and worker accounts if they don't exist"

    def handle(self, *args, **options):
        if not User.objects.filter(username='anup').exists():
            User.objects.create_superuser(username='anup', email='anupnandan014@gmail.com', password='ChangeThisPassword123!')
            self.stdout.write(self.style.SUCCESS('Created admin user: anup'))
        else:
            self.stdout.write('Admin user anup already exists')

        if not User.objects.filter(username='worker1').exists():
            User.objects.create_user(username='worker1', password='workerpass123')
            self.stdout.write(self.style.SUCCESS('Created worker user: worker1'))
        else:
            self.stdout.write('Worker user worker1 already exists')
