"""
Async concurrency tests.

Tests for concurrent execution patterns and edge cases:
- Concurrent request handling
- Race conditions
- Resource sharing
- Performance under concurrent load
- asyncio.gather patterns
- Task cancellation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import time

from utils.RequestAPIJokes import (
    AsyncJokeAPIClient,
    aget_joke,
    aget_ten_jokes,
    aget_joke_by_id,
    aget_jokes_by_type,
    _aclient,
)
from main import tool_aget_joke, tool_aget_joke_by_id, tool_aget_joke_by_type
from utils.model import Joke, Jokes
from utils.exceptions import JokeAPITimeoutError, JokeAPIConnectionError


# Access the underlying functions from the decorated tools
_tool_aget_joke_func = tool_aget_joke.fn if hasattr(tool_aget_joke, 'fn') else tool_aget_joke
_tool_aget_joke_by_id_func = tool_aget_joke_by_id.fn if hasattr(tool_aget_joke_by_id, 'fn') else tool_aget_joke_by_id
_tool_aget_joke_by_type_func = tool_aget_joke_by_type.fn if hasattr(tool_aget_joke_by_type, 'fn') else tool_aget_joke_by_type


@pytest.fixture
def create_joke():
    """Factory for creating jokes."""
    def _create(joke_id, joke_type="general"):
        return Joke(
            id=joke_id,
            type=joke_type,
            setup=f"Setup for joke {joke_id}",
            punchline=f"Punchline for joke {joke_id}"
        )
    return _create


class TestConcurrentRequestHandling:
    """Tests for handling concurrent requests."""

    @pytest.mark.asyncio
    async def test_many_concurrent_get_joke_requests(self, create_joke):
        """Test handling many concurrent aget_joke requests."""
        num_concurrent = 100

        jokes = [create_joke(i) for i in range(num_concurrent)]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = jokes

            results = await asyncio.gather(*[aget_joke() for _ in range(num_concurrent)])

            assert len(results) == num_concurrent
            assert all(isinstance(r, Joke) for r in results)
            assert mock_get.call_count == num_concurrent

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_functions(self, create_joke):
        """Test concurrent requests to different async functions."""
        joke = create_joke(1)
        jokes = Jokes(jokes=[create_joke(i) for i in range(1, 11)])

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get_joke, \
             patch.object(_aclient, 'get_ten_jokes', new_callable=AsyncMock) as mock_get_ten, \
             patch.object(_aclient, 'get_joke_by_id', new_callable=AsyncMock) as mock_get_by_id, \
             patch.object(_aclient, 'get_jokes_by_type', new_callable=AsyncMock) as mock_get_by_type:

            mock_get_joke.return_value = joke
            mock_get_ten.return_value = jokes
            mock_get_by_id.return_value = joke
            mock_get_by_type.return_value = jokes

            # Create 100 concurrent tasks mixing different functions
            tasks = []
            for i in range(100):
                if i % 4 == 0:
                    tasks.append(aget_joke())
                elif i % 4 == 1:
                    tasks.append(aget_ten_jokes())
                elif i % 4 == 2:
                    tasks.append(aget_joke_by_id(i))
                else:
                    tasks.append(aget_jokes_by_type("general"))

            results = await asyncio.gather(*tasks)

            assert len(results) == 100
            # Verify all functions were called
            assert mock_get_joke.call_count == 25
            assert mock_get_ten.call_count == 25
            assert mock_get_by_id.call_count == 25
            assert mock_get_by_type.call_count == 25

    @pytest.mark.asyncio
    async def test_concurrent_tool_invocations(self, create_joke):
        """Test concurrent invocations of async MCP tools."""
        joke = create_joke(1)
        jokes = Jokes(jokes=[create_joke(i) for i in range(1, 11)])

        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget, \
             patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id, \
             patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:

            mock_aget.return_value = joke
            mock_aget_by_id.return_value = joke
            mock_aget_by_type.return_value = jokes

            # 50 concurrent tool invocations
            tasks = []
            for i in range(50):
                if i % 3 == 0:
                    tasks.append(_tool_aget_joke_func())
                elif i % 3 == 1:
                    tasks.append(_tool_aget_joke_by_id_func(i))
                else:
                    tasks.append(_tool_aget_joke_by_type_func("general"))

            results = await asyncio.gather(*tasks)

            assert len(results) == 50
            assert all(isinstance(r, str) for r in results)


class TestConcurrentErrorHandling:
    """Tests for error handling in concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_mixed_errors(self, create_joke):
        """Test handling mixed errors in concurrent requests."""
        # Create a sequence of responses: some succeed, some fail
        responses = []
        for i in range(20):
            if i % 4 == 0:
                responses.append(JokeAPITimeoutError())
            elif i % 4 == 1:
                responses.append(JokeAPIConnectionError())
            else:
                responses.append(create_joke(i))

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = responses

            results = await asyncio.gather(
                *[aget_joke() for _ in range(20)],
                return_exceptions=True
            )

            assert len(results) == 20
            timeout_errors = sum(1 for r in results if isinstance(r, JokeAPITimeoutError))
            connection_errors = sum(1 for r in results if isinstance(r, JokeAPIConnectionError))
            successes = sum(1 for r in results if isinstance(r, Joke))

            assert timeout_errors == 5  # Every 4th starting from 0
            assert connection_errors == 5  # Every 4th starting from 1
            assert successes == 10  # The rest

    @pytest.mark.asyncio
    async def test_concurrent_requests_all_fail(self):
        """Test handling when all concurrent requests fail."""
        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = JokeAPITimeoutError()

            results = await asyncio.gather(
                *[aget_joke() for _ in range(10)],
                return_exceptions=True
            )

            assert all(isinstance(r, JokeAPITimeoutError) for r in results)
            assert len(results) == 10

    @pytest.mark.asyncio
    async def test_concurrent_requests_fail_fast(self):
        """Test fail-fast behavior without return_exceptions."""
        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = JokeAPIConnectionError()

            # Without return_exceptions, should raise on first error
            with pytest.raises(JokeAPIConnectionError):
                await asyncio.gather(*[aget_joke() for _ in range(10)])


