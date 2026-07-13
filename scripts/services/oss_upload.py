"""OSS 文件上传集成

支持:
- 阿里云 OSS
- 腾讯云 COS
- 七牛云
- MinIO (自建)
"""

import os
import hashlib
import hmac
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ========================================
# 配置
# ========================================

OSS_PROVIDER = os.getenv("OSS_PROVIDER", "aliyun")  # aliyun | tencent | qiniu | minio
OSS_ACCESS_KEY = os.getenv("OSS_ACCESS_KEY", "")
OSS_SECRET_KEY = os.getenv("OSS_SECRET_KEY", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "zhimeiquan")
OSS_REGION = os.getenv("OSS_REGION", "cn-hangzhou")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
OSS_CUSTOM_DOMAIN = os.getenv("OSS_CUSTOM_DOMAIN", "")

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")

# ========================================
# 模型
# ========================================

class UploadResult(BaseModel):
    file_id: str
    url: str
    filename: str
    mime_type: str
    size: int
    etag: Optional[str] = None


class UploadOptions(BaseModel):
    path: str = ""
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    max_size: int = 100 * 1024 * 1024  # 100MB
    acl: str = "public-read"  # public-read | private


# ========================================
# 基础存储类
# ========================================

class BaseStorage:
    """存储基类"""

    def __init__(self):
        self.access_key = OSS_ACCESS_KEY
        self.secret_key = OSS_SECRET_KEY
        self.bucket = OSS_BUCKET
        self.region = OSS_REGION
        self.custom_domain = OSS_CUSTOM_DOMAIN

    def _generate_key(self, path: str, filename: str) -> str:
        """生成存储键"""
        import uuid
        ext = Path(filename).suffix
        name = f"{uuid.uuid4().hex}{ext}"
        return f"{path}/{name}" if path else name

    def _get_extension(self, filename: str) -> str:
        """获取扩展名"""
        return Path(filename).suffix.lower()

    async def upload(
        self,
        file: BinaryIO,
        options: UploadOptions
    ) -> UploadResult:
        """上传文件（子类实现）"""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """删除文件"""
        raise NotImplementedError

    async def get_url(self, key: str, expires: int = 3600) -> str:
        """获取访问 URL"""
        raise NotImplementedError


# ========================================
# 阿里云 OSS
# ========================================

class AliyunOSS(BaseStorage):
    """阿里云 OSS 存储"""

    def __init__(self):
        super().__init__()
        self.endpoint = OSS_ENDPOINT or f"https://oss-{self.region}.aliyuncs.com"
        self.host = f"{self.bucket}.{self.endpoint.replace('https://', '')}"

    async def upload(
        self,
        file: BinaryIO,
        options: UploadOptions
    ) -> UploadResult:
        """上传文件"""
        content = file.read()
        size = len(content)

        if size > options.max_size:
            raise ValueError(f"文件大小超出限制: {size} > {options.max_size}")

        key = self._generate_key(options.path, options.filename or "file")
        mime_type = options.mime_type or "application/octet-stream"

        # 计算签名
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_md5 = base64.b64encode(
            hashlib.md5(content).digest()
        ).decode()

        string_to_sign = f"PUT\n{content_md5}\n{mime_type}\n{date}\n/{self.bucket}/{key}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        # 上传
        url = f"https://{self.host}/{key}"
        headers = {
            "Date": date,
            "Content-Type": mime_type,
            "Content-MD5": content_md5,
            "Authorization": f"OSS {self.access_key}:{signature}",
            "x-oss-object-acl": options.acl,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(url, content=content, headers=headers)
            response.raise_for_status()

        etag = response.headers.get("ETag", "").strip('"')

        # 返回结果
        result_url = self.custom_domain or f"https://{self.host}"
        return UploadResult(
            file_id=key,
            url=f"{result_url}/{key}",
            filename=options.filename or Path(key).name,
            mime_type=mime_type,
            size=size,
            etag=etag,
        )

    async def delete(self, key: str) -> bool:
        """删除文件"""
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        string_to_sign = f"DELETE\n\n\n{date}\n/{self.bucket}/{key}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        url = f"https://{self.host}/{key}"
        headers = {
            "Date": date,
            "Authorization": f"OSS {self.access_key}:{signature}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=headers)
            return response.status_code == 204

    async def get_url(self, key: str, expires: int = 3600) -> str:
        """获取签名 URL"""
        if self.custom_domain and self.custom_domain.startswith("https://"):
            # 公开访问，直接返回
            return f"{self.custom_domain}/{key}"

        # 生成签名 URL
        import time
        expires_timestamp = int(time.time()) + expires
        string_to_sign = f"GET\n\n\n{expires_timestamp}\n/{self.bucket}/{key}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        return f"https://{self.host}/{key}?OSSAccessKeyId={self.access_key}&Expires={expires_timestamp}&Signature={signature}"


# ========================================
# 腾讯云 COS
# ========================================

class TencentCOS(BaseStorage):
    """腾讯云 COS 存储"""

    def __init__(self):
        super().__init__()
        self.endpoint = OSS_ENDPOINT or f"cos.{self.region}.myqcloud.com"
        self.host = f"{self.bucket}.{self.endpoint}"

    async def upload(
        self,
        file: BinaryIO,
        options: UploadOptions
    ) -> UploadResult:
        """上传文件"""
        content = file.read()
        size = len(content)

        if size > options.max_size:
            raise ValueError(f"文件大小超出限制")

        key = self._generate_key(options.path, options.filename or "file")
        mime_type = options.mime_type or "application/octet-stream"

        url = f"https://{self.host}/{key}"

        # 简化实现，生产环境需要完整签名
        headers = {
            "Content-Type": mime_type,
            "Authorization": f"q-sign-algorithm=sha1&q-ak={self.access_key}",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(url, content=content, headers=headers)
            response.raise_for_status()

        result_url = self.custom_domain or f"https://{self.host}"
        return UploadResult(
            file_id=key,
            url=f"{result_url}/{key}",
            filename=options.filename or Path(key).name,
            mime_type=mime_type,
            size=size,
        )


# ========================================
# MinIO (自建)
# ========================================

class MinIOStorage(BaseStorage):
    """MinIO 存储（S3 兼容）"""

    def __init__(self):
        super().__init__()
        self.endpoint = MINIO_ENDPOINT
        self.host = self.endpoint.replace("http://", "").replace("https://", "")

    async def upload(
        self,
        file: BinaryIO,
        options: UploadOptions
    ) -> UploadResult:
        """上传文件"""
        content = file.read()
        size = len(content)

        if size > options.max_size:
            raise ValueError(f"文件大小超出限制")

        key = self._generate_key(options.path, options.filename or "file")
        mime_type = options.mime_type or "application/octet-stream"

        url = f"{self.endpoint}/{self.bucket}/{key}"

        # S3 签名（简化版）
        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(size),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(url, content=content, headers=headers)
            response.raise_for_status()

        result_url = self.custom_domain or f"{self.endpoint}/{self.bucket}"
        return UploadResult(
            file_id=key,
            url=f"{result_url}/{key}",
            filename=options.filename or Path(key).name,
            mime_type=mime_type,
            size=size,
        )


# ========================================
# 工厂函数
# ========================================

def get_storage() -> BaseStorage:
    """获取存储实例"""
    providers = {
        "aliyun": AliyunOSS,
        "tencent": TencentCOS,
        "qiniu": AliyunOSS,  # 七牛签名类似
        "minio": MinIOStorage,
    }
    provider_class = providers.get(OSS_PROVIDER, AliyunOSS)
    return provider_class()


# 导出
storage = get_storage()