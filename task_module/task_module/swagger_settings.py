# task_module/swagger_settings.py
from drf_yasg import openapi

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'SessionID': {
            'type': 'apiKey',
            'name': 'X-Session-ID',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'OPERATIONS_SORTER': 'alpha',
    'SHOW_REQUEST_HEADERS': True,
    'VALIDATOR_URL': None,
}