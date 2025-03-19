"""
WSGI config for personal_finance_tracker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os, sys
from dotenv import load_dotenv

load_dotenv()

project_path = os.environ.get("DJANGO_PROJECT_PATH")
venv_path = os.environ.get("VENV_PATH")

sys.path.append(project_path)
sys.path.append(venv_path)

# poiting to the project settings
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_finance_tracker.settings")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personal_finance_tracker.settings')

application = get_wsgi_application()
