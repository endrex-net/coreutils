import logging
from dataclasses import replace

from faststream.nats import NatsBroker
from nats.js.api import ConsumerConfig
from nats.js.errors import NotFoundError

from coreutils.nats_utils.stream import Stream


log = logging.getLogger("faststream")


class NatsStreamManager:
    def __init__(self, broker: NatsBroker):
        self.__broker = broker
        self.__stream = broker.stream

    async def initialize_stream(self, stream: Stream) -> None:
        try:
            await self._create_or_update_stream(stream)
        except Exception:
            log.exception("Failed to initialize NATS JetStream streams.")
            raise

        try:
            for consumer_config in stream.consumer_configs:
                await self._create_or_update_consumer(stream.name, consumer_config)
            log.info("NATS JetStream consumers initialized successfully")
        except Exception:
            log.exception("Failed to initialize NATS JetStream consumers.")
            raise

    async def _create_or_update_stream(self, stream: Stream) -> None:
        if self.__stream is None:
            raise RuntimeError("NATS JetStream is not initialized")

        try:
            stream_info = await self.__stream.stream_info(stream.name)
            log.info(
                "Stream %s already exists with config %s, updating...",
                stream.name,
                stream_info.config,
            )

            new_subjects = stream.config.subjects or []
            new_subjects.extend(stream_info.config.subjects or [])
            stream_config = replace(stream_info.config, subjects=new_subjects)

            await self.__stream.update_stream(stream_config)
            log.info("Stream %s updated successfully", stream.name)
        except NotFoundError:
            log.info("Creating new stream %s...", stream.name)
            await self.__stream.add_stream(stream.config)
            log.info("Stream %s created successfully", stream.name)
        except Exception as exc:
            log.error("Failed to create/update stream %s: %s", stream.name, exc)
            raise

    async def _create_or_update_consumer(
        self,
        stream_name: str,
        consumer_config: ConsumerConfig,
    ) -> None:
        if self.__stream is None:
            raise RuntimeError("NATS JetStream is not initialized")

        if consumer_config.name is None:
            raise ValueError("Consumer name is required")

        try:
            await self.__stream.consumer_info(stream_name, consumer_config.name)
            log.info(
                "Consumer %s already exists in stream %s",
                consumer_config.name,
                stream_name,
            )

        except NotFoundError:
            log.info(
                "Creating consumer %s for stream %s...",
                consumer_config.name,
                stream_name,
            )

            await self.__stream.add_consumer(stream_name, consumer_config)
            log.info(
                "Consumer %s created successfully for stream %s",
                consumer_config.name,
                stream_name,
            )

        except Exception as exc:
            log.error(
                "Failed to create consumer %s for stream %s: %s",
                consumer_config.name,
                stream_name,
                exc,
            )
            raise
