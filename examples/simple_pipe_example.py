from src.core.process_manager import ProcessManager
from src.core.ipc.pipes import pipe_process

pm = ProcessManager()
pm.create_process("p1", pipe_process)
pm.send_message("p1", "Hello from example")
print(pm.receive_message("p1"))
pm.stop_process("p1")