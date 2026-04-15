import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Imports staff from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        path = options['csv_file']
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Based on description:
                # row[0] = BOA Level, row[1] = First Name, row[2] = Email, row[3] = Last Name
                level = row[0]
                first_name = row[1]
                email = row[2]
                last_name = row[3]
                
                # We'll use the name as the username to keep it simple
                username = first_name

                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        boa_level=level
                    )
                    # Set a random password they will change later
                    user.set_password(last_name) 
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'User {username} already exists.'))