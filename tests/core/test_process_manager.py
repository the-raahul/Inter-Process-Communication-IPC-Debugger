import pytest
from src.core.process_manager import ProcessManager

def test_process_creation():
    pm = ProcessManager()
    pm.create_process("test", lambda conn: None)
    assert "test" in pm.processes