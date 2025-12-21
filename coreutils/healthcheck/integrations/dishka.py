from dishka import Provider, Scope, provide
from faststream.nats import NatsBroker
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from coreutils.healthcheck.healthchecks.nats import NatsHealthCheck
from coreutils.healthcheck.healthchecks.postgres import PostgresHealthCheck
from coreutils.healthcheck.healthchecks.redis import RedisHealthCheck
from coreutils.healthcheck.readiness_runner import ReadinessRunner


class MonitoringProvider(Provider):
    scope = Scope.APP

    @provide()
    def nats_health_check(self, broker: NatsBroker) -> NatsHealthCheck:
        return NatsHealthCheck(broker=broker)

    @provide()
    def postgres_health_check(self, engine: AsyncEngine) -> PostgresHealthCheck:
        return PostgresHealthCheck(engine=engine)

    @provide()
    def redis_health_check(self, redis: Redis) -> RedisHealthCheck:
        return RedisHealthCheck(redis=redis)

    @provide()
    def runner(
        self,
        nats_health_check: NatsHealthCheck,
        postgres_health_check: PostgresHealthCheck,
        redis_health_check: RedisHealthCheck,
    ) -> ReadinessRunner:
        return ReadinessRunner(
            checks=[nats_health_check, postgres_health_check, redis_health_check],
        )
