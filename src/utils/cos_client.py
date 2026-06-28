"""
IBM Cloud Object Storage (COS) Utility - Free tier compatible
Handles image upload, download, presigned URLs, and bucket management
"""
import os
import uuid
import base64
from datetime import datetime, timedelta
from typing import Optional, Tuple, BinaryIO
from dataclasses import dataclass
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError
    COS_AVAILABLE = True
except ImportError:
    COS_AVAILABLE = False


@dataclass
class UploadResult:
    success: bool
    object_key: str
    public_url: Optional[str] = None
    presigned_url: Optional[str] = None
    error: Optional[str] = None
    size_bytes: int = 0


@dataclass
class COSConfig:
    api_key_id: str
    service_instance_id: str
    endpoint: str
    bucket_name: str
    region: str = "us-south"


class COSClient:
    """IBM Cloud Object Storage client for waste image storage"""
    
    # Free tier limits
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
    BUCKET_PREFIX = "ecosort-"
    
    def __init__(self, config: COSConfig):
        self.config = config
        self.client = None
        self.bucket_created = False
        self._init_client()
    
    def _init_client(self):
        """Initialize boto3 client for IBM COS"""
        if not COS_AVAILABLE:
            print("[WARN] ibm-cos-sdk/boto3 not installed. COS features disabled.")
            return
        
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.config.endpoint,
                aws_access_key_id=self.config.api_key_id,
                aws_secret_access_key=self.config.service_instance_id,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                ),
                region_name=self.config.region
            )
            print("[OK] COS client initialized")
        except Exception as e:
            print(f"[WARN] COS client init failed: {e}")
            self.client = None
    
    def ensure_bucket(self) -> bool:
        """Create bucket if it doesn't exist (idempotent)"""
        if not self.client:
            return False
        
        if self.bucket_created:
            return True
        
        try:
            self.client.head_bucket(Bucket=self.config.bucket_name)
            print(f"[OK] Bucket '{self.config.bucket_name}' exists")
            self.bucket_created = True
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.client.create_bucket(Bucket=self.config.bucket_name)
                    print(f"[OK] Created bucket '{self.config.bucket_name}'")
                    self.bucket_created = True
                    return True
                except ClientError as ce:
                    print(f"[ERROR] Failed to create bucket: {ce}")
                    return False
            else:
                print(f"[ERROR] Bucket check failed: {e}")
                return False
    
    def _validate_file(self, file_path: str, file_bytes: bytes = None) -> Tuple[bool, str]:
        """Validate file type and size"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid format: {ext}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        size_mb = len(file_bytes) / (1024 * 1024) if file_bytes else path.stat().st_size / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            return False, f"File too large: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB limit"
        
        return True, ""
    
    def upload_image(
        self, 
        file_path: str, 
        object_key: Optional[str] = None,
        make_public: bool = False
    ) -> UploadResult:
        """
        Upload waste image to COS
        
        Args:
            file_path: Local path to image file
            object_key: Custom object key (auto-generated if None)
            make_public: Generate public URL (requires bucket public access)
        
        Returns:
            UploadResult with URLs and metadata
        """
        if not self.client:
            return UploadResult(False, "", error="COS client not initialized")
        
        if not self.ensure_bucket():
            return UploadResult(False, "", error="Bucket not available")
        
        # Validate file
        valid, err = self._validate_file(file_path)
        if not valid:
            return UploadResult(False, "", error=err)
        
        # Generate object key if not provided
        if not object_key:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = Path(file_path).suffix.lower()
            object_key = f"waste-images/{timestamp}_{unique_id}{ext}"
        
        try:
            # Upload file
            with open(file_path, 'rb') as f:
                self.client.upload_fileobj(
                    f, 
                    self.config.bucket_name, 
                    object_key,
                    ExtraArgs={
                        'ContentType': self._get_content_type(Path(file_path).suffix),
                        'Metadata': {
                            'uploaded-by': 'ecosort-ai',
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    }
                )
            
            # Get file size
            size_bytes = Path(file_path).stat().st_size
            
            # Generate presigned URL (valid for 7 days - free tier friendly)
            presigned_url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': object_key},
                ExpiresIn=604800  # 7 days
            )
            
            # Public URL (if bucket allows)
            public_url = None
            if make_public:
                public_url = f"{self.config.endpoint}/{self.config.bucket_name}/{object_key}"
            
            print(f"[OK] Uploaded: {object_key} ({size_bytes/1024:.1f} KB)")
            
            return UploadResult(
                success=True,
                object_key=object_key,
                public_url=public_url,
                presigned_url=presigned_url,
                size_bytes=size_bytes
            )
            
        except ClientError as e:
            error_msg = f"Upload failed: {e.response['Error']['Message']}"
            print(f"[ERROR] {error_msg}")
            return UploadResult(False, object_key, error=error_msg)
    
    def upload_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        object_key: Optional[str] = None
    ) -> UploadResult:
        """Upload image from bytes (e.g., from web upload)"""
        if not self.client:
            return UploadResult(False, "", error="COS client not initialized")
        
        if not self.ensure_bucket():
            return UploadResult(False, "", error="Bucket not available")
        
        # Validate
        valid, err = self._validate_file(filename, image_bytes)
        if not valid:
            return UploadResult(False, "", error=err)
        
        if not object_key:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = Path(filename).suffix.lower()
            object_key = f"waste-images/{timestamp}_{unique_id}{ext}"
        
        try:
            self.client.put_object(
                Bucket=self.config.bucket_name,
                Key=object_key,
                Body=image_bytes,
                ContentType=self._get_content_type(Path(filename).suffix),
                Metadata={
                    'uploaded-by': 'ecosort-ai',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            presigned_url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': object_key},
                ExpiresIn=604800
            )
            
            print(f"[OK] Uploaded bytes: {object_key} ({len(image_bytes)/1024:.1f} KB)")
            
            return UploadResult(
                success=True,
                object_key=object_key,
                presigned_url=presigned_url,
                size_bytes=len(image_bytes)
            )
            
        except ClientError as e:
            return UploadResult(False, object_key, error=f"Upload failed: {e}")
    
    def download_image(self, object_key: str, save_path: str) -> bool:
        """Download image from COS to local path"""
        if not self.client:
            return False
        
        try:
            self.client.download_file(self.config.bucket_name, object_key, save_path)
            print(f"[OK] Downloaded: {object_key} -> {save_path}")
            return True
        except ClientError as e:
            print(f"[ERROR] Download failed: {e}")
            return False
    
    def get_presigned_url(self, object_key: str, expires_hours: int = 168) -> Optional[str]:
        """Get presigned URL for temporary access (max 7 days)"""
        if not self.client:
            return None
        
        try:
            return self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': object_key},
                ExpiresIn=expires_hours * 3600
            )
        except ClientError:
            return None
    
    def delete_image(self, object_key: str) -> bool:
        """Delete image from COS"""
        if not self.client:
            return False
        
        try:
            self.client.delete_object(Bucket=self.config.bucket_name, Key=object_key)
            print(f"[OK] Deleted: {object_key}")
            return True
        except ClientError as e:
            print(f"[ERROR] Delete failed: {e}")
            return False
    
    def list_images(self, prefix: str = "waste-images/") -> list:
        """List uploaded waste images"""
        if not self.client:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.config.bucket_name,
                Prefix=prefix
            )
            return [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                }
                for obj in response.get('Contents', [])
            ]
        except ClientError:
            return []
    
    def _get_content_type(self, ext: str) -> str:
        types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.heic': 'image/heic'
        }
        return types.get(ext.lower(), 'application/octet-stream')


def create_cos_client_from_env() -> Optional[COSClient]:
    """Factory function to create COS client from environment variables"""
    api_key = os.getenv("COS_API_KEY_ID")
    instance_id = os.getenv("COS_SERVICE_INSTANCE_ID")
    endpoint = os.getenv("COS_ENDPOINT", "https://s3.us-south.cloud-object-storage.appdomain.cloud")
    bucket = os.getenv("COS_BUCKET_NAME", "ecosort-waste-images")
    
    if not api_key or not instance_id:
        print("[WARN] COS credentials not found in environment")
        return None
    
    config = COSConfig(
        api_key_id=api_key,
        service_instance_id=instance_id,
        endpoint=endpoint,
        bucket_name=bucket
    )
    return COSClient(config)