from dataclasses import dataclass, field, replace
from functools import cached_property

from nats.js.api import ConsumerConfig, StreamConfig

from coreutils.nats_utils.utils import durable_from_subject


@dataclass(frozen=True)
class Stream:
    service_prefix: str
    config: StreamConfig
    default_consumer_config: ConsumerConfig
    consumers_configs: dict[str, ConsumerConfig] = field(default_factory=dict)

    @cached_property
    def consumer_configs(self) -> list[ConsumerConfig]:
        consumers = []

        if self.config.subjects:
            for subject in self.config.subjects:
                consumers.append(
                    self.consumers_configs.get(
                        durable_from_subject(subject, self.service_prefix),
                        replace(
                            self.default_consumer_config,
                            durable_name=durable_from_subject(subject, self.service_prefix),
                            name=durable_from_subject(subject, self.service_prefix),
                        ),
                    )
                )

        return consumers

    @cached_property
    def name(self) -> str:
        if self.config.name is None:
            raise RuntimeError("Stream name is required")

        return self.config.name

    def __post_init__(self) -> None:
        if self.config.name is None:
            raise ValueError("Stream name is required")
