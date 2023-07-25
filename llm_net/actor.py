from typing import Any, AsyncIterable, Iterable, Optional

import ray

from llm_net.asyncio import AsyncGenAgent
from llm_net.base import GenAgent, GenNetwork, Message, llm_net


@ray.remote(max_restarts=3, max_task_retries=3, num_cpus=1)
class GenActor:
    node: GenAgent

    def __init__(self, node: GenAgent):
        self.node = node

    def receive(self, message: Message) -> Iterable[Message]:
        """For receiving messages"""
        return self.node.receive(message)

    def property(self, prop: str) -> Any:
        """For getting arbitrary properties on the node"""
        return getattr(self.node, prop)


class GenActorNetwork(GenNetwork):
    def receive(self, message: Message) -> Iterable[Message]:
        agent: Optional[GenActor] = message.receiver
        if agent is None:
            return
        if agent not in self:
            raise ValueError(f"Receiver {agent.id} not in GenNetwork")

        self.emit("receive", message)

        previous_network = llm_net.set(self)
        try:
            for response in agent.receive.remote(message):
                if (yield response) == StopIteration:
                    break
                yield from self.receive(response)
        finally:
            llm_net.reset(previous_network)


@ray.remote(max_restarts=3, max_task_retries=3, num_cpus=1)
class GenAsyncActor:
    node: AsyncGenAgent

    def __init__(self, node: AsyncGenAgent):
        self.node = node

    def property(self, prop: str) -> Any:
        return getattr(self.node, prop)

    async def areceive(self, message: Message):
        return await self.node.areceive(message)


class GenAsyncActorNetwork(GenNetwork):
    async def areceive(self, message: Message) -> AsyncIterable[Message]:
        agent: Optional[GenAsyncActor] = message.receiver
        if agent is None:
            return
        if agent not in self:
            raise ValueError(f"Receiver {agent.id} not in GenNetwork")

        self.emit("receive", message)

        previous_network = llm_net.set(self)
        try:
            async for response in agent.areceive.remote(message):
                if (yield response) == StopIteration:
                    break
                async for response in self.areceive(response):
                    yield response
        finally:
            llm_net.reset(previous_network)
