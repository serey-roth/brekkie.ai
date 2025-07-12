from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from services.chat_services.chat_session_engine import ChatSessionEngineState


class TestChatSessionEngineState:
    def test_init(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        assert state.is_closed == False
        assert isinstance(state.last_activity_timestamp, datetime)
        assert state.timeout_task is None
        assert state.session_ttl == session_ttl
    
    def test_is_active_when_active(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        assert state.is_active() == True
    
    def test_is_active_when_inactive(self):
        session_ttl = 1
        state = ChatSessionEngineState(session_ttl)
        
        state.last_activity_timestamp = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        assert state.is_active() == False
    
    def test_close(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        mock_task = Mock()
        mock_task.done.return_value = False
        state.timeout_task = mock_task # type: ignore
        
        state.close()
        
        assert state.is_closed == True
        assert isinstance(state.last_activity_timestamp, datetime)
        mock_task.cancel.assert_called_once()
        assert state.timeout_task is None
    
    def test_cleanup_timeout_task_with_running_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        mock_task = Mock()
        mock_task.done.return_value = False
        state.timeout_task = mock_task # type: ignore
        
        state.cleanup_timeout_task()
        
        mock_task.cancel.assert_called_once()
        assert state.timeout_task is None
    
    def test_cleanup_timeout_task_with_done_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        mock_task = Mock()
        mock_task.done.return_value = True
        state.timeout_task = mock_task # type: ignore
        
        state.cleanup_timeout_task()
        
        mock_task.cancel.assert_not_called()
        assert state.timeout_task is None
    
    def test_cleanup_timeout_task_with_no_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        state.cleanup_timeout_task()
        
        assert state.timeout_task is None
    
    def test_is_timeout_task_running_with_running_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        mock_task = Mock()
        mock_task.done.return_value = False
        state.timeout_task = mock_task # type: ignore
        
        assert state.is_timeout_task_running() == True
    
    def test_is_timeout_task_running_with_done_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        mock_task = Mock()
        mock_task.done.return_value = True
        state.timeout_task = mock_task # type: ignore
        
        assert state.is_timeout_task_running() == False
    
    def test_is_timeout_task_running_with_no_task(self):
        session_ttl = 300
        state = ChatSessionEngineState(session_ttl)
        
        assert state.is_timeout_task_running() == False 