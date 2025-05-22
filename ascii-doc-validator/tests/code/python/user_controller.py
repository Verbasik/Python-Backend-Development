from typing import Dict, Optional
from models import User

class UserController:
    """Контроллер для управления объектами User."""

    def __init__(self):
        self.db: Dict[int, User] = {}

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.get(user_id)

    def create_user(self, user_id: int, name: str) -> None:
        self.db[user_id] = User(user_id, name)