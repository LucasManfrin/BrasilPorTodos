from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_session
from app.modules.auth.dependencies import current_user
from app.modules.users.models import User

DB = Annotated[Session, Depends(get_session)]
Config = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(current_user)]
