import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_service.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
