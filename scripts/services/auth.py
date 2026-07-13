"""JWT 认证与权限控制"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, Depends, Request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# ─────────────────────────────────────────
# 模型
# ─────────────────────────────────────────

class User(BaseModel):
    """用户模型"""
    id: str
    email: EmailStr
    name: str
    role: str = "user"
    permissions: List[str] = []
    is_active: bool = True
    created_at: datetime


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # user_id
    email: str
    role: str
    permissions: List[str]
    exp: datetime


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


# ─────────────────────────────────────────
# 密码处理
# ─────────────────────────────────────────

def hash_password(password: str) -> str:
    """哈希密码"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ─────────────────────────────────────────
# JWT 处理
# ─────────────────────────────────────────

def create_token(user: User) -> str:
    """创建 JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "permissions": user.permissions,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


# ─────────────────────────────────────────
# 认证依赖
# ─────────────────────────────────────────

async def get_current_user(request: Request) -> User:
    """获取当前用户"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证")
    
    token = auth_header[7:]
    payload = decode_token(token)
    
    # TODO: 从数据库获取完整用户信息
    return User(
        id=payload.sub,
        email=payload.email,
        name="",
        role=payload.role,
        permissions=payload.permissions,
    )


async def get_current_user_optional(request: Request) -> Optional[User]:
    """可选认证（允许未认证用户）"""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


# ─────────────────────────────────────────
# 权限控制
# ─────────────────────────────────────────

# 权限定义
PERMISSIONS = {
    "content:read": "查看内容",
    "content:write": "创建/编辑内容",
    "content:delete": "删除内容",
    "media:read": "查看媒体",
    "media:write": "上传媒体",
    "media:delete": "删除媒体",
    "comment:read": "查看评论",
    "comment:write": "发表评论",
    "comment:moderate": "管理评论",
    "tag:read": "查看标签",
    "tag:write": "管理标签",
    "trend:read": "查看热点",
    "trend:scan": "扫描热点",
    "channel:read": "查看渠道",
    "channel:write": "管理渠道",
    "subscription:read": "查看订阅",
    "subscription:manage": "管理订阅",
    "user:read": "查看用户",
    "user:manage": "管理用户",
    "admin": "管理员权限",
}

# 角色权限映射
ROLE_PERMISSIONS = {
    "viewer": ["content:read", "media:read", "comment:read", "tag:read", "trend:read"],
    "editor": [
        "content:read", "content:write",
        "media:read", "media:write",
        "comment:read", "comment:write",
        "tag:read", "trend:read", "trend:scan",
    ],
    "manager": [
        "content:read", "content:write", "content:delete",
        "media:read", "media:write", "media:delete",
        "comment:read", "comment:write", "comment:moderate",
        "tag:read", "tag:write",
        "trend:read", "trend:scan",
        "channel:read", "channel:write",
    ],
    "admin": ["admin"],  # admin 拥有所有权限
}


def require_permissions(*required_permissions: str):
    """权限检查装饰器"""
    async def permission_checker(user: User = Depends(get_current_user)):
        # 管理员拥有所有权限
        if "admin" in user.permissions or user.role == "admin":
            return user
        
        # 检查权限
        user_permissions = set(user.permissions)
        if user.role in ROLE_PERMISSIONS:
            user_permissions.update(ROLE_PERMISSIONS[user.role])
        
        missing = [p for p in required_permissions if p not in user_permissions]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"缺少权限: {', '.join(missing)}"
            )
        
        return user
    
    return permission_checker


def require_role(*required_roles: str):
    """角色检查装饰器"""
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in required_roles and user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"需要角色: {', '.join(required_roles)}"
            )
        return user
    
    return role_checker


# ─────────────────────────────────────────
# 认证服务
# ─────────────────────────────────────────

class AuthService:
    """认证服务"""
    
    def __init__(self, db):
        self.db = db
    
    async def register(self, data: RegisterRequest) -> User:
        """用户注册"""
        # 检查邮箱是否已存在
        existing = await self.get_user_by_email(data.email)
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已注册")
        
        # 创建用户
        user_id = f"user_{datetime.utcnow().timestamp()}"
        hashed_password = hash_password(data.password)
        
        # TODO: 存储到数据库
        user = User(
            id=user_id,
            email=data.email,
            name=data.name,
            role="viewer",
            permissions=ROLE_PERMISSIONS["viewer"],
            created_at=datetime.utcnow(),
        )
        
        logger.info(f"用户注册: {data.email}")
        return user
    
    async def login(self, data: LoginRequest) -> TokenResponse:
        """用户登录"""
        user = await self.get_user_by_email(data.email)
        if not user:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        # TODO: 验证密码
        # if not verify_password(data.password, user.password_hash):
        #     raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        token = create_token(user)
        
        return TokenResponse(
            access_token=token,
            expires_in=JWT_EXPIRE_HOURS * 3600,
            user=user.dict(),
        )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        # TODO: 从数据库查询
        return None
    
    async def refresh_token(self, user: User) -> TokenResponse:
        """刷新 Token"""
        token = create_token(user)
        return TokenResponse(
            access_token=token,
            expires_in=JWT_EXPIRE_HOURS * 3600,
            user=user.dict(),
        )


# ─────────────────────────────────────────
# 导出
# ─────────────────────────────────────────

__all__ = [
    "User",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "hash_password",
    "verify_password",
    "create_token",
    "decode_token",
    "get_current_user",
    "get_current_user_optional",
    "require_permissions",
    "require_role",
    "AuthService",
    "PERMISSIONS",
    "ROLE_PERMISSIONS",
]