from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from services.websocket_event_sender import WebSocketEventSender


@pytest.fixture
def mock_websocket():
    websocket = MagicMock(spec=WebSocket)
    websocket.client_state = WebSocketState.CONNECTED
    websocket.send_json = AsyncMock()
    return websocket


@pytest.fixture
def websocket_sender():
    return WebSocketEventSender()


@pytest.mark.asyncio
async def test_send_event_success(mock_websocket, websocket_sender):
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is True
    mock_websocket.send_json.assert_called_once_with({
        "event": event,
        "data": data
    })


@pytest.mark.asyncio
async def test_send_event_disconnected_websocket(mock_websocket, websocket_sender):
    mock_websocket.client_state = WebSocketState.DISCONNECTED
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is False
    mock_websocket.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_send_event_connecting_websocket(mock_websocket, websocket_sender):
    mock_websocket.client_state = WebSocketState.CONNECTING
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is False
    mock_websocket.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_send_event_exception_handling(mock_websocket, websocket_sender):
    mock_websocket.send_json.side_effect = Exception("Connection error")
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is False
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_send_event_with_complex_data(mock_websocket, websocket_sender):
    event = "recipe_completed"
    data = {
        "recipe": {
            "name": "Pasta Carbonara",
            "ingredients": ["pasta", "eggs", "bacon"],
            "instructions": ["Boil pasta", "Mix ingredients"]
        },
        "metadata": {
            "generation_time": 2.5,
            "user_id": "user123"
        }
    }
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is True
    mock_websocket.send_json.assert_called_once_with({
        "event": event,
        "data": data
    })


@pytest.mark.asyncio
async def test_send_event_with_empty_data(mock_websocket, websocket_sender):
    event = "ping"
    data = {}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is True
    mock_websocket.send_json.assert_called_once_with({
        "event": event,
        "data": data
    })


@pytest.mark.asyncio
async def test_send_event_with_none_data(mock_websocket, websocket_sender):
    event = "any_event"
    data = None
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is True
    mock_websocket.send_json.assert_called_once_with({
        "event": event,
        "data": data
    })


@pytest.mark.asyncio
async def test_send_event_websocket_close_exception(mock_websocket, websocket_sender):
    mock_websocket.send_json.side_effect = ConnectionResetError("Connection reset")
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is False
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_send_event_timeout_exception(mock_websocket, websocket_sender):
    mock_websocket.send_json.side_effect = TimeoutError("Send timeout")
    event = "test_event"
    data = {"key": "value"}
    
    result = await websocket_sender.send_event(mock_websocket, event, data)
    
    assert result is False
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_send_event_always_sleeps(mock_websocket, websocket_sender):
    with patch("asyncio.sleep") as mock_sleep:
        event = "test_event"
        data = {"key": "value"}
        
        result = await websocket_sender.send_event(mock_websocket, event, data)
        
        assert result is True
        mock_sleep.assert_called_once_with(0.01)


@pytest.mark.asyncio
async def test_send_event_sleeps_even_on_exception(mock_websocket, websocket_sender):
    mock_websocket.send_json.side_effect = Exception("Test error")
    
    with patch("asyncio.sleep") as mock_sleep:
        event = "test_event"
        data = {"key": "value"}
        
        result = await websocket_sender.send_event(mock_websocket, event, data)
        
        assert result is False
        mock_sleep.assert_called_once_with(0.01)


@pytest.mark.asyncio
async def test_send_event_multiple_calls(mock_websocket, websocket_sender):
    events = [
        ("event1", {"data": "value1"}),
        ("event2", {"data": "value2"}),
        ("event3", {"data": "value3"})
    ]
    
    results = []
    for event, data in events:
        result = await websocket_sender.send_event(mock_websocket, event, data)
        results.append(result)
    
    assert all(results)
    assert mock_websocket.send_json.call_count == 3
    
    # Check each call individually to avoid dictionary key order issues
    calls = mock_websocket.send_json.call_args_list
    assert len(calls) == 3
    
    for i, (event, data) in enumerate(events):
        call_args = calls[i][0][0]  # Get the first argument of the call
        assert call_args["event"] == event
        assert call_args["data"] == data 