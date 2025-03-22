import multiprocessing as mp

class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.pipes = {}

    def create_process(self, name, target_func):
        parent_conn, child_conn = mp.Pipe()
        process = mp.Process(target=target_func, args=(child_conn,))
        self.processes[name] = process
        self.pipes[name] = parent_conn
        process.start()
        return parent_conn

    def send_message(self, name, message):
        if name in self.pipes:
            self.pipes[name].send(message)

    def receive_message(self, name):
        if name in self.pipes and self.pipes[name].poll():
            return self.pipes[name].recv()
        return None

    def stop_process(self, name):
        if name in self.processes:
            self.processes[name].terminate()
            del self.processes[name]
            del self.pipes[name]