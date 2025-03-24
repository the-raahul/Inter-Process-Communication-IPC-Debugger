# IPC Debugger

A powerful tool for debugging and visualizing Inter-Process Communication (IPC) mechanisms. This application provides a graphical interface for monitoring and debugging pipes, message queues, shared memory, and detecting potential deadlocks in your applications.

## Features

- **Pipe Debugging**: Monitor and debug pipe communications between processes
- **Message Queue Debugging**: Track message queue operations and contents
- **Shared Memory Debugging**: Visualize shared memory segments and their usage
- **Deadlock Detection**: Identify potential deadlocks in your application
- **Graphical User Interface**: User-friendly interface for monitoring and debugging
- **Real-time Visualization**: Live updates of IPC operations and states

## Project Structure

```
ipc_debugger/
├── __init__.py
├── gui.py              # Main GUI implementation
├── pipe_debug.py       # Pipe debugging functionality
├── queue_debug.py      # Message queue debugging
├── shared_mem_debug.py # Shared memory debugging
└── deadlock_detector.py # Deadlock detection logic

├── main.py            # Application entry point
├── requirements.txt   # Project dependencies
├── LICENSE           # Project license
└── CHANGELOG.md      # Version history and changes
```

## Prerequisites

- Python 3.x
- NetworkX 2.8.8 (for graph visualization)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ipc-debugger
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application using:
```bash
python main.py
```

The application will launch with a graphical interface where you can:
- Monitor IPC operations in real-time
- Debug pipe communications
- Track message queue operations
- Visualize shared memory usage
- Detect potential deadlocks

## Development

The project includes several utility scripts:
- `check_size.sh`: Check project size and dependencies
- `cleanup.sh`: Clean temporary files and caches
- `verify_structure.sh`: Verify project structure integrity

## License

This project is licensed under the terms specified in the LICENSE file.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes. 
