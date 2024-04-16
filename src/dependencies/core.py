from typing import Annotated

from src.database.database import get_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DBSession = Annotated[AsyncSession, Depends(get_session)]
