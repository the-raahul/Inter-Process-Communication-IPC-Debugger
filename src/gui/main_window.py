from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from src.core.process_manager import ProcessManager
from src.core.ipc.pipes import pipe_process
from src.analysis.event_logger import EventLogger
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPC Debugger")
        self.setGeometry(100, 100, 800, 600)
        
        self.manager = ProcessManager()
        self.logger = EventLogger()
        
        self.setup_ui()

    def setup_ui(self):
        container = QWidget()
        layout = QVBoxLayout()

        self.create_btn = QPushButton("Create Process")
        self.create_btn.clicked.connect(self.create_process)
        layout.addWidget(self.create_btn)

        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)

        self.stop_btn = QPushButton("Stop Process")
        self.stop_btn.clicked.connect(self.stop_process)
        layout.addWidget(self.stop_btn)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_logs()

    def create_process(self):
        name = f"process_{len(self.manager.processes) + 1}"
        self.manager.create_process(name, pipe_process)
        self.logger.log(name, "Created")
        self.update_logs()
        self.update_visualization()

    def send_message(self):
        if self.manager.processes:
            name = list(self.manager.processes.keys())[0]
            self.manager.send_message(name, "Hello")
            response = self.manager.receive_message(name)
            self.logger.log(name, f"Sent: Hello, Received: {response}")
            self.update_logs()

    def stop_process(self):
        if self.manager.processes:
            name = list(self.manager.processes.keys())[0]
            self.manager.stop_process(name)
            self.logger.log(name, "Stopped")
            self.update_logs()
            self.update_visualization()

    def update_logs(self):
        logs = self.logger.get_logs()
        self.log_display.setText("\n".join([f"{row[1]} - {row[2]}: {row[3]}" for row in logs]))

    def update_visualization(self):
        self.ax.clear()
        processes = list(self.manager.processes.keys())
        for i, proc in enumerate(processes):
            self.ax.plot([0, 1], [i, i], 'bo-', label=proc)
        self.ax.legend()
        self.canvas.draw()