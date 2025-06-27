import boto3
import os
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_pdf_to_s3(file_data: bytes, filename: str) -> str:
    s3_key = f"pahani-pdfs/{uuid4()}_{filename}"
    
    s3_client.put_object(
        Bucket=AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_data,
        ContentType="application/pdf",
    )

    return f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
