"""API 密钥加密工具"""
from cryptography.fernet import Fernet
import os
from app.core.logger import logger


class APIKeyEncryption:
    """API 密钥加密/解密"""
    
    def __init__(self):
        # 从环境变量读取加密密钥
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            logger.warning("ENCRYPTION_KEY not set, generating a new one")
            key = self.generate_key()
            logger.warning(f"Generated ENCRYPTION_KEY: {key}")
            logger.warning("Please save this key to your .env file!")
        
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid ENCRYPTION_KEY")
    
    def encrypt(self, api_key: str) -> str:
        """加密 API 密钥"""
        if not api_key:
            return None
        try:
            return self.cipher.encrypt(api_key.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise
    
    def decrypt(self, encrypted_key: str) -> str:
        """解密 API 密钥"""
        if not encrypted_key:
            return None
        try:
            return self.cipher.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise
    
    @staticmethod
    def generate_key() -> str:
        """生成新的加密密钥"""
        return Fernet.generate_key().decode()


# 全局加密实例
encryption = APIKeyEncryption()

