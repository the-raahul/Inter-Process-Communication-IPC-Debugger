from src.core.ipc.base import IPCBase

def pipe_process(conn):
    while True:
        try:
            msg = conn.recv()
            print(f"Process received: {msg}")
            conn.send(f"Echo: {msg}")
        except EOFError:
            break

class PipeIPC(IPCBase):
    def __init__(self, conn):
        self.conn = conn

    def send(self, data):
        self.conn.send(data)

    def receive(self):
        if self.conn.poll():
            return self.conn.recv()
        return None