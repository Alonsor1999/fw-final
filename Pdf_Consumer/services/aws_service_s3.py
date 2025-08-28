import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

log = logging.getLogger(__name__)

class AWSServiceS3:
    def __init__(self, aws_region: str, s3_bucket: str):
        self.s3_client = boto3.client("s3", region_name=aws_region)
        self.s3_bucket = s3_bucket

    def upload_to_s3(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            log.info("Archivo subido a s3://%s/%s", self.s3_bucket, key)
        except (BotoCoreError, ClientError) as e:
            log.error("Error al subir archivo a S3: %s", e)
            raise
