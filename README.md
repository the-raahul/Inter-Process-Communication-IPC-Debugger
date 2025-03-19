# Inter-Process-Communication-IPC-Debugger

# IPC Debugger
A tool for debugging inter-process communication.

## Installation
1. Install Python 3.8+
2. Run ./scripts/setup.sh

## Usage
Run python main.py



# IPC Debugger

The IPC Debugger is a tool designed to simulate, visualize, and debug inter-process communication (IPC) mechanisms in software applications. This project provides a modular framework for analyzing IPC, with a focus on pipes, real-time logging, and a simple graphical user interface (GUI). It was developed as a proof-of-concept with core functionality implemented and additional features planned for future expansion.

## Features

### Implemented Features
- *Process Creation and Management*: Dynamically create and manage processes using Python's multiprocessing module.
- *Pipe-Based IPC*: Communicate between processes using pipes, with message sending and echoing capabilities.
- *Real-Time Event Logging*: Log events (e.g., process creation, message passing, termination) to an SQLite database (ipc_events.db) and display them in the GUI.
- *Basic GUI Interface*: A PyQt6-based interface with buttons for creating processes, sending messages, and stopping processes, plus a log display and simple visualization.
- *Simple Process Visualization*: A Matplotlib plot showing active processes as horizontal lines, updated in real-time.
- *Process Termination*: Stop individual processes with updates reflected in logs and visualization.
- *Modular Design*: Organized codebase for extensibility.
- *Unit Tests*: Basic tests for process management and pipe IPC using pytest.
- *Example Script*: A standalone demo of pipe communication (examples/simple_pipe_example.py).

### Planned Features (Placeholders)
Due to time constraints, the following features are included as placeholders and not fully implemented:

- *Multiple IPC Mechanisms*: Message queues and shared memory (placeholders in src/core/ipc/).
- *Deadlock Detection*: Algorithms to identify synchronization issues (placeholder in src/analysis/deadlock_detector.py).
- *Bottleneck Analysis*: Performance bottleneck identification (placeholder in src/analysis/bottleneck_analyzer.py).
- *Advanced Performance Metrics*: Detailed IPC metrics (basic implementation in src/analysis/performance_metrics.py).
- *Enhanced Visualization*: Interactive process graphs and data flow animations (placeholders in src/gui/process_view.py, src/gui/data_flow_view.py).
- *IPC Configuration*: User-configurable IPC settings (placeholder in src/gui/config_panel.py).
- *Synchronization Primitives*: Semaphores and mutexes for testing (basic class in src/core/ipc/sync_primitives.py).

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. *Clone or Extract the Project:*  
   If downloaded as a zip, extract it to a directory (e.g., ipc-debugger/).

2. *Navigate to the Project Directory:*
   bash
   cd ipc-debugger
   

3. *Install Dependencies:*
   bash
   pip install -r requirements.txt
   
   Required packages: pyqt6, matplotlib, networkx, pytest.

4. *(Optional) Make Scripts Executable (Linux/macOS):*
   bash
   chmod +x scripts/setup.sh scripts/run_tests.sh
   ./scripts/setup.sh
   

## Usage

### Running the Application
1. *Start the Program:*
   bash
   python main.py
   
   A GUI window will open titled "IPC Debugger".

2. *Interact with the GUI:*
   - *Create Process*: Click to spawn a new process (e.g., process_1). Logs and plot update.
   - *Send Message*: Send "Hello" to the first process, which echoes it back. Logs update with sent/received messages.
   - *Stop Process*: Terminate the first process. Logs and plot update.
   - *Logs*: View real-time event logs in the text area.
   - *Visualization*: See active processes as lines in the plot.

3. *Check Terminal Output:*
   - Process messages (e.g., "Process received: Hello") appear in the terminal.

### Running Tests
Execute unit tests:
bash
pytest tests/

Tests verify process creation and pipe communication.

### Running Examples
Try the pipe example:
bash
python examples/simple_pipe_example.py

Demonstrates standalone pipe IPC.

## Directory Structure


ipc-debugger/
│
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── process_manager.py      # Process creation and management
│   │   ├── ipc/                   # IPC mechanisms
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Abstract IPC base class
│   │   │   ├── pipes.py           # Pipe IPC implementation
│   │   │   ├── message_queues.py  # Message queue placeholder
│   │   │   ├── shared_memory.py   # Shared memory placeholder
│   │   │   └── sync_primitives.py # Synchronization primitives (basic)
│   │   └── data_tracker.py        # Data flow tracking (basic)
│   │
│   ├── analysis/          # Analysis tools
│   │   ├── __init__.py
│   │   ├── deadlock_detector.py    # Deadlock detection placeholder
│   │   ├── bottleneck_analyzer.py  # Bottleneck analysis placeholder
│   │   ├── performance_metrics.py  # Basic performance metrics
│   │   └── event_logger.py         # SQLite event logging
│   │
│   └── gui/               # GUI components
│       ├── __init__.py
│       ├── main_window.py          # Main GUI window
│       ├── process_view.py         # Process visualization placeholder
│       ├── data_flow_view.py       # Data flow animation placeholder
│       ├── metrics_view.py         # Metrics display placeholder
│       ├── config_panel.py         # Configuration placeholder
│       └── resources/              # Empty directory for GUI resources
│
├── tests/                 # Unit tests
│   ├── core/
│   │   ├── test_process_manager.py
│   │   └── test_ipc/
│   │       ├── test_pipes.py
│   │       ├── test_message_queues.py
│   │       └── test_shared_memory.py
│   ├── analysis/
│   │   ├── test_deadlock_detector.py
│   │   └── test_performance_metrics.py
│   └── gui/
│       └── test_process_view.py
│
├── examples/              # Example scripts
│   ├── simple_pipe_example.py
│   ├── message_queue_demo.py
│   └── deadlock_scenario.py
│
├── docs/                  # Documentation
│   ├── user_manual.md
│   ├── api_reference.md
│   └── developer_guide.md
│
├── scripts/               # Utility scripts
│   ├── setup.sh          # Install dependencies
│   └── run_tests.sh      # Run tests
│
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── setup.py              # Setup script
└── main.py               # Entry point
