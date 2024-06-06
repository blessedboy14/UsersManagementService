from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class Group:
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=UUID)
    