class TestConcurrentPerformance:
    """Tests for performance characteristics under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_execution_is_parallel(self, create_joke):
        """Test that concurrent requests execute in parallel."""
        # Simulate slow async operation
        async def slow_get_joke():
            await asyncio.sleep(0.1)  # 100ms delay
            return create_joke(1)

        with patch.object(_aclient, 'get_joke', side_effect=slow_get_joke):
            start_time = time.time()

            # 10 concurrent requests, each taking 100ms
            await asyncio.gather(*[aget_joke() for _ in range(10)])

            elapsed = time.time() - start_time

            # Should take ~100ms (parallel), not ~1000ms (sequential)
            # Allow some overhead, but should be < 300ms
            assert elapsed < 0.3, f"Took {elapsed}s, expected < 0.3s for parallel execution"

    @pytest.mark.asyncio
    async def test_sequential_execution_is_slower(self, create_joke):
        """Test that sequential execution is slower than concurrent."""
        async def slow_get_joke():
            await asyncio.sleep(0.05)  # 50ms delay
            return create_joke(1)

        with patch.object(_aclient, 'get_joke', side_effect=slow_get_joke):
            # Concurrent execution
            start_concurrent = time.time()
            await asyncio.gather(*[aget_joke() for _ in range(10)])
            concurrent_time = time.time() - start_concurrent

            # Sequential execution
            start_sequential = time.time()
            for _ in range(10):
                await aget_joke()
            sequential_time = time.time() - start_sequential

            # Sequential should be at least 3x slower
            assert sequential_time > concurrent_time * 3

    @pytest.mark.asyncio
    async def test_high_concurrency_load(self, create_joke):
        """Test system under high concurrent load."""
        num_requests = 500

        jokes = [create_joke(i) for i in range(num_requests)]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = jokes

            start_time = time.time()
            results = await asyncio.gather(*[aget_joke() for _ in range(num_requests)])
            elapsed = time.time() - start_time

            assert len(results) == num_requests
            assert all(isinstance(r, Joke) for r in results)
            # Should complete in reasonable time (< 2 seconds for 500 requests)
            assert elapsed < 2.0


class TestAsyncioGatherPatterns:
    """Tests for various asyncio.gather patterns."""

    @pytest.mark.asyncio
    async def test_gather_with_return_exceptions_true(self, create_joke):
        """Test gather with return_exceptions=True."""
        responses = [
            create_joke(1),
            JokeAPITimeoutError(),
            create_joke(2),
            JokeAPIConnectionError(),
        ]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = responses

            results = await asyncio.gather(
                aget_joke(),
                aget_joke(),
                aget_joke(),
                aget_joke(),
                return_exceptions=True
            )

            assert len(results) == 4
            assert isinstance(results[0], Joke)
            assert isinstance(results[1], JokeAPITimeoutError)
            assert isinstance(results[2], Joke)
            assert isinstance(results[3], JokeAPIConnectionError)

    @pytest.mark.asyncio
    async def test_gather_with_return_exceptions_false(self, create_joke):
        """Test gather with return_exceptions=False (default)."""
        responses = [
            create_joke(1),
            JokeAPITimeoutError(),
        ]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = responses

            # Should raise the first exception
            with pytest.raises(JokeAPITimeoutError):
                await asyncio.gather(
                    aget_joke(),
                    aget_joke(),
                )

    @pytest.mark.asyncio
    async def test_gather_empty_list(self):
        """Test gather with empty task list."""
        results = await asyncio.gather()
        assert results == []

    @pytest.mark.asyncio
    async def test_gather_single_task(self, create_joke):
        """Test gather with single task."""
        joke = create_joke(1)

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = joke

            results = await asyncio.gather(aget_joke())

            assert len(results) == 1
            assert isinstance(results[0], Joke)


class TestTaskCancellation:
    """Tests for task cancellation in concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_task_cancellation_during_execution(self, create_joke):
        """Test cancelling tasks during execution."""
        async def long_running_get_joke():
            await asyncio.sleep(1.0)  # Long delay
            return create_joke(1)

        with patch.object(_aclient, 'get_joke', side_effect=long_running_get_joke):
            task = asyncio.create_task(aget_joke())

            # Let it start
            await asyncio.sleep(0.1)

            # Cancel it
            task.cancel()

            # Verify it was cancelled
            with pytest.raises(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio
    async def test_some_tasks_cancelled_others_continue(self, create_joke):
        """Test that cancelling some tasks doesn't affect others."""
        call_count = [0]

        async def mock_get_joke():
            call_count[0] += 1
            if call_count[0] == 1:  # First call (slow task)
                await asyncio.sleep(0.5)
                return create_joke(1)
            else:  # Second call (fast task)
                await asyncio.sleep(0.05)
                return create_joke(2)

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock, side_effect=mock_get_joke):
            slow_task = asyncio.create_task(aget_joke())
            fast_task = asyncio.create_task(aget_joke())

            # Cancel slow task
            await asyncio.sleep(0.1)
            slow_task.cancel()

            # Fast task should complete
            result = await fast_task
            assert isinstance(result, Joke)

            # Slow task should be cancelled
            with pytest.raises(asyncio.CancelledError):
                await slow_task


