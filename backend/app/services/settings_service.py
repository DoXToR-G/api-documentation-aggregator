"""
Settings Service - Handles persistent storage of AI settings
Uses database for persistence and encryption for sensitive values
"""

import base64
import logging
from typing import Optional, Any
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.db.models import AISettings
from app.core.config import settings

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing persistent AI settings"""

    def __init__(self):
        # Use SECRET_KEY from config for encryption
        # In production, use a dedicated encryption key
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        self.cipher = Fernet(key)

    def _encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value"""
        try:
            encrypted = self.cipher.encrypt(value.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value"""
        try:
            decoded = base64.b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def save_setting(
        self,
        db: Session,
        key: str,
        value: Any,
        encrypt: bool = False,
        setting_type: str = 'string',
        description: Optional[str] = None
    ) -> bool:
        """
        Save a setting to database

        Args:
            db: Database session
            key: Setting key (e.g., 'openai_api_key')
            value: Setting value
            encrypt: Whether to encrypt the value
            setting_type: Type of setting (string, boolean, integer, json)
            description: Optional description

        Returns:
            True if saved successfully
        """
        try:
            # Convert value to string
            if setting_type == 'boolean':
                str_value = 'true' if value else 'false'
            elif setting_type == 'integer':
                str_value = str(value)
            elif setting_type == 'json':
                import json
                str_value = json.dumps(value)
            else:
                str_value = str(value) if value else None

            # Encrypt if needed
            if encrypt and str_value:
                str_value = self._encrypt_value(str_value)

            # Check if setting exists
            setting = db.query(AISettings).filter(AISettings.setting_key == key).first()

            if setting:
                # Update existing
                setting.setting_value = str_value
                setting.is_encrypted = encrypt
                setting.setting_type = setting_type
                if description:
                    setting.description = description
            else:
                # Create new
                setting = AISettings(
                    setting_key=key,
                    setting_value=str_value,
                    is_encrypted=encrypt,
                    setting_type=setting_type,
                    description=description
                )
                db.add(setting)

            db.commit()
            logger.info(f"Setting '{key}' saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save setting '{key}': {e}")
            db.rollback()
            return False

    def get_setting(
        self,
        db: Session,
        key: str,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get a setting from database

        Args:
            db: Database session
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        try:
            setting = db.query(AISettings).filter(AISettings.setting_key == key).first()

            if not setting or not setting.setting_value:
                return default

            # Decrypt if encrypted
            value = setting.setting_value
            if setting.is_encrypted:
                value = self._decrypt_value(value)

            # Convert to appropriate type
            if setting.setting_type == 'boolean':
                return value.lower() == 'true'
            elif setting.setting_type == 'integer':
                return int(value)
            elif setting.setting_type == 'json':
                import json
                return json.loads(value)
            else:
                return value

        except Exception as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return default

    def delete_setting(self, db: Session, key: str) -> bool:
        """Delete a setting from database"""
        try:
            setting = db.query(AISettings).filter(AISettings.setting_key == key).first()
            if setting:
                db.delete(setting)
                db.commit()
                logger.info(f"Setting '{key}' deleted successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete setting '{key}': {e}")
            db.rollback()
            return False

    def load_settings_to_config(self, db: Session):
        """Load all settings from database into config object"""
        try:
            # Load OpenAI API key
            api_key = self.get_setting(db, 'openai_api_key')
            if api_key:
                settings.openai_api_key = api_key
                logger.info("OpenAI API key loaded from database")

            # Load OpenAI model
            model = self.get_setting(db, 'openai_model')
            if model:
                settings.openai_model = model

            # Load web search setting
            enable_web_search = self.get_setting(db, 'enable_web_search')
            if enable_web_search is not None:
                settings.enable_web_search = enable_web_search

            # Load use_openai_agent setting
            use_openai_agent = self.get_setting(db, 'use_openai_agent')
            if use_openai_agent is not None:
                settings.use_openai_agent = use_openai_agent

            logger.info("Settings loaded from database successfully")

        except Exception as e:
            logger.error(f"Failed to load settings from database: {e}")


# Global instance
settings_service = SettingsService()
