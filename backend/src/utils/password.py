import bcrypt
from utils.logger import Logger

logger = Logger("password_utils")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False