class TestResourceSharing:
    """Tests for resource sharing in concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_singleton_client_shared_across_requests(self, create_joke):
        """Test that singleton client is shared across concurrent requests."""
        from utils.RequestAPIJokes import _aclient as client1
        from utils.RequestAPIJokes import _aclient as client2

        # Verify they're the same instance
        assert client1 is client2

        joke = create_joke(1)

        with patch.object(client1, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = joke

            # Multiple concurrent requests using singleton
            results = await asyncio.gather(*[aget_joke() for _ in range(10)])

            assert len(results) == 10
            # All used the same client
            assert mock_get.call_count == 10

    @pytest.mark.asyncio
    async def test_separate_client_instances_dont_interfere(self, create_joke):
        """Test that separate client instances don't interfere."""
        client1 = AsyncJokeAPIClient()
        client2 = AsyncJokeAPIClient()

        joke1 = create_joke(1)
        joke2 = create_joke(2)

        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = joke1.to_dict()

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = joke2.to_dict()

        mock_async_client1 = AsyncMock()
        mock_async_client1.get.return_value = mock_response1

        mock_async_client2 = AsyncMock()
        mock_async_client2.get.return_value = mock_response2

        call_count = [0]

        def mock_client_factory(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                mock = AsyncMock()
                mock.__aenter__ = AsyncMock(return_value=mock_async_client1)
                mock.__aexit__ = AsyncMock()
                return mock
            else:
                mock = AsyncMock()
                mock.__aenter__ = AsyncMock(return_value=mock_async_client2)
                mock.__aexit__ = AsyncMock()
                return mock

        with patch('httpx.AsyncClient', side_effect=mock_client_factory):
            result1, result2 = await asyncio.gather(
                client1.get_joke(),
                client2.get_joke(),
            )

            # Each client got its own result
            assert result1.id == 1
            assert result2.id == 2


class TestConcurrentEdgeCases:
    """Tests for edge cases in concurrent execution."""

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, create_joke):
        """Test rapid-fire requests with minimal delay."""
        jokes = [create_joke(i) for i in range(1000)]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = jokes

            # Create 1000 tasks as fast as possible
            start = time.time()
            results = await asyncio.gather(*[aget_joke() for _ in range(1000)])
            elapsed = time.time() - start

            assert len(results) == 1000
            # Should complete very quickly since there's no actual I/O
            assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_interleaved_successes_and_failures(self, create_joke):
        """Test interleaved pattern of successes and failures."""
        # Pattern: success, fail, success, fail, ...
        responses = []
        for i in range(100):
            if i % 2 == 0:
                responses.append(create_joke(i))
            else:
                responses.append(JokeAPITimeoutError())

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = responses

            results = await asyncio.gather(
                *[aget_joke() for _ in range(100)],
                return_exceptions=True
            )

            successes = [r for r in results if isinstance(r, Joke)]
            failures = [r for r in results if isinstance(r, JokeAPITimeoutError)]

            assert len(successes) == 50
            assert len(failures) == 50

    @pytest.mark.asyncio
    async def test_nested_concurrent_calls(self, create_joke):
        """Test nested concurrent calls."""
        joke = create_joke(1)

        async def get_multiple_jokes():
            # Each outer call makes 5 inner concurrent calls
            return await asyncio.gather(*[aget_joke() for _ in range(5)])

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = joke

            # 10 outer concurrent calls, each making 5 inner calls = 50 total
            results = await asyncio.gather(*[get_multiple_jokes() for _ in range(10)])

            assert len(results) == 10  # 10 outer results
            assert all(len(r) == 5 for r in results)  # Each has 5 inner results
            assert mock_get.call_count == 50  # Total calls


