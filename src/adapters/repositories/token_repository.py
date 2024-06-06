from aioredis import Redis

from src.ports.repositories.token_repository import TokenRepository


class RedisTokenRepository(TokenRepository):
    async def get(self, token: str) -> str | None:
        return await self.redis_entity.get(token)

    async def blacklist(self, token: str) -> None:
        await self.redis_entity.set(token, 'blacklisted')

    def __init__(self, redis: Redis) -> None:
        self.redis_entity = redis
