"""
GUI implementation for IPC Debugger using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import queue
import datetime
import math
import random

from .pipe_debug import PipeDebugger
from .queue_debug import QueueDebugger 
from .shared_mem_debug import SharedMemoryDebugger
from .deadlock_detector import DeadlockDetector

class IPCDebuggerGUI:
    def __init__(self, root):
        """Initialize the IPC Debugger GUI"""
        self.root = root
        self.root.title("IPC Debugger")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initialize debuggers
        self.pipe_debugger = PipeDebugger()
        self.queue_debugger = QueueDebugger()
        self.shared_mem_debugger = SharedMemoryDebugger()
        self.deadlock_detector = DeadlockDetector()
        
        # Variables for process filtering and auto-analysis
        self.filtered_processes = None
        self.auto_analyze_active = False
        
        # Setup UI
        self._setup_ui()
        
        # Start UI refresh
        self.refresh_rate = 500  # milliseconds
        self._refresh_ui()
        
        # Start resource cleanup (every 10 minutes)
        self.root.after(600000, self._cleanup_resources)
        
        # Start simulation for demo purposes
        self.simulate_ipc_activity()
    
    def _setup_ui(self):
        """Create the main UI elements"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        overview_tab = ttk.Frame(notebook)
        pipes_tab = ttk.Frame(notebook)
        queues_tab = ttk.Frame(notebook)
        shared_mem_tab = ttk.Frame(notebook)
        deadlock_tab = ttk.Frame(notebook)
        
        # Setup each tab
        self._setup_overview_tab(notebook)
        self._setup_pipes_tab(pipes_tab)
        self._setup_queues_tab(queues_tab)
        self._setup_shared_mem_tab(shared_mem_tab)
        self._setup_deadlock_tab(deadlock_tab)
        
        # Add tabs to notebook
        notebook.add(pipes_tab, text="Pipes")
        notebook.add(queues_tab, text="Message Queues")
        notebook.add(shared_mem_tab, text="Shared Memory")
        notebook.add(deadlock_tab, text="Deadlock Detection")
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_overview_tab(self, notebook):
        """Set up the overview tab"""
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="Overview")
        
        # Create top control area with demo button
        control_frame = ttk.Frame(overview_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        demo_button = ttk.Button(control_frame, text="Run Demo Simulation", 
                                command=self.simulate_ipc_activity)
        demo_button.pack(side=tk.RIGHT, padx=5)
        
        # Create summary frames
        summary_frame = ttk.Frame(overview_frame)
        summary_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Create IPC type summary frames
        pipe_frame = ttk.LabelFrame(summary_frame, text="Pipes")
        pipe_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.pipe_count = ttk.Label(pipe_frame, text="Active: 0")
        self.pipe_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        queue_frame = ttk.LabelFrame(summary_frame, text="Message Queues")
        queue_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.queue_count = ttk.Label(queue_frame, text="Active: 0")
        self.queue_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.queue_messages = ttk.Label(queue_frame, text="Messages: 0")
        self.queue_messages.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        shm_frame = ttk.LabelFrame(summary_frame, text="Shared Memory")
        shm_frame.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self.shm_count = ttk.Label(shm_frame, text="Active: 0")
        self.shm_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.shm_access = ttk.Label(shm_frame, text="Accesses: 0")
        self.shm_access.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        deadlock_frame = ttk.LabelFrame(summary_frame, text="Deadlock Detection")
        deadlock_frame.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.process_count = ttk.Label(deadlock_frame, text="Processes: 0")
        self.process_count.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.resource_count = ttk.Label(deadlock_frame, text="Resources: 0")
        self.resource_count.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.deadlock_count = ttk.Label(deadlock_frame, text="Deadlocks: 0")
        self.deadlock_count.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        
        # Configure grid columns to be evenly sized
        for i in range(4):
            summary_frame.columnconfigure(i, weight=1)
        
        # Create visualization frame
        viz_frame = ttk.LabelFrame(overview_frame, text="System Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.overview_canvas = tk.Canvas(viz_frame, bg="white")
        self.overview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create metrics frame
        metrics_frame = ttk.LabelFrame(overview_frame, text="System Metrics")
        metrics_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # Setup metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Label(metrics_grid, text="CPU Usage:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cpu_usage = ttk.Label(metrics_grid, text="0%")
        self.cpu_usage.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="Memory Usage:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.memory_usage = ttk.Label(metrics_grid, text="0 MB")
        self.memory_usage.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="IPC Throughput:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.ipc_throughput = ttk.Label(metrics_grid, text="0 ops/sec")
        self.ipc_throughput.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(metrics_grid, text="Active Processes:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.active_process_count = ttk.Label(metrics_grid, text="0")
        self.active_process_count.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        # Event log frame
        log_frame = ttk.LabelFrame(overview_frame, text="Event Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log filter frame
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.log_filter_var = tk.StringVar()
        log_filter_entry = ttk.Entry(filter_frame, textvariable=self.log_filter_var, width=30)
        log_filter_entry.pack(side=tk.LEFT, padx=5)
        
        apply_filter_btn = ttk.Button(filter_frame, text="Apply Filter", command=self._apply_log_filter)
        apply_filter_btn.pack(side=tk.LEFT, padx=5)
        
        clear_filter_btn = ttk.Button(filter_frame, text="Clear Filter", command=self._clear_log_filter)
        clear_filter_btn.pack(side=tk.LEFT, padx=5)
        
        # Log type checkboxes
        log_type_frame = ttk.Frame(filter_frame)
        log_type_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(log_type_frame, text="Show:").pack(side=tk.LEFT, padx=2)
        
        self.show_pipe_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Pipes", variable=self.show_pipe_logs, 
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_queue_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Queues", variable=self.show_queue_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_shm_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Shared Memory", variable=self.show_shm_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        self.show_deadlock_logs = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_type_frame, text="Deadlocks", variable=self.show_deadlock_logs,
                       command=self._update_log_text).pack(side=tk.LEFT, padx=2)
        
        # Log text area with scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_text_frame, height=10, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Initialize log filter
        self.log_filter = None
    
    def _setup_pipes_tab(self, tab):
        """Set up the pipes tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Pipe IPC Debugger", font=("Arial", 16)).pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Pipe ID:").pack(side=tk.LEFT, padx=5)
        self.pipe_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.pipe_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Pipe", command=self._create_pipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Pipe", command=self._delete_pipe).pack(side=tk.LEFT, padx=5)
        
        # Pipe operations frame
        ops_frame = ttk.LabelFrame(frame, text="Pipe Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Pipe ID:").pack(side=tk.LEFT, padx=5)
        self.op_pipe_id_var = tk.StringVar()
        self.pipe_dropdown = ttk.Combobox(op_controls, textvariable=self.op_pipe_id_var, state="readonly")
        self.pipe_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Writer PID:").pack(side=tk.LEFT, padx=5)
        self.pipe_writer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.pipe_writer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Reader PID:").pack(side=tk.LEFT, padx=5)
        self.pipe_reader_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.pipe_reader_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Set PIDs", command=self._set_pipe_pids).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Transfer", command=self._simulate_pipe_transfer).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Bottleneck", command=self._simulate_pipe_bottleneck).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Pipe Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.pipe_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.pipe_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.pipe_status_text.config(state=tk.DISABLED)
        
    def _setup_queues_tab(self, tab):
        """Set up the message queues tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Message Queue Debugger", font=("Arial", 16)).pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Queue ID:").pack(side=tk.LEFT, padx=5)
        self.queue_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.queue_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Capacity:").pack(side=tk.LEFT, padx=5)
        self.queue_capacity_var = tk.StringVar(value="10")
        ttk.Entry(control_frame, textvariable=self.queue_capacity_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Queue", command=self._create_queue).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Queue", command=self._delete_queue).pack(side=tk.LEFT, padx=5)
        
        # Queue operations frame
        ops_frame = ttk.LabelFrame(frame, text="Queue Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Queue ID:").pack(side=tk.LEFT, padx=5)
        self.op_queue_id_var = tk.StringVar()
        self.queue_dropdown = ttk.Combobox(op_controls, textvariable=self.op_queue_id_var, state="readonly")
        self.queue_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Producer PID:").pack(side=tk.LEFT, padx=5)
        self.queue_producer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.queue_producer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Consumer PID:").pack(side=tk.LEFT, padx=5)
        self.queue_consumer_pid_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.queue_consumer_pid_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Set PIDs", command=self._set_queue_pids).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Enqueue", command=self._enqueue_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Dequeue", command=self._dequeue_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Simulate Slow Consumer", command=self._simulate_slow_consumer).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Queue Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.queue_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.queue_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.queue_status_text.config(state=tk.DISABLED)
        
    def _setup_shared_mem_tab(self, tab):
        """Set up the shared memory tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(frame, text="Shared Memory Debugger", font=("Arial", 16)).pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Memory ID:").pack(side=tk.LEFT, padx=5)
        self.memory_id_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.memory_id_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Size (bytes):").pack(side=tk.LEFT, padx=5)
        self.memory_size_var = tk.StringVar(value="1024")
        ttk.Entry(control_frame, textvariable=self.memory_size_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Create Memory Segment", 
                  command=self._create_shared_memory).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Delete Memory Segment", 
                  command=self._delete_shared_memory).pack(side=tk.LEFT, padx=5)
        
        # Memory operations frame
        ops_frame = ttk.LabelFrame(frame, text="Memory Operations")
        ops_frame.pack(fill=tk.X, pady=10)
        
        op_controls = ttk.Frame(ops_frame)
        op_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_controls, text="Memory ID:").pack(side=tk.LEFT, padx=5)
        self.op_memory_id_var = tk.StringVar()
        self.memory_dropdown = ttk.Combobox(op_controls, textvariable=self.op_memory_id_var, state="readonly")
        self.memory_dropdown.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Process ID:").pack(side=tk.LEFT, padx=5)
        self.memory_process_id_var = tk.StringVar()
        ttk.Entry(op_controls, textvariable=self.memory_process_id_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Offset:").pack(side=tk.LEFT, padx=5)
        self.memory_offset_var = tk.StringVar(value="0")
        ttk.Entry(op_controls, textvariable=self.memory_offset_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(op_controls, text="Size:").pack(side=tk.LEFT, padx=5)
        self.memory_op_size_var = tk.StringVar(value="128")
        ttk.Entry(op_controls, textvariable=self.memory_op_size_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(op_controls, text="Read", command=self._read_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Write", command=self._write_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Lock", command=self._lock_shared_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_controls, text="Unlock", command=self._unlock_shared_memory).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Shared Memory Status")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.shm_status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.shm_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.shm_status_text.config(state=tk.DISABLED)
    
    def _setup_deadlock_tab(self, tab):
        """Set up the deadlock detection tab"""
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left control panel
        control_frame = ttk.LabelFrame(frame, text="Deadlock Controls")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Process controls
        ttk.Label(control_frame, text="Process Management:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        process_frame = ttk.Frame(control_frame)
        process_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(process_frame, text="Process ID:").pack(side=tk.LEFT)
        self.process_id_var = tk.StringVar(value="process_1")
        ttk.Entry(process_frame, textvariable=self.process_id_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(control_frame, text="Register Process", command=self._register_process).pack(pady=5, padx=10, fill=tk.X)
        
        # Process selection and unregistration
        process_select_frame = ttk.Frame(control_frame)
        process_select_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(process_select_frame, text="Select Process:").pack(side=tk.LEFT)
        self.selected_process_var = tk.StringVar(value="None")
        self.process_dropdown = ttk.Combobox(process_select_frame, textvariable=self.selected_process_var, state="readonly")
        self.process_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(control_frame, text="Unregister Process", command=self._unregister_process).pack(pady=5, padx=10, fill=tk.X)
        
        # Process filter
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.process_filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.process_filter_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        filter_buttons_frame = ttk.Frame(control_frame)
        filter_buttons_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(filter_buttons_frame, text="Apply Filter", command=self._apply_process_filter).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(filter_buttons_frame, text="Clear Filter", command=self._clear_process_filter).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Resource controls
        ttk.Label(control_frame, text="Resource Management:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        resource_frame = ttk.Frame(control_frame)
        resource_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(resource_frame, text="Resource ID:").pack(side=tk.LEFT)
        self.resource_id_var = tk.StringVar(value="resource_1")
        ttk.Entry(resource_frame, textvariable=self.resource_id_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(control_frame, text="Register Resource", command=self._register_resource).pack(pady=5, padx=10, fill=tk.X)
        
        # Request/release controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        
        ttk.Label(control_frame, text="Process:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        self.process_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_process_var)
        self.process_dropdown.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(control_frame, text="Resource:").pack(pady=(5, 0), padx=10, anchor=tk.W)
        self.selected_resource_var = tk.StringVar(value="None")
        self.resource_dropdown = ttk.Combobox(control_frame, textvariable=self.selected_resource_var)
        self.resource_dropdown.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(control_frame, text="Request Resource", command=self._request_resource).pack(pady=5, padx=10, fill=tk.X)
        ttk.Button(control_frame, text="Release Resource", command=self._release_resource).pack(pady=5, padx=10, fill=tk.X)
        
        # Analysis controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        ttk.Label(control_frame, text="Analysis:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        analysis_frame = ttk.Frame(control_frame)
        analysis_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Button(analysis_frame, text="Analyze", command=self._analyze_deadlocks).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.auto_analyze_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(analysis_frame, text="Auto", variable=self.auto_analyze_var, 
                       command=self._toggle_auto_analysis).pack(side=tk.LEFT, padx=(5, 0))
        
        # Simulation controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        ttk.Label(control_frame, text="Simulation:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        sim_frame = ttk.Frame(control_frame)
        sim_frame.pack(pady=5, padx=10, fill=tk.X)
        
        ttk.Label(sim_frame, text="Processes:").pack(side=tk.LEFT)
        self.sim_processes_var = tk.StringVar(value="3")
        ttk.Entry(sim_frame, textvariable=self.sim_processes_var, width=3).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sim_frame, text="Resources:").pack(side=tk.LEFT)
        self.sim_resources_var = tk.StringVar(value="3")
        ttk.Entry(sim_frame, textvariable=self.sim_resources_var, width=3).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Simulate Deadlock", command=self._simulate_deadlock).pack(pady=5, padx=10, fill=tk.X)
        
        # Deadlock visualization area
        vis_frame = ttk.LabelFrame(frame, text="Deadlock Visualization")
        vis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for deadlock visualization (wait-for graph)
        canvas_frame = ttk.Frame(vis_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.deadlock_canvas = tk.Canvas(canvas_frame, bg="white")
        self.deadlock_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars for large graphs
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.deadlock_canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.deadlock_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.deadlock_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        self.deadlock_canvas.configure(scrollregion=(0, 0, 1000, 1000))
        
        # Add zoom controls
        zoom_frame = ttk.Frame(vis_frame)
        zoom_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(zoom_frame, text="Zoom In", command=self._zoom_in_deadlock).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self._zoom_out_deadlock).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self._reset_deadlock_view).pack(side=tk.LEFT, padx=2)
        
        # Setup canvas interactions
        self.deadlock_canvas.bind("<ButtonPress-1>", self._deadlock_canvas_click)
        self.deadlock_canvas.bind("<B1-Motion>", self._deadlock_canvas_drag)
        self.deadlock_canvas.bind("<MouseWheel>", self._deadlock_canvas_zoom)  # Windows/macOS
        self.deadlock_canvas.bind("<Button-4>", self._deadlock_canvas_zoom)    # Linux scroll up
        self.deadlock_canvas.bind("<Button-5>", self._deadlock_canvas_zoom)    # Linux scroll down
        
        # Initialize canvas state
        self.deadlock_canvas_scale = 1.0
        self.deadlock_canvas_drag_start = None
        self.deadlock_canvas_clicked_item = None
        
        # Deadlock status display
        status_frame = ttk.LabelFrame(vis_frame, text="Deadlock Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label for quick overview
        self.deadlock_status = ttk.Label(status_frame, text="No deadlocks detected")
        self.deadlock_status.pack(fill=tk.X, padx=5, pady=5)
        
        # Detailed status text
        self.deadlock_status_text = scrolledtext.ScrolledText(status_frame, height=5)
        self.deadlock_status_text.pack(fill=tk.BOTH, expand=True)
        self.deadlock_status_text.config(state=tk.DISABLED)
        
        # Suggestions area
        suggestion_frame = ttk.LabelFrame(vis_frame, text="Analysis & Suggestions")
        suggestion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.deadlock_suggestion_text = scrolledtext.ScrolledText(suggestion_frame, height=3)
        self.deadlock_suggestion_text.pack(fill=tk.BOTH, expand=True)
        self.deadlock_suggestion_text.config(state=tk.DISABLED)
        
        # Initialize process filter
        self.filtered_processes = None
        self.auto_analyze_active = False
    
    # ------ Action Callbacks ------
    
    # Pipe actions
    def _create_pipe(self):
        """Create a new pipe"""
        pipe_id = self.pipe_id_var.get()
        if pipe_id:
            self.pipe_debugger.register_pipe(pipe_id)
            self._update_pipe_ui()
            self.status_bar.config(text=f"Pipe {pipe_id} created")
    
    def _delete_pipe(self):
        """Delete a pipe"""
        pipe_id = self.op_pipe_id_var.get()
        if pipe_id:
            self.pipe_debugger.unregister_pipe(pipe_id)
            self._update_pipe_ui()
            self.status_bar.config(text=f"Pipe {pipe_id} deleted")
    
    def _set_pipe_pids(self):
        """Set writer and reader PIDs for a pipe"""
        pipe_id = self.op_pipe_id_var.get()
        writer_pid = self.pipe_writer_pid_var.get()
        reader_pid = self.pipe_reader_pid_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            
            if writer_pid:
                pipe_status["writer_pid"] = writer_pid
            
            if reader_pid:
                pipe_status["reader_pid"] = reader_pid
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self._update_pipe_ui()
            self.status_bar.config(text=f"PIDs updated for pipe {pipe_id}")
    
    def _simulate_pipe_transfer(self):
        """Simulate data transfer through pipe"""
        pipe_id = self.op_pipe_id_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            pipe_status["status"] = "transferring"
            pipe_status["progress"] = 0
            pipe_status["bytes_transferred"] = random.randint(1000, 10000)
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self.pipe_debugger.add_log_entry(pipe_id, "Started data transfer")
            
            # Simulate progress updates
            def update_progress(p_id, progress):
                if progress <= 100:
                    p_status = self.pipe_debugger.get_pipe_status().get(p_id, {}).copy()
                    if p_status and p_status.get("status") == "transferring":
                        p_status["progress"] = progress
                        self.pipe_debugger.update_pipe_status(p_id, p_status)
                        self._update_pipe_ui()
                        
                        # Schedule next update
                        if progress < 100:
                            self.root.after(300, update_progress, p_id, progress + 10)
                        else:
                            p_status["status"] = "idle"
                            self.pipe_debugger.update_pipe_status(p_id, p_status)
                            self.pipe_debugger.add_log_entry(p_id, "Transfer completed")
            
            # Start progress updates
            self.root.after(300, update_progress, pipe_id, 10)
            self.status_bar.config(text=f"Transfer started on pipe {pipe_id}")
    
    def _simulate_pipe_bottleneck(self):
        """Simulate a bottleneck in the pipe"""
        pipe_id = self.op_pipe_id_var.get()
        
        if pipe_id:
            pipe_status = self.pipe_debugger.get_pipe_status().get(pipe_id, {}).copy()
            pipe_status["status"] = "bottleneck"
            pipe_status["progress"] = 50  # Stuck at 50%
            
            self.pipe_debugger.update_pipe_status(pipe_id, pipe_status)
            self.pipe_debugger.add_log_entry(pipe_id, "Bottleneck detected")
            self._update_pipe_ui()
            self.status_bar.config(text=f"Bottleneck simulated on pipe {pipe_id}")
    
    # Queue actions
    def _create_queue(self):
        """Create a new message queue"""
        queue_id = self.queue_id_var.get()
        capacity = int(self.queue_capacity_var.get() or "10")
        
        if queue_id:
            self.queue_debugger.register_queue(queue_id, capacity)
            self._update_queue_ui()
            self.status_bar.config(text=f"Queue {queue_id} created with capacity {capacity}")
    
    def _delete_queue(self):
        """Delete a message queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            self.queue_debugger.unregister_queue(queue_id)
            self._update_queue_ui()
            self.status_bar.config(text=f"Queue {queue_id} deleted")
    
    def _set_queue_pids(self):
        """Set producer and consumer PIDs for a queue"""
        queue_id = self.op_queue_id_var.get()
        producer_pid = self.queue_producer_pid_var.get()
        consumer_pid = self.queue_consumer_pid_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if producer_pid:
                queue_status["producer_pid"] = producer_pid
            
            if consumer_pid:
                queue_status["consumer_pid"] = consumer_pid
            
            self.queue_debugger.update_queue_status(queue_id, queue_status)
            self._update_queue_ui()
            self.status_bar.config(text=f"PIDs updated for queue {queue_id}")
    
    def _enqueue_message(self):
        """Enqueue a message to the selected queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status and queue_status.get("message_count", 0) < queue_status.get("capacity", 10):
                queue_status["message_count"] = queue_status.get("message_count", 0) + 1
                queue_status["status"] = "active"
                
                self.queue_debugger.update_queue_status(queue_id, queue_status)
                self.queue_debugger.add_log_entry(queue_id, "Message enqueued")
                self._update_queue_ui()
                self.status_bar.config(text=f"Message enqueued to queue {queue_id}")
            else:
                self.status_bar.config(text=f"Queue {queue_id} is full")
    
    def _dequeue_message(self):
        """Dequeue a message from the selected queue"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status and queue_status.get("message_count", 0) > 0:
                queue_status["message_count"] = queue_status.get("message_count", 0) - 1
                
                if queue_status["message_count"] == 0:
                    queue_status["status"] = "idle"
                
                self.queue_debugger.update_queue_status(queue_id, queue_status)
                self.queue_debugger.add_log_entry(queue_id, "Message dequeued")
                self._update_queue_ui()
                self.status_bar.config(text=f"Message dequeued from queue {queue_id}")
            else:
                self.status_bar.config(text=f"Queue {queue_id} is empty")
    
    def _simulate_slow_consumer(self):
        """Simulate a slow consumer scenario with queue filling up"""
        queue_id = self.op_queue_id_var.get()
        
        if queue_id:
            queue_status = self.queue_debugger.get_queue_status().get(queue_id, {}).copy()
            
            if queue_status:
                capacity = queue_status.get("capacity", 10)
                
                # Fill up the queue gradually
                def fill_queue(q_id, count):
                    q_status = self.queue_debugger.get_queue_status().get(q_id, {}).copy()
                    
                    if q_status and count < capacity:
                        q_status["message_count"] = count + 1
                        q_status["status"] = "active"
                        
                        if q_status["message_count"] >= capacity:
                            q_status["status"] = "full"
                            self.queue_debugger.add_log_entry(q_id, "Queue is full - slow consumer detected")
                        
                        self.queue_debugger.update_queue_status(q_id, q_status)
                        self._update_queue_ui()
                        
                        # Schedule next fill
                        self.root.after(500, fill_queue, q_id, count + 1)
                
                # Start filling
                current_count = queue_status.get("message_count", 0)
                self.root.after(500, fill_queue, queue_id, current_count)
                self.status_bar.config(text=f"Simulating slow consumer on queue {queue_id}")
    
    # Shared memory actions
    def _create_shared_memory(self):
        """Create a new shared memory segment"""
        memory_id = self.memory_id_var.get()
        size = int(self.memory_size_var.get() or "1024")
        
        if memory_id:
            self.shared_mem_debugger.register_memory_segment(memory_id, size)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} created with size {size} bytes")
    
    def _delete_shared_memory(self):
        """Delete a shared memory segment"""
        memory_id = self.memory_id_var.get()
        
        if memory_id:
            self.shared_mem_debugger.unregister_memory_segment(memory_id)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} deleted")
            
    def _read_shared_memory(self):
        """Simulate reading from shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Update memory status
                memory_status["status"] = "active"
                memory_status["access_count"] = memory_status.get("access_count", 0) + 1
                
                # Add to recent readers
                recent_readers = memory_status.get("recent_readers", [])
                if process_id not in recent_readers:
                    recent_readers.append(process_id)
                memory_status["recent_readers"] = recent_readers
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Read by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Read from shared memory {memory_id}")
    
    def _write_shared_memory(self):
        """Simulate writing to shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Update memory status
                memory_status["status"] = "active"
                memory_status["access_count"] = memory_status.get("access_count", 0) + 1
                memory_status["last_writer"] = process_id
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Written by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Wrote to shared memory {memory_id}")
    
    def _lock_shared_memory(self):
        """Simulate locking a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Add locked region
                locked_regions = memory_status.get("locked_regions", [])
                new_region = {"offset": offset, "size": size, "owner": process_id}
                locked_regions.append(new_region)
                memory_status["locked_regions"] = locked_regions
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Region locked by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Locked region in shared memory {memory_id}")
    
    def _unlock_shared_memory(self):
        """Simulate unlocking a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            if memory_status:
                # Remove matching locked region
                locked_regions = memory_status.get("locked_regions", [])
                memory_status["locked_regions"] = [
                    r for r in locked_regions 
                    if not (r.get("offset") == offset and r.get("size") == size)
                ]
                
                self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
                self.shared_mem_debugger.add_log_entry(
                    memory_id, f"Region unlocked by {process_id} at offset {offset}, size {size} bytes"
                )
                self._update_shm_ui()
                self.status_bar.config(text=f"Unlocked region in shared memory {memory_id}")
    
    # Deadlock actions
    def _register_process(self):
        """Register a process for deadlock detection"""
        process_id = self.process_id_var.get()
        if process_id:
            self.deadlock_detector.register_process(process_id)
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} registered")
    
    def _unregister_process(self):
        """Unregister a process from deadlock detection"""
        process_id = self.process_id_var.get()
        if process_id:
            self.deadlock_detector.unregister_process(process_id)
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} unregistered")
    
    def _register_resource(self):
        """Register a resource for deadlock detection"""
        resource_id = self.resource_id_var.get()
        if resource_id:
            self.deadlock_detector.register_resource(resource_id)
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Resource {resource_id} registered")
    
    def _unregister_resource(self):
        """Unregister a resource from deadlock detection"""
        resource_id = self.resource_id_var.get()
        if resource_id:
            self.deadlock_detector.unregister_resource(resource_id)
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Resource {resource_id} unregistered")
    
    def _set_resource_owner(self):
        """Set a process as the owner of a resource"""
        process_id = self.owner_process_var.get()
        resource_id = self.owned_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.set_resource_owner(resource_id, process_id)
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Process {process_id} now owns resource {resource_id}"
            )
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} set as owner of resource {resource_id}")
    
    def _set_process_waiting(self):
        """Set a process as waiting for a resource"""
        process_id = self.waiting_process_var.get()
        resource_id = self.waited_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.add_waiting_process(resource_id, process_id)
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Process {process_id} now waiting for resource {resource_id}"
            )
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} set as waiting for resource {resource_id}")
    
    def _clear_process_waiting(self):
        """Clear a process from waiting for a resource"""
        process_id = self.waiting_process_var.get()
        resource_id = self.waited_resource_var.get()
        
        if process_id and resource_id:
            self.deadlock_detector.remove_waiting_process(resource_id, process_id)
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Process {process_id} no longer waiting for resource {resource_id}"
            )
            self._update_deadlock_ui()
            self.status_bar.config(text=f"Process {process_id} cleared from waiting for resource {resource_id}")
    
    def _detect_deadlocks(self):
        """Run deadlock detection algorithm"""
        deadlocks = self.deadlock_detector.detect_deadlocks()
        if deadlocks:
            self.deadlock_detector.add_log_entry(
                "deadlock_detector", 
                f"Detected {len(deadlocks)} deadlock cycle(s)"
            )
            self.status_bar.config(text=f"Detected {len(deadlocks)} deadlock cycle(s)")
        else:
            self.status_bar.config(text="No deadlocks detected")
            
        self._update_deadlock_ui()
    
    def _clear_deadlock_data(self):
        """Clear all deadlock detection data"""
        self.deadlock_detector.clear_all()
        self.deadlock_detector.add_log_entry("deadlock_detector", "All data cleared")
        self._update_deadlock_ui()
        self.status_bar.config(text="Deadlock detection data cleared")
    
    def _toggle_auto_analyze(self):
        """Toggle automatic deadlock analysis"""
        self.auto_analyze_active = self.auto_analyze_var.get()
        action = "enabled" if self.auto_analyze_active else "disabled"
        self.status_bar.config(text=f"Auto-analysis {action}")
    
    def _update_deadlock_ui(self):
        """Update the deadlock detection UI elements"""
        # Get current resources and processes
        resources = self.deadlock_detector.get_resource_status()
        processes = self.deadlock_detector.get_process_status()
        
        # Apply process filtering if active
        if self.filtered_processes is not None:
            # Filter processes based on filter criteria
            filtered_processes = {p_id: p_info for p_id, p_info in processes.items() 
                                if p_id in self.filtered_processes}
            processes = filtered_processes
        
        # Update dropdowns
        self.process_dropdown['values'] = list(processes.keys())
        self.resource_dropdown['values'] = list(resources.keys())
        
        # Check for deadlocks
        deadlocks = self.deadlock_detector.detect_deadlocks()
        
        # Run auto-analysis if enabled
        if self.auto_analyze_active and deadlocks:
            self._analyze_deadlocks()
        
        if deadlocks:
            self.deadlock_status.config(text=f"Deadlock detected: {len(deadlocks)} cycle(s)")
        else:
            self.deadlock_status.config(text="No deadlocks detected")
        
        # Update status text
        self.deadlock_status_text.config(state=tk.NORMAL)
        self.deadlock_status_text.delete(1.0, tk.END)
        
        status_text = "RESOURCES:\n"
        for r_id, r_info in resources.items():
            status_text += f"{r_id}: {r_info['state']} (Owner: {r_info['owner'] or 'None'}, " \
                          f"Waiters: {len(r_info['waiters'])})\n"
        
        status_text += "\nPROCESSES:\n"
        for p_id, p_info in processes.items():
            status_text += f"{p_id}: Owns {len(p_info['owns'])} resources, " \
                          f"Waiting for: {p_info['waiting_for'] or 'None'}\n"
        
        if deadlocks:
            status_text += "\nDEADLOCKS DETECTED:\n"
            for cycle in deadlocks:
                status_text += f"Deadlock cycle: {' -> '.join(cycle)}\n"
        
        self.deadlock_status_text.insert(tk.END, status_text)
        self.deadlock_status_text.config(state=tk.DISABLED)
        
        # Update visualization
        self.deadlock_canvas.delete("all")
        
        width = self.deadlock_canvas.winfo_width()
        height = self.deadlock_canvas.winfo_height()
        
        # Adjust the scrolling region based on graph size
        graph_width = max(1000, width * 2)
        graph_height = max(1000, height * 2)
        self.deadlock_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))
        
        # Avoid drawing if canvas size is not yet determined
        if width < 10 or height < 10:
            return
        
        # Calculate positions for resources and processes
        process_nodes = {}
        resource_nodes = {}
        self.process_node_ids = {}  # Store canvas IDs for processes
        self.resource_node_ids = {}  # Store canvas IDs for resources
        
        process_count = len(processes)
        resource_count = len(resources)
        
        if process_count == 0 or resource_count == 0:
            # Nothing to draw
            return
        
        # Create layout for larger graphs
        if process_count > 10 or resource_count > 10:
            # Use a circle layout for larger graphs
            center_x = graph_width / 2
            center_y = graph_height / 2
            process_radius = min(graph_width, graph_height) * 0.3
            resource_radius = min(graph_width, graph_height) * 0.6
            
            # Position processes in inner circle
            for i, p_id in enumerate(processes):
                angle = 2 * 3.14159 * i / process_count
                x = center_x + process_radius * math.cos(angle)
                y = center_y + process_radius * math.sin(angle)
                process_nodes[p_id] = (x, y)
            
            # Position resources in outer circle
            for i, r_id in enumerate(resources):
                angle = 2 * 3.14159 * i / resource_count
                x = center_x + resource_radius * math.cos(angle)
                y = center_y + resource_radius * math.sin(angle)
                resource_nodes[r_id] = (x, y)
        else:
            # Use the grid layout for smaller graphs
            # Arrange processes at the top
            process_spacing = width / (process_count + 1)
            for i, p_id in enumerate(processes):
                process_nodes[p_id] = (process_spacing * (i + 1), height * 0.25)
            
            # Arrange resources at the bottom
            resource_spacing = width / (resource_count + 1)
            for i, r_id in enumerate(resources):
                resource_nodes[r_id] = (resource_spacing * (i + 1), height * 0.75)
        
        # Draw nodes
        radius = 20
        
        # Find processes in deadlocks for highlighting
        deadlocked_processes = set()
        for cycle in deadlocks:
            deadlocked_processes.update(cycle)
        
        # Draw resource nodes (rectangles)
        for r_id, (x, y) in resource_nodes.items():
            resource = resources[r_id]
            
            # Color based on state
            if resource['state'] == 'owned':
                fill_color = "green"
            elif resource['state'] == 'free':
                fill_color = "lightgray"
            else:
                fill_color = "orange"
                
            # Highlight resources involved in deadlocks
            for cycle in deadlocks:
                for p_id in cycle:
                    if p_id in processes and processes[p_id]['waiting_for'] == r_id:
                        fill_color = "orange"
                        outline_width = 3
                        break
                else:
                    outline_width = 2
                    continue
                break
            else:
                outline_width = 2
            
            # Draw rectangle for resource
            rect_id = self.deadlock_canvas.create_rectangle(
                x-radius, y-radius, x+radius, y+radius,
                fill=fill_color, outline="black", width=outline_width,
                tags=(f"resource:{r_id}", "resource")
            )
            self.resource_node_ids[r_id] = rect_id
            
            text_id = self.deadlock_canvas.create_text(
                x, y, text=r_id, tags=(f"resource_label:{r_id}", "resource_label")
            )
            
            # Add tooltip and click behavior
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Enter>", 
                                         lambda e, rid=r_id: self._show_resource_tooltip(e, rid))
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Leave>", self._hide_tooltip)
            self.deadlock_canvas.tag_bind(f"resource:{r_id}", "<Button-1>", 
                                         lambda e, rid=r_id: self._select_resource(rid))
        
        # Draw process nodes (circles)
        for p_id, (x, y) in process_nodes.items():
            process = processes[p_id]
            
            # Color based on state
            if p_id in deadlocked_processes:
                fill_color = "red"
                outline_width = 3
            elif process['waiting_for'] is None:
                fill_color = "lightblue"
                outline_width = 2
            else:
                fill_color = "yellow"
                outline_width = 2
            
            # Draw circle for process
            circle_id = self.deadlock_canvas.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                fill=fill_color, outline="black", width=outline_width,
                tags=(f"process:{p_id}", "process")
            )
            self.process_node_ids[p_id] = circle_id
            
            text_id = self.deadlock_canvas.create_text(
                x, y, text=p_id, tags=(f"process_label:{p_id}", "process_label")
            )
            
            # Add tooltip and click behavior
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Enter>", 
                                         lambda e, pid=p_id: self._show_process_tooltip(e, pid))
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Leave>", self._hide_tooltip)
            self.deadlock_canvas.tag_bind(f"process:{p_id}", "<Button-1>", 
                                         lambda e, pid=p_id: self._select_process(pid))
        
        # Draw edges for ownership (process to resource)
        for p_id, p_info in processes.items():
            if p_id in process_nodes:
                px, py = process_nodes[p_id]
                
                # Draw edges for owned resources
                for r_id in p_info['owns']:
                    if r_id in resource_nodes:
                        rx, ry = resource_nodes[r_id]
                        line_id = self.deadlock_canvas.create_line(
                            px, py+radius, rx, ry-radius,
                            arrow=tk.LAST, width=2, fill="black",
                            tags=(f"owns_edge:{p_id}:{r_id}", "edge")
                        )
        
        # Draw edges for waiting processes (process to resource)
        for p_id, p_info in processes.items():
            if p_id in process_nodes and p_info['waiting_for']:
                px, py = process_nodes[p_id]
                r_id = p_info['waiting_for']
                
                if r_id in resource_nodes:
                    rx, ry = resource_nodes[r_id]
                    # Determine if this edge is part of a deadlock
                    is_deadlocked = p_id in deadlocked_processes
                    
                    # Dashed line for waiting relationship
                    line_id = self.deadlock_canvas.create_line(
                        px, py+radius, rx, ry-radius,
                        dash=(4, 4), arrow=tk.LAST, width=2,
                        fill="red" if is_deadlocked else "gray",
                        tags=(f"waits_edge:{p_id}:{r_id}", "edge")
                    )
        
        # Highlight deadlock cycles
        for i, cycle in enumerate(deadlocks):
            # Create a semi-transparent overlay to highlight the deadlock cycle
            cycle_nodes = []
            for p_id in cycle:
                if p_id in process_nodes:
                    cycle_nodes.append(process_nodes[p_id])
            
            if cycle_nodes:
                # Create highlight path around the cycle
                for j in range(len(cycle_nodes)):
                    x1, y1 = cycle_nodes[j]
                    x2, y2 = cycle_nodes[(j + 1) % len(cycle_nodes)]
                    
                    self.deadlock_canvas.create_line(
                        x1, y1, x2, y2,
                        width=3, fill="red", dash=(8, 4),
                        tags=(f"cycle:{i}", "cycle_highlight"),
                        state=tk.DISABLED  # This line is just for visualization
                    )
                
                # Add cycle label
                center_x = sum(x for x, y in cycle_nodes) / len(cycle_nodes)
                center_y = sum(y for x, y in cycle_nodes) / len(cycle_nodes)
                self.deadlock_canvas.create_text(
                    center_x, center_y - 40,
                    text=f"Deadlock #{i+1}",
                    font=("Arial", 10, "bold"), fill="red",
                    tags=(f"cycle_label:{i}", "cycle_label")
                )
    
    def _apply_process_filter(self):
        """Filter the processes shown in the deadlock visualization"""
        filter_text = self.process_filter_var.get()
        if filter_text:
            try:
                processes = self.deadlock_detector.get_process_status()
                self.filtered_processes = [p_id for p_id in processes if filter_text.lower() in p_id.lower()]
                self.status_bar.config(text=f"Filter applied: {len(self.filtered_processes)} processes shown")
                self._update_deadlock_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply filter: {str(e)}")
        else:
            self._clear_process_filter()
    
    def _clear_process_filter(self):
        """Clear the process filter"""
        self.process_filter_var.set("")
        self.filtered_processes = None
        self.status_bar.config(text="Process filter cleared")
        self._update_deadlock_ui()
    
    def _analyze_deadlocks(self):
        """Perform detailed analysis on detected deadlocks"""
        deadlocks = self.deadlock_detector.detect_deadlocks()
        resources = self.deadlock_detector.get_resource_status()
        processes = self.deadlock_detector.get_process_status()
        
        self.deadlock_suggestion_text.config(state=tk.NORMAL)
        self.deadlock_suggestion_text.delete(1.0, tk.END)
        
        if not deadlocks:
            self.deadlock_suggestion_text.insert(tk.END, "No deadlocks detected. System is operating normally.")
        else:
            # Create detailed analysis and suggestions
            suggestions = []
            for cycle_idx, cycle in enumerate(deadlocks):
                cycle_str = " → ".join(cycle)
                suggestions.append(f"Deadlock #{cycle_idx+1}: {cycle_str}\n")
                
                # Find the resources involved
                deadlocked_resources = []
                for p_id in cycle:
                    if p_id in processes and processes[p_id]['waiting_for']:
                        deadlocked_resources.append(processes[p_id]['waiting_for'])
                
                # Generate suggestions
                if deadlocked_resources:
                    suggestions.append("Potential resolutions:\n")
                    
                    # Suggestion 1: Release a resource
                    for i, p_id in enumerate(cycle):
                        if p_id in processes:
                            wait_res = processes[p_id]['waiting_for']
                            if wait_res:
                                owner = resources.get(wait_res, {}).get('owner')
                                if owner:
                                    suggestions.append(f"1. Release '{wait_res}' held by '{owner}'\n")
                                    break
                    
                    # Suggestion 2: Terminate a process
                    suggestions.append(f"2. Terminate one process in the cycle (e.g., '{cycle[0]}')\n")
                    
                    # Suggestion 3: Priority-based resource allocation
                    suggestions.append(f"3. Implement priority-based allocation for resources: {', '.join(deadlocked_resources)}\n")
            
            self.deadlock_suggestion_text.insert(tk.END, "".join(suggestions))
        
        self.deadlock_suggestion_text.config(state=tk.DISABLED)
    
    def _toggle_auto_analysis(self):
        """Toggle automatic deadlock analysis"""
        self.auto_analyze_active = self.auto_analyze_var.get()
        if self.auto_analyze_active:
            self.status_bar.config(text="Auto-analysis activated")
        else:
            self.status_bar.config(text="Auto-analysis deactivated")
    
    def _on_closing(self):
        """Handle application close"""
        # Stop all monitoring threads
        self.pipe_debugger.stop_monitoring()
        self.queue_debugger.stop_monitoring()
        self.shared_mem_debugger.stop_monitoring()
        self.deadlock_detector.stop_monitoring()
        
        # Close the application
        self.root.destroy()
    
    def _cleanup_resources(self):
        """Periodically clean up inactive resources"""
        try:
            # Clean up resources in each debugger
            pipes_removed = self.pipe_debugger.cleanup_inactive_pipes(timeout=300)  # 5 minutes
            queues_removed = self.queue_debugger.cleanup_inactive_queues(timeout=300)
            shm_removed = self.shared_mem_debugger.cleanup_inactive_memory(timeout=300)
            
            if pipes_removed > 0 or queues_removed > 0 or shm_removed > 0:
                self.status_bar.config(text=f"Cleaned up inactive resources: {pipes_removed} pipes, {queues_removed} queues, {shm_removed} shared memory segments")
            
            # Schedule next cleanup
            self.root.after(600000, self._cleanup_resources)  # Run every 10 minutes
        except Exception as e:
            # Log the error but don't crash
            print(f"Error during resource cleanup: {e}")
            # Ensure the cleanup continues on schedule despite errors
            self.root.after(600000, self._cleanup_resources) 

    def _zoom_in_deadlock(self):
        """Zoom in on the deadlock visualization"""
        self.deadlock_canvas_scale *= 1.1
        self.deadlock_canvas.scale("all", 0, 0, self.deadlock_canvas_scale, self.deadlock_canvas_scale)
    
    def _zoom_out_deadlock(self):
        """Zoom out on the deadlock visualization"""
        self.deadlock_canvas_scale /= 1.1
        self.deadlock_canvas.scale("all", 0, 0, self.deadlock_canvas_scale, self.deadlock_canvas_scale)
    
    def _reset_deadlock_view(self):
        """Reset the deadlock visualization"""
        self.deadlock_canvas_scale = 1.0
        self.deadlock_canvas.scale("all", 0, 0, self.deadlock_canvas_scale, self.deadlock_canvas_scale)
    
    def _deadlock_canvas_click(self, event):
        """Handle click on the deadlock visualization"""
        self.deadlock_canvas_drag_start = (event.x, event.y)
        self.deadlock_canvas_clicked_item = self.deadlock_canvas.find_closest(event.x, event.y)
    
    def _deadlock_canvas_drag(self, event):
        """Handle drag on the deadlock visualization"""
        if self.deadlock_canvas_drag_start:
            dx = event.x - self.deadlock_canvas_drag_start[0]
            dy = event.y - self.deadlock_canvas_drag_start[1]
            self.deadlock_canvas.move("all", dx, dy)
            self.deadlock_canvas_drag_start = (event.x, event.y)
    
    def _deadlock_canvas_zoom(self, event):
        """Handle zoom on the deadlock visualization"""
        if self.deadlock_canvas_clicked_item:
            dx = event.x - self.deadlock_canvas.canvasx(event.x)
            dy = event.y - self.deadlock_canvas.canvasy(event.y)
            self.deadlock_canvas_scale *= 1.1 if event.delta > 0 else 0.9
            self.deadlock_canvas.scale("all", self.deadlock_canvas.canvasx(event.x), self.deadlock_canvas.canvasy(event.y), self.deadlock_canvas_scale, self.deadlock_canvas_scale)
            self.deadlock_canvas.move("all", -dx, -dy)
            self.deadlock_canvas_clicked_item = None 
    
    def _show_process_tooltip(self, event, process_id):
        """Show tooltip for a process node"""
        processes = self.deadlock_detector.get_process_status()
        if process_id not in processes:
            return
        
        process = processes[process_id]
        owned_resources = ", ".join(process['owns']) if process['owns'] else "None"
        waiting_for = process['waiting_for'] if process['waiting_for'] else "None"
        
        tooltip_text = f"Process: {process_id}\nOwns: {owned_resources}\nWaiting for: {waiting_for}"
        
        self._show_tooltip(event, tooltip_text)
    
    def _show_resource_tooltip(self, event, resource_id):
        """Show tooltip for a resource node"""
        resources = self.deadlock_detector.get_resource_status()
        if resource_id not in resources:
            return
        
        resource = resources[resource_id]
        owner = resource['owner'] if resource['owner'] else "None"
        waiters = ", ".join(resource['waiters']) if resource['waiters'] else "None"
        
        tooltip_text = f"Resource: {resource_id}\nState: {resource['state']}\nOwner: {owner}\nWaiters: {waiters}"
        
        self._show_tooltip(event, tooltip_text)
    
    def _show_tooltip(self, event, text):
        """Display a tooltip at the cursor position"""
        x, y = event.x + 20, event.y + 10
        
        # Destroy any existing tooltip
        self._hide_tooltip()
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        
        # Position near the cursor
        self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        # Create label with tooltip text
        label = tk.Label(self.tooltip, text=text, justify=tk.LEFT,
                         background="#FFFFCC", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9))
        label.pack()
    
    def _hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def _select_process(self, process_id):
        """Handle selection of a process in the visualization"""
        # Update the process dropdown
        self.selected_process_var.set(process_id)
        
        # Highlight the selected process
        self._highlight_selected_node("process", process_id)
        
        # Show detailed information in the status bar
        processes = self.deadlock_detector.get_process_status()
        if process_id in processes:
            process = processes[process_id]
            owned_resources = ", ".join(process['owns']) if process['owns'] else "None"
            waiting_for = process['waiting_for'] if process['waiting_for'] else "None"
            self.status_bar.config(text=f"Selected process: {process_id} | Owns: {owned_resources} | Waiting for: {waiting_for}")
    
    def _select_resource(self, resource_id):
        """Handle selection of a resource in the visualization"""
        # Update the resource dropdown
        self.selected_resource_var.set(resource_id)
        
        # Highlight the selected resource
        self._highlight_selected_node("resource", resource_id)
        
        # Show detailed information in the status bar
        resources = self.deadlock_detector.get_resource_status()
        if resource_id in resources:
            resource = resources[resource_id]
            owner = resource['owner'] if resource['owner'] else "None"
            waiters = ", ".join(resource['waiters']) if resource['waiters'] else "None"
            self.status_bar.config(text=f"Selected resource: {resource_id} | State: {resource['state']} | Owner: {owner} | Waiters: {waiters}")
    
    def _highlight_selected_node(self, node_type, node_id):
        """Highlight the selected node and its relationships"""
        # Reset all highlights
        self.deadlock_canvas.itemconfig("process", width=2)
        self.deadlock_canvas.itemconfig("resource", width=2)
        self.deadlock_canvas.itemconfig("edge", width=2)
        
        if node_type == "process":
            # Highlight this process
            self.deadlock_canvas.itemconfig(f"process:{node_id}", width=4)
            
            # Highlight all owned resources and connecting edges
            processes = self.deadlock_detector.get_process_status()
            if node_id in processes:
                process = processes[node_id]
                
                # Highlight resources owned by this process
                for r_id in process['owns']:
                    self.deadlock_canvas.itemconfig(f"resource:{r_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"owns_edge:{node_id}:{r_id}", width=4)
                
                # Highlight resource this process is waiting for
                if process['waiting_for']:
                    r_id = process['waiting_for']
                    self.deadlock_canvas.itemconfig(f"resource:{r_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"waits_edge:{node_id}:{r_id}", width=4)
        
        elif node_type == "resource":
            # Highlight this resource
            self.deadlock_canvas.itemconfig(f"resource:{node_id}", width=4)
            
            # Highlight owner and waiting processes
            resources = self.deadlock_detector.get_resource_status()
            if node_id in resources:
                resource = resources[node_id]
                
                # Highlight owner
                if resource['owner']:
                    p_id = resource['owner']
                    self.deadlock_canvas.itemconfig(f"process:{p_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"owns_edge:{p_id}:{node_id}", width=4)
                
                # Highlight waiters
                for p_id in resource['waiters']:
                    self.deadlock_canvas.itemconfig(f"process:{p_id}", width=4)
                    self.deadlock_canvas.itemconfig(f"waits_edge:{p_id}:{node_id}", width=4)
    
    def simulate_ipc_activity(self):
        """Simulate various IPC activities for demonstration purposes"""
        # Create or update pipes
        for i in range(3):
            pipe_id = f"demo_pipe_{i}"
            status = random.choice(["idle", "transferring", "bottleneck"])
            progress = random.randint(0, 100) if status == "transferring" else 0
            
            self.pipe_debugger.register_pipe(pipe_id)
            self.pipe_debugger.update_pipe_status(
                pipe_id, 
                {
                    "status": status,
                    "writer_pid": f"process_{random.randint(1000, 9999)}",
                    "reader_pid": f"process_{random.randint(1000, 9999)}",
                    "bytes_transferred": random.randint(1000, 10000),
                    "progress": progress
                }
            )
            
            # Add to log
            if status != "idle":
                self.pipe_debugger.add_log_entry(
                    pipe_id, 
                    f"Data {'transfer in progress' if status == 'transferring' else 'bottleneck detected'}"
                )
        
        # Create or update queues
        for i in range(2):
            queue_id = f"demo_queue_{i}"
            capacity = 10
            message_count = random.randint(0, capacity)
            
            self.queue_debugger.register_queue(queue_id, capacity)
            self.queue_debugger.update_queue_status(
                queue_id,
                {
                    "status": "active" if message_count > 0 else "idle",
                    "message_count": message_count,
                    "capacity": capacity,
                    "producer_pid": f"process_{random.randint(1000, 9999)}",
                    "consumer_pid": f"process_{random.randint(1000, 9999)}"
                }
            )
            
            # Add to log
            if random.random() < 0.3:  # 30% chance to add a log entry
                action = random.choice(["enqueued", "dequeued"])
                self.queue_debugger.add_log_entry(
                    queue_id, 
                    f"Message {action} (queue size: {message_count}/{capacity})"
                )
        
        # Create or update shared memory
        for i in range(4):
            shm_id = f"demo_shm_{i}"
            
            self.shared_mem_debugger.register_memory_segment(shm_id, random.randint(1024, 10240))
            self.shared_mem_debugger.update_memory_status(
                shm_id,
                {
                    "status": random.choice(["active", "idle"]),
                    "size": random.randint(1024, 10240),
                    "access_count": random.randint(0, 100),
                    "last_writer": f"process_{random.randint(1000, 9999)}",
                    "locked_regions": [{"offset": 0, "size": 100}] if random.random() < 0.2 else []
                }
            )
            
            # Add to log
            if random.random() < 0.3:  # 30% chance to add a log entry
                action = random.choice(["write", "read", "lock", "unlock"])
                self.shared_mem_debugger.add_log_entry(
                    shm_id, 
                    f"Memory {action} operation at offset {random.randint(0, 1000)}"
                )
        
        # Create processes and resources for deadlock simulation
        for i in range(5):
            process_id = f"process_{random.randint(1000, 9999)}"
            self.deadlock_detector.register_process(process_id)
        
        # Register 8 resources
        for i in range(8):
            resource_id = f"resource_{i}"
            self.deadlock_detector.register_resource(resource_id)
        
        # Create a deadlock situation occasionally
        if random.random() < 0.3:  # 30% chance of deadlock
            # Create a simple deadlock cycle between 3 processes and 3 resources
            processes = list(self.deadlock_detector.get_process_status().keys())[:3]
            resources = list(self.deadlock_detector.get_resource_status().keys())[:3]
            
            if len(processes) >= 3 and len(resources) >= 3:
                # Process 0 owns Resource 0, waits for Resource 1
                # Process 1 owns Resource 1, waits for Resource 2
                # Process 2 owns Resource 2, waits for Resource 0
                for i in range(3):
                    self.deadlock_detector.set_resource_owner(resources[i], processes[i])
                    self.deadlock_detector.add_waiting_process(resources[(i+1)%3], processes[i])
                
                # Add to log
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Deadlock cycle detected involving processes {', '.join(processes)}"
                )
        
        # Create random resource ownership and waiting
        processes = list(self.deadlock_detector.get_process_status().keys())
        resources = list(self.deadlock_detector.get_resource_status().keys())
        
        for resource in resources[3:]:  # Use resources not involved in deadlock
            if random.random() < 0.7:  # 70% chance of assigning owner
                owner = random.choice(processes)
                self.deadlock_detector.set_resource_owner(resource, owner)
        
        for process in processes:
            if random.random() < 0.3:  # 30% chance of waiting
                resource = random.choice(resources)
                self.deadlock_detector.add_waiting_process(resource, process)
        
        # Schedule next simulation
        self.root.after(5000, self.simulate_ipc_activity)  # Run every 5 seconds
    
    # ------ UI Update Methods ------
    
    def _update_pipe_ui(self):
        """Update pipe UI elements"""
        # Get pipe status and update dropdown
        pipe_status = self.pipe_debugger.get_pipe_status()
        self.pipe_dropdown['values'] = list(pipe_status.keys())
        
        # Update status text
        self.pipe_status_text.config(state=tk.NORMAL)
        self.pipe_status_text.delete(1.0, tk.END)
        
        if not pipe_status:
            self.pipe_status_text.insert(tk.END, "No active pipes")
        else:
            status_text = "ACTIVE PIPES:\n\n"
            for pipe_id, pipe_info in pipe_status.items():
                status_text += f"Pipe ID: {pipe_id}\n"
                status_text += f"Status: {pipe_info.get('status', 'unknown')}\n"
                status_text += f"Writer PID: {pipe_info.get('writer_pid', 'None')}\n"
                status_text += f"Reader PID: {pipe_info.get('reader_pid', 'None')}\n"
                
                if pipe_info.get('status') == 'transferring':
                    status_text += f"Progress: {pipe_info.get('progress', 0)}%\n"
                    status_text += f"Bytes transferred: {pipe_info.get('bytes_transferred', 0)}\n"
                elif pipe_info.get('status') == 'bottleneck':
                    status_text += "WARNING: Bottleneck detected!\n"
                
                status_text += "\n"
            
            self.pipe_status_text.insert(tk.END, status_text)
        
        self.pipe_status_text.config(state=tk.DISABLED)
    
    def _update_queue_ui(self):
        """Update message queue UI elements"""
        # Get queue status and update dropdown
        queue_status = self.queue_debugger.get_queue_status()
        self.queue_dropdown['values'] = list(queue_status.keys())
        
        # Update status text
        self.queue_status_text.config(state=tk.NORMAL)
        self.queue_status_text.delete(1.0, tk.END)
        
        if not queue_status:
            self.queue_status_text.insert(tk.END, "No active message queues")
        else:
            status_text = "ACTIVE MESSAGE QUEUES:\n\n"
            for queue_id, queue_info in queue_status.items():
                status_text += f"Queue ID: {queue_id}\n"
                status_text += f"Status: {queue_info.get('status', 'unknown')}\n"
                status_text += f"Messages: {queue_info.get('message_count', 0)}/{queue_info.get('capacity', 'unknown')}\n"
                status_text += f"Producer PID: {queue_info.get('producer_pid', 'None')}\n"
                status_text += f"Consumer PID: {queue_info.get('consumer_pid', 'None')}\n"
                
                # Add warning for full queues
                if queue_info.get('message_count', 0) >= queue_info.get('capacity', 0):
                    status_text += "WARNING: Queue is full!\n"
                
                status_text += "\n"
            
            self.queue_status_text.insert(tk.END, status_text)
        
        self.queue_status_text.config(state=tk.DISABLED)
    
    def _update_shm_ui(self):
        """Update shared memory UI elements"""
        # Get memory status and update dropdown
        memory_status = self.shared_mem_debugger.get_memory_status()
        self.memory_dropdown['values'] = list(memory_status.keys())
        
        # Update status text
        self.shm_status_text.config(state=tk.NORMAL)
        self.shm_status_text.delete(1.0, tk.END)
        
        if not memory_status:
            self.shm_status_text.insert(tk.END, "No active shared memory segments")
        else:
            status_text = "ACTIVE SHARED MEMORY SEGMENTS:\n\n"
            for memory_id, memory_info in memory_status.items():
                status_text += f"Segment ID: {memory_id}\n"
                status_text += f"Status: {memory_info.get('status', 'unknown')}\n"
                status_text += f"Size: {memory_info.get('size', 0)} bytes\n"
                status_text += f"Access count: {memory_info.get('access_count', 0)}\n"
                status_text += f"Last writer: {memory_info.get('last_writer', 'None')}\n"
                
                # Add locked regions info
                locked_regions = memory_info.get('locked_regions', [])
                if locked_regions:
                    status_text += "Locked regions:\n"
                    for region in locked_regions:
                        status_text += f"  Offset {region.get('offset', 0)}, Size {region.get('size', 0)}"
                        status_text += f" (Owner: {region.get('owner', 'Unknown')})\n"
                
                status_text += "\n"
            
            self.shm_status_text.insert(tk.END, status_text)
        
        self.shm_status_text.config(state=tk.DISABLED)
    
    def _update_log_text(self):
        """Update the log text area with new events"""
        # Get log entries from all debuggers
        pipe_logs = []
        queue_logs = []
        shm_logs = []
        deadlock_logs = []
        
        # Collect logs based on visibility options
        if self.show_pipe_logs.get():
            pipe_logs = self.pipe_debugger.get_log_entries()
        
        if self.show_queue_logs.get():
            queue_logs = self.queue_debugger.get_log_entries()
        
        if self.show_shm_logs.get():
            shm_logs = self.shared_mem_debugger.get_log_entries()
        
        if self.show_deadlock_logs.get():
            deadlock_logs = self.deadlock_detector.get_log_entries()
        
        # Combine and sort logs by timestamp
        all_logs = pipe_logs + queue_logs + shm_logs + deadlock_logs
        all_logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Apply filter if one is set
        filtered_logs = all_logs
        if self.log_filter:
            filtered_logs = [log for log in all_logs 
                            if self.log_filter.lower() in log.get('message', '').lower() or 
                               self.log_filter.lower() in log.get('component_id', '').lower()]
        
        # Limit to latest 1000 entries to avoid performance issues
        filtered_logs = filtered_logs[:1000]
        
        # Update log text
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for log in filtered_logs:
            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0))
            time_str = timestamp.strftime('%H:%M:%S')
            
            # Color code based on component type
            component_id = log.get('component_id', '')
            
            if component_id.startswith('pipe'):
                tag = 'pipe_log'
                prefix = '[PIPE] '
            elif component_id.startswith('queue'):
                tag = 'queue_log'
                prefix = '[QUEUE] '
            elif component_id.startswith('shm'):
                tag = 'shm_log'
                prefix = '[SHM] '
            elif component_id.startswith('deadlock'):
                tag = 'deadlock_log'
                prefix = '[DEADLOCK] '
            else:
                tag = 'other_log'
                prefix = '[SYSTEM] '
            
            # Add log entry with tag
            log_entry = f"{time_str} {prefix}{component_id}: {log.get('message', '')}\n"
            self.log_text.insert(tk.END, log_entry, tag)
        
        # Configure tags colors
        self.log_text.tag_configure('pipe_log', foreground='blue')
        self.log_text.tag_configure('queue_log', foreground='green')
        self.log_text.tag_configure('shm_log', foreground='purple')
        self.log_text.tag_configure('deadlock_log', foreground='red')
        self.log_text.tag_configure('other_log', foreground='black')
        
        self.log_text.config(state=tk.DISABLED)
    
    def _update_overview_canvas(self):
        """Update the overview canvas with all IPC activities"""
        # Clear canvas
        self.overview_canvas.delete("all")
        
        # Get dimensions
        width = self.overview_canvas.winfo_width()
        height = self.overview_canvas.winfo_height()
        
        # Skip drawing if canvas size is not determined yet
        if width < 10 or height < 10:
            self.root.after(100, self._update_overview_canvas)
            return
        
        # Draw background grid
        for i in range(0, width, 50):
            self.overview_canvas.create_line(i, 0, i, height, fill="#EEEEEE")
        for i in range(0, height, 50):
            self.overview_canvas.create_line(0, i, width, i, fill="#EEEEEE")
        
        # Get data from all debuggers
        pipes = self.pipe_debugger.get_pipe_status()
        queues = self.queue_debugger.get_queue_status()
        memory_segments = self.shared_mem_debugger.get_memory_status()
        processes = self.deadlock_detector.get_process_status()
        resources = self.deadlock_detector.get_resource_status()
        
        # Calculate metrics
        active_pipes = len(pipes)
        active_queues = len(queues)
        active_memory = len(memory_segments)
        active_processes = len(processes)
        
        total_queue_messages = sum(q.get('message_count', 0) for q in queues.values())
        total_memory_access = sum(m.get('access_count', 0) for m in memory_segments.values())
        
        # Update metric labels
        self.pipe_count.config(text=f"Active: {active_pipes}")
        self.queue_count.config(text=f"Active: {active_queues}")
        self.queue_messages.config(text=f"Messages: {total_queue_messages}")
        self.shm_count.config(text=f"Active: {active_memory}")
        self.shm_access.config(text=f"Accesses: {total_memory_access}")
        
        self.process_count.config(text=f"Processes: {active_processes}")
        self.resource_count.config(text=f"Resources: {len(resources)}")
        self.deadlock_count.config(text=f"Deadlocks: {len(self.deadlock_detector.detect_deadlocks())}")
        
        # Mock system metrics (in a real system these would come from actual measurements)
        cpu_usage = random.randint(10, 80)
        memory_usage = random.randint(100, 2000)
        ipc_ops = active_pipes + active_queues + active_memory
        
        self.cpu_usage.config(text=f"{cpu_usage}%")
        self.memory_usage.config(text=f"{memory_usage} MB")
        self.ipc_throughput.config(text=f"{ipc_ops} ops/sec")
        self.active_process_count.config(text=f"{active_processes}")
        
        # Draw system components
        # Draw processes at the top
        process_y = height * 0.2
        process_spacing = width / (active_processes + 1) if active_processes > 0 else width / 2
        process_positions = {}
        
        for i, (process_id, process) in enumerate(processes.items()):
            x = process_spacing * (i + 1)
            process_positions[process_id] = (x, process_y)
            
            # Color based on state (deadlocked processes are red)
            deadlocks = self.deadlock_detector.detect_deadlocks()
            is_deadlocked = any(process_id in cycle for cycle in deadlocks)
            color = "red" if is_deadlocked else ("yellow" if process.get('waiting_for') else "lightblue")
            
            # Draw process as circle
            self.overview_canvas.create_oval(x-15, process_y-15, x+15, process_y+15, 
                                           fill=color, outline="black")
            self.overview_canvas.create_text(x, process_y, text=f"P{i+1}")
        
        # Draw resources in the middle
        resource_y = height * 0.5
        resource_spacing = width / (len(resources) + 1) if resources else width / 2
        resource_positions = {}
        
        for i, (resource_id, resource) in enumerate(resources.items()):
            x = resource_spacing * (i + 1)
            resource_positions[resource_id] = (x, resource_y)
            
            # Color based on state
            if resource.get('state') == 'owned':
                color = "green"
            elif resource.get('state') == 'free':
                color = "lightgray"
            else:
                color = "orange"
            
            # Draw resource as rectangle
            self.overview_canvas.create_rectangle(x-15, resource_y-15, x+15, resource_y+15, 
                                                fill=color, outline="black")
            self.overview_canvas.create_text(x, resource_y, text=f"R{i+1}")
        
        # Draw pipes on the left
        pipe_x = width * 0.25
        pipe_y_start = height * 0.7
        pipe_spacing = height * 0.2 / (active_pipes + 1) if active_pipes > 0 else height * 0.1
        
        for i, (pipe_id, pipe) in enumerate(pipes.items()):
            y = pipe_y_start + pipe_spacing * (i + 1)
            
            # Draw pipe
            self.overview_canvas.create_rectangle(pipe_x-50, y-8, pipe_x+50, y+8, 
                                                fill="lightblue", outline="black")
            
            # Draw status indicator
            status = pipe.get('status', 'idle')
            if status == 'idle':
                status_color = "gray"
            elif status == 'transferring':
                status_color = "green"
            else:  # bottleneck
                status_color = "red"
            
            self.overview_canvas.create_oval(pipe_x+60, y-8, pipe_x+76, y+8, 
                                           fill=status_color, outline="black")
        
        # Draw queues in the middle
        queue_x = width * 0.5
        queue_y_start = height * 0.7
        queue_spacing = height * 0.2 / (active_queues + 1) if active_queues > 0 else height * 0.1
        
        for i, (queue_id, queue) in enumerate(queues.items()):
            y = queue_y_start + queue_spacing * (i + 1)
            
            # Calculate fill level
            capacity = queue.get('capacity', 10)
            message_count = queue.get('message_count', 0)
            fill_ratio = message_count / capacity if capacity > 0 else 0
            
            # Draw queue
            queue_width = 70
            fill_width = queue_width * fill_ratio
            
            self.overview_canvas.create_rectangle(queue_x-35, y-15, queue_x+35, y+15, 
                                                fill="white", outline="black")
            
            if fill_width > 0:
                self.overview_canvas.create_rectangle(queue_x-35, y-15, queue_x-35+fill_width, y+15, 
                                                    fill="green", outline="")
            
            self.overview_canvas.create_text(queue_x, y, text=f"{message_count}/{capacity}")
        
        # Draw shared memory segments on the right
        shm_x = width * 0.75
        shm_y_start = height * 0.7
        shm_spacing = height * 0.2 / (active_memory + 1) if active_memory > 0 else height * 0.1
        
        for i, (memory_id, memory) in enumerate(memory_segments.items()):
            y = shm_y_start + shm_spacing * (i + 1)
            
            # Draw memory segment
            self.overview_canvas.create_rectangle(shm_x-40, y-20, shm_x+40, y+20, 
                                                fill="lightyellow", outline="black")
            
            # Draw locked regions if any
            locked_regions = memory.get('locked_regions', [])
            if locked_regions:
                self.overview_canvas.create_rectangle(shm_x-30, y-10, shm_x-10, y+10, 
                                                    fill="red", outline="black")
                self.overview_canvas.create_text(shm_x, y, text=f"Locked: {len(locked_regions)}")
            else:
                self.overview_canvas.create_text(shm_x, y, text="Unlocked")
        
        # Draw relationships between processes and resources
        for process_id, process in processes.items():
            if process_id in process_positions:
                px, py = process_positions[process_id]
                
                # Draw owned resources
                for resource_id in process.get('owns', []):
                    if resource_id in resource_positions:
                        rx, ry = resource_positions[resource_id]
                        self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                       arrow=tk.LAST, fill="black")
                
                # Draw waiting relationships
                waiting_for = process.get('waiting_for')
                if waiting_for and waiting_for in resource_positions:
                    rx, ry = resource_positions[waiting_for]
                    self.overview_canvas.create_line(px, py+15, rx, ry-15, 
                                                   arrow=tk.LAST, fill="red", dash=(4, 4))
    
    def _apply_log_filter(self):
        """Apply a filter to the log text"""
        filter_text = self.log_filter_var.get()
        if filter_text:
            self.log_filter = filter_text
            self._update_log_text()
            self.status_bar.config(text=f"Log filter applied: '{filter_text}'")
        else:
            self._clear_log_filter()
    
    def _clear_log_filter(self):
        """Clear the current log filter"""
        self.log_filter_var.set("")
        self.log_filter = None
        self._update_log_text()
        self.status_bar.config(text="Log filter cleared")

    def _refresh_ui(self):
        """Refresh all UI elements"""
        self._update_pipe_ui()
        self._update_queue_ui()
        self._update_shm_ui()
        self._update_deadlock_ui()
        self._update_log_text()
        self._update_overview_canvas()
        
        # Schedule next refresh
        self.root.after(self.refresh_rate, self._refresh_ui)

    def _request_resource(self):
        """Request a resource for a process (set process as waiting for a resource)"""
        process_id = self.selected_process_var.get()
        resource_id = self.selected_resource_var.get()
        
        if process_id and resource_id:
            # Check if this resource is already owned
            resource_status = self.deadlock_detector.get_resource_status().get(resource_id, {})
            owner = resource_status.get('owner')
            
            if owner:
                # Resource is owned, add process to waiters
                self.deadlock_detector.add_waiting_process(resource_id, process_id)
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Process {process_id} waiting for resource {resource_id} (owned by {owner})"
                )
                self.status_bar.config(text=f"Process {process_id} is now waiting for resource {resource_id}")
            else:
                # Resource is free, assign it to the process
                self.deadlock_detector.set_resource_owner(resource_id, process_id)
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Process {process_id} acquired resource {resource_id}"
                )
                self.status_bar.config(text=f"Process {process_id} acquired resource {resource_id}")
            
            # Update UI
            self._update_deadlock_ui()
    
    def _release_resource(self):
        """Release a resource from a process"""
        process_id = self.selected_process_var.get()
        resource_id = self.selected_resource_var.get()
        
        if process_id and resource_id:
            # Check if this process owns the resource
            resource_status = self.deadlock_detector.get_resource_status().get(resource_id, {})
            if resource_status.get('owner') == process_id:
                # Release the resource
                self.deadlock_detector.release_resource(resource_id)
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Process {process_id} released resource {resource_id}"
                )
                self.status_bar.config(text=f"Resource {resource_id} released by process {process_id}")
                
                # Check if there are waiters
                waiters = resource_status.get('waiters', [])
                if waiters:
                    # Assign to first waiter
                    new_owner = waiters[0]
                    self.deadlock_detector.remove_waiting_process(resource_id, new_owner)
                    self.deadlock_detector.set_resource_owner(resource_id, new_owner)
                    self.deadlock_detector.add_log_entry(
                        "deadlock_detector", 
                        f"Resource {resource_id} assigned to waiting process {new_owner}"
                    )
            else:
                self.status_bar.config(text=f"Process {process_id} doesn't own resource {resource_id}")
            
            # Update UI
            self._update_deadlock_ui()
    
    def _simulate_deadlock(self):
        """Simulate a deadlock scenario"""
        try:
            # Get number of processes and resources to create
            num_processes = int(self.sim_processes_var.get() or "3")
            num_resources = int(self.sim_resources_var.get() or "3")
            
            # Clear existing data
            self.deadlock_detector.clear_all()
            
            # Create processes
            processes = [f"p{i+1}" for i in range(num_processes)]
            for p_id in processes:
                self.deadlock_detector.register_process(p_id)
            
            # Create resources
            resources = [f"r{i+1}" for i in range(num_resources)]
            for r_id in resources:
                self.deadlock_detector.register_resource(r_id)
            
            # Create deadlock if we have at least 2 processes and 2 resources
            if num_processes >= 2 and num_resources >= 2:
                # Simple deadlock: circular wait
                for i in range(num_processes):
                    # Each process owns one resource
                    self.deadlock_detector.set_resource_owner(resources[i % num_resources], processes[i])
                    
                    # Each process waits for the next resource (circular)
                    next_resource = resources[(i + 1) % num_resources]
                    self.deadlock_detector.add_waiting_process(next_resource, processes[i])
                
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Simulated deadlock with {num_processes} processes and {num_resources} resources"
                )
                self.status_bar.config(text=f"Deadlock simulation created with {num_processes} processes and {num_resources} resources")
            else:
                # Just assign resources without deadlock
                for i in range(min(num_processes, num_resources)):
                    self.deadlock_detector.set_resource_owner(resources[i], processes[i])
                
                self.deadlock_detector.add_log_entry(
                    "deadlock_detector", 
                    f"Created {num_processes} processes and {num_resources} resources without deadlock"
                )
                self.status_bar.config(text="Resources assigned without creating deadlock")
            
            # Update UI
            self._update_deadlock_ui()
            self._analyze_deadlocks()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for processes and resources")
            return
    
    def _on_shm_selected(self, event=None):
        """Handle selection of a shared memory segment from dropdown"""
        selected_memory = self.op_memory_id_var.get()
        if selected_memory:
            # Update memory information in status bar
            memory_status = self.shared_mem_debugger.get_memory_status().get(selected_memory, {})
            size = memory_status.get("size", 0)
            access_count = memory_status.get("access_count", 0)
            self.status_bar.config(text=f"Selected memory: {selected_memory} | Size: {size} bytes | Accesses: {access_count}")
    
    def _write_to_memory(self):
        """Simulate writing to shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        data = self.shm_data_entry.get() or "Test data"
        size = len(data)
        
        if memory_id:
            self._write_shared_memory()
            self.status_bar.config(text=f"Data written to shared memory {memory_id} at offset {offset}")
    
    def _read_from_memory(self):
        """Simulate reading from shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        offset = int(self.memory_offset_var.get() or "0")
        size = int(self.memory_op_size_var.get() or "128")
        
        if memory_id:
            self._read_shared_memory()
            # In a real system, we would display the read data
            messagebox.showinfo("Memory Read", f"Read {size} bytes from {memory_id} at offset {offset}")
            self.status_bar.config(text=f"Data read from shared memory {memory_id} at offset {offset}")
    
    def _close_shared_memory(self):
        """Delete the selected shared memory segment"""
        memory_id = self.op_memory_id_var.get()
        if memory_id:
            self.shared_mem_debugger.unregister_memory_segment(memory_id)
            self._update_shm_ui()
            self.status_bar.config(text=f"Shared memory segment {memory_id} closed")
    
    def _lock_region(self):
        """Lock a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        start = int(self.lock_start_var.get() or "0")
        end = int(self.lock_end_var.get() or "100")
        size = end - start
        
        if memory_id and size > 0:
            self._lock_shared_memory()
            self.status_bar.config(text=f"Region locked in shared memory {memory_id} from {start} to {end}")
    
    def _unlock_region(self):
        """Unlock a region of shared memory"""
        memory_id = self.op_memory_id_var.get()
        process_id = self.memory_process_id_var.get() or f"proc_{random.randint(1000, 9999)}"
        start = int(self.lock_start_var.get() or "0")
        end = int(self.lock_end_var.get() or "100")
        size = end - start
        
        if memory_id and size > 0:
            self._unlock_shared_memory()
            self.status_bar.config(text=f"Region unlocked in shared memory {memory_id} from {start} to {end}")
    
    def _simulate_race_condition(self):
        """Simulate a race condition in shared memory access"""
        memory_id = self.op_memory_id_var.get()
        
        if memory_id:
            # Create two processes that will access the same memory region
            process1 = f"proc_{random.randint(1000, 9999)}"
            process2 = f"proc_{random.randint(1000, 9999)}"
            
            offset = int(self.memory_offset_var.get() or "0")
            
            memory_status = self.shared_mem_debugger.get_memory_status().get(memory_id, {}).copy()
            
            # Log the simulation start
            self.shared_mem_debugger.add_log_entry(
                memory_id, 
                f"Race condition simulation started: {process1} and {process2} accessing same region"
            )
            
            # Simulate concurrent access - first process writes
            self.memory_process_id_var.set(process1)
            self._write_shared_memory()
            
            # Second process writes to the same location without synchronization
            self.memory_process_id_var.set(process2)
            self._write_shared_memory()
            
            # Update status to indicate race condition
            memory_status["status"] = "race_condition"
            self.shared_mem_debugger.update_memory_status(memory_id, memory_status)
            
            # Log the race condition
            self.shared_mem_debugger.add_log_entry(
                memory_id, 
                f"Race condition detected between {process1} and {process2} at offset {offset}"
            )
            
            self._update_shm_ui()
            self.status_bar.config(text=f"Race condition simulated on shared memory {memory_id}")
            
            # Reset process ID
            self.memory_process_id_var.set("")