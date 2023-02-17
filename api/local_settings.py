import json
import os
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path
CRYPTO_KEY='ipcoTyAUubVxWGeWByis_iTkDIpYMq438pmjseqE27U='
BASE_DIR = Path(__file__).resolve().parent.parent
API_MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
API_APP_LABEL = 'app'
DEFAULT_KEY = 'default'
API_APPS = [
    'django_extensions',
    "rest_framework",
    'drf_yasg',
    "corsheaders",
    "api",
    "api.logger"
]

CONNECTION_KEY_TESTS = {
    # 'APP': {
    #     'DB_KEY': 'app',
    #     'APPS': ['logger', 'webpush'],
    #     'MODELS': [],
    #     'TABLES': []
    # },
    'DEFAULT': {
        'DB_KEY': 'default',
        'APPS': [],
        'MODELS': [],
        'TABLES': []
    }
}

MODEL_FIELD_TYPES = {
    "spatial": ['GeometryField', 'PointField', 'LineStringField', 'PolygonField',
                'MultiPointField', 'MultiLineStringField', 'MultiPolygonField',
                'GeometryCollectionField', 'RasterField'],
    "number": ['AutoField', 'BigAutoField', 'BigIntegerField', 'DecimalField', 'DurationField', 'FloatField',
               'IntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 'SmallIntegerField'],
    "date": ['DateField', 'DateTimeField', 'TimeField'],
    "string": ['CharField', 'EmailField', 'FilePathField', 'TextField'],
    "others": ['BinaryField', 'BooleanField', 'FileField', 'FileField and FieldFile',
               'ImageField', 'GenericIPAddressField', 'NullBooleanField', 'SlugField', 'URLField', 'UUIDField'],
    "relational": ['ForeignKey']
}
