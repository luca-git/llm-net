# Generated by CodiumAI
import pytest
import ray

from llegos.actors import ActorAgent, actor_namespace, actor_propogate_all
from llegos.test_helpers import Inform, MockAsyncAgent


class MockActorAgent(ActorAgent, MockAsyncAgent):
    ...


class TestActorAgent:
    @classmethod
    def setup_class(cls):
        ray.init()

    @classmethod
    def teardown_class(cls):
        ray.shutdown()

    def test_reusable_actors(self):
        agent = MockActorAgent()
        ns = actor_namespace.get()
        id = str(agent.id)
        with agent.get_actor() as actor:
            got_actor = ray.get_actor(namespace=ns, name=id)
            assert actor._ray_actor_id == got_actor._ray_actor_id

    @pytest.mark.asyncio
    async def test_handling_messages(self):
        # Create an instance of ActorAgent
        agent = MockActorAgent()
        m1 = Inform(body="Message 1", receiver=agent)
        m2 = Inform(body="Message 2", receiver=agent)

        messages = [m1, m2]
        replies = []

        async for reply in actor_propogate_all(messages):
            replies.append(reply)

        assert len(messages) == len(replies)

        for message, reply in zip(messages, replies):
            assert reply.body == f"Ack: {message.id}"