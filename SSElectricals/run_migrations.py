
import os
import sys
import django
from django.core.management import call_command

# Add the current directory to sys.path
sys.path.append(os.getcwd())

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSElectricals.settings')

# Initialize Django
django.setup()

def run_migrations():
    with open('migration_log.txt', 'a') as log:
        try:
            log.write(f"Migration started at {django.utils.timezone.now()}\n")
            print("Running makemigrations...")
            call_command('makemigrations', 'firstApp')
            log.write("makemigrations success\n")
            print("Running migrate...")
            call_command('migrate', 'firstApp')
            log.write("migrate success\n")
            print("All migrations completed successfully!")
            log.write("Migration finished successfully\n")
        except Exception as e:
            log.write(f"Migration Error: {e}\n")
            import traceback
            log.write(traceback.format_exc())
            print(f"Migration Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_migrations()
