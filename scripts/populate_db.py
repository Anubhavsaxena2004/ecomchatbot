import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_chatbot.settings')
django.setup()

from django.core.management import call_command

def main():
    print("Starting database population...")
    call_command('populate_db')
    print("Database population completed successfully!")

if __name__ == '__main__':
    main() 