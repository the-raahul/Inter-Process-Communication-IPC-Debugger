import pytest
from src.core.ipc.pipes import PipeIPC

def test_pipe_send_receive():
    import multiprocessing as mp
    parent_conn, child_conn = mp.Pipe()
    pipe = PipeIPC(parent_conn)
    pipe.send("test")
    assert child_conn.recv() == "test"