class TestConcurrencyWithDifferentJokeTypes:
    """Tests for concurrent requests with different joke types."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_all_joke_types(self, create_joke):
        """Test concurrent requests for all joke types."""
        types = ["general", "programming", "knock-knock", "dad"]

        jokes_by_type = {
            t: Jokes(jokes=[create_joke(i, t) for i in range(1, 6)])
            for t in types
        }

        with patch.object(_aclient, 'get_jokes_by_type', new_callable=AsyncMock) as mock_get:
            async def get_by_type(joke_type):
                return jokes_by_type[joke_type]

            mock_get.side_effect = get_by_type

            # Concurrent requests for all types
            tasks = [aget_jokes_by_type(t) for t in types]
            results = await asyncio.gather(*tasks)

            assert len(results) == 4
            for i, joke_type in enumerate(types):
                assert all(j.type == joke_type for j in results[i].jokes)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_by_id_requests(self, create_joke):
        """Test concurrent requests for jokes by different IDs."""
        ids = range(1, 51)  # IDs 1-50

        jokes = {joke_id: create_joke(joke_id) for joke_id in ids}

        with patch.object(_aclient, 'get_joke_by_id', new_callable=AsyncMock) as mock_get:
            async def get_by_id(joke_id):
                return jokes[joke_id]

            mock_get.side_effect = get_by_id

            # Concurrent requests for all IDs
            results = await asyncio.gather(*[aget_joke_by_id(i) for i in ids])

            assert len(results) == 50
            # Verify each joke has correct ID
            for i, joke_id in enumerate(ids):
                assert results[i].id == joke_id
