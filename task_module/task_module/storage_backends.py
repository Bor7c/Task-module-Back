# your_project/storage_backends.py
import os
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    """Custom storage backend for media files using MinIO."""
    
    bucket_name = 'media'
    # Убедитесь, что у вас правильный URL для доступа к бакету
    custom_domain = f"{os.getenv('MINIO_ENDPOINT', 'http://minio:9000')}/{bucket_name}"

    # Опционально: можно переопределить метод, если необходимо
    def get_object_parameters(self, name=None):
        params = super().get_object_parameters(name)
        # Если нужно, можно добавить дополнительные параметры
        return params
