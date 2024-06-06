from dataclasses import dataclass, field


@dataclass
class Token:
    access_token: str
    refresh_token: str
    type: str
