"""
Pipe debugging functionality for IPC Debugger.
"""

import os
import time
import tempfile
import threading
from multiprocessing import Process, Pipe
from queue import Queue, Full as QueueFull

class PipeDebugger:
    def __init__(self):
        self.active_pipes = {}
        self.transfer_log = []
        self.log_queue = Queue(maxsize=1000)  # Limit to 1000 log entries
        self._running = False
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start monitoring pipe communications"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_pipes)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring pipe communications"""
        if not self._running:
            return  # Already stopped
            
        self._running = False
        
        if hasattr(self, '_monitor_thread'):
            try:
                # Give thread time to terminate gracefully
                self._monitor_thread.join(2.0)
                
                # Log if thread didn't terminate
                if self._monitor_thread.is_alive():
                    self._log_event({
                        'time': time.time(),
                        'action': 'warning',
                        'message': 'Monitor thread did not terminate cleanly'
                    })
            except Exception as e:
                # Log any errors during thread termination
                self._log_event({
                    'time': time.time(),
                    'action': 'error',
                    'message': f'Error terminating monitor thread: {str(e)}'
                })
    
    def _log_event(self, event):
        """Add an event to the log queue, dropping oldest if full"""
        try:
            self.log_queue.put_nowait(event)
        except QueueFull:
            # Queue is full, remove oldest entry and add new one
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(event)
            except:
                # If any error occurs, just ignore this log entry
                pass
    
    def _monitor_pipes(self):
        """Monitor active pipes and log activities"""
        while self._running:
            time.sleep(0.1)
            
            # Take a snapshot of pipe states under the lock
            pipes_to_update = {}
            with self._lock:
                for pipe_id, pipe_info in self.active_pipes.items():
                    if pipe_info['status'] == 'transferring':
                        # Make a copy of the relevant information
                        pipes_to_update[pipe_id] = {
                            'current_progress': pipe_info['progress'],
                            'data_size': pipe_info['data_size']
                        }
            
            # Process pipe updates outside the lock
            updates_to_apply = {}
            for pipe_id, info in pipes_to_update.items():
                current_progress = info['current_progress']
                data_size = info['data_size']
                
                new_progress = min(100, current_progress + 10)
                
                # Check if transfer is complete
                if new_progress >= 100:
                    updates_to_apply[pipe_id] = {
                        'progress': new_progress,
                        'status': 'completed',
                        'should_log': True
                    }
                else:
                    updates_to_apply[pipe_id] = {
                        'progress': new_progress,
                        'should_log': False
                    }
            
            # Apply updates under the lock
            if updates_to_apply:
                with self._lock:
                    for pipe_id, update in updates_to_apply.items():
                        if pipe_id in self.active_pipes:
                            pipe_info = self.active_pipes[pipe_id]
                            pipe_info['progress'] = update['progress']
                            
                            if 'status' in update:
                                pipe_info['status'] = update['status']
                            
                            # Log if transfer is complete
                            if update.get('should_log', False):
                                self._log_event({
                                    'time': time.time(),
                                    'pipe_id': pipe_id,
                                    'action': 'transfer_completed',
                                    'data_size': pipe_info['data_size']
                                })
    
    def create_pipe_pair(self):
        """Create a new pipe and return its ID"""
        pipe_id = f"pipe_{len(self.active_pipes) + 1}"
        
        with self._lock:
            # Create the pipe
            reader, writer = Pipe(duplex=False)  # One-way pipe for simplicity
            
            # Store pipe info
            self.active_pipes[pipe_id] = {
                'reader': reader,
                'writer': writer,
                'create_time': time.time(),
                'last_activity': time.time(),
                'status': 'idle',
                'reader_pid': None,
                'writer_pid': None,
                'bytes_transferred': 0,
                'progress': 0
            }
            
            # Log the creation
            self._log_event({
                'time': time.time(),
                'action': 'create',
                'pipe_id': pipe_id,
                'message': f"Created pipe {pipe_id}"
            })
            
        return pipe_id
    
    def register_pipe(self, pipe_id=None):
        """Register a pipe for monitoring (or create a new one if pipe_id is None)"""
        if pipe_id is None:
            return self.create_pipe_pair()
            
        # If pipe_id is provided, check if it already exists
        if pipe_id in self.active_pipes:
            return pipe_id
            
        # Register a new pipe with the given ID
        with self._lock:
            # Create the pipe
            reader, writer = Pipe(duplex=False)  # One-way pipe for simplicity
            
            # Store pipe info
            self.active_pipes[pipe_id] = {
                'reader': reader,
                'writer': writer,
                'create_time': time.time(),
                'last_activity': time.time(),
                'status': 'idle',
                'reader_pid': None,
                'writer_pid': None,
                'bytes_transferred': 0,
                'progress': 0
            }
            
            # Log the creation
            self._log_event({
                'time': time.time(),
                'action': 'create',
                'pipe_id': pipe_id,
                'message': f"Registered pipe {pipe_id}"
            })
            
        return pipe_id
    
    def send_data(self, pipe_id, data):
        """Send data through a pipe"""
        if pipe_id not in self.active_pipes:
            raise ValueError(f"Pipe {pipe_id} not found")
        
        pipe_info = self.active_pipes[pipe_id]
        data_size = len(str(data))
        
        with self._lock:
            pipe_info['status'] = 'transferring'
            pipe_info['progress'] = 0
            pipe_info['data_size'] = data_size
            pipe_info['last_activity_time'] = time.time()
            
            self._log_event({
                'time': time.time(),
                'pipe_id': pipe_id,
                'action': 'transfer_started',
                'data_size': data_size
            })
        
        # Actual send in a separate thread to not block
        def _send():
            try:
                pipe_info['reader'].send(data)
            except Exception as e:
                with self._lock:
                    pipe_info['status'] = 'error'
                    self._log_event({
                        'time': time.time(),
                        'pipe_id': pipe_id,
                        'action': 'transfer_error',
                        'error': str(e)
                    })
        
        threading.Thread(target=_send).start()
        return True
    
    def receive_data(self, pipe_id):
        """Receive data from a pipe"""
        if pipe_id not in self.active_pipes:
            raise ValueError(f"Pipe {pipe_id} not found")
        
        pipe_info = self.active_pipes[pipe_id]
        
        # Update last activity time
        with self._lock:
            pipe_info['last_activity_time'] = time.time()
        
        # Non-blocking check if data is available
        if pipe_info['writer'].poll():
            try:
                data = pipe_info['writer'].recv()
                
                with self._lock:
                    self._log_event({
                        'time': time.time(),
                        'pipe_id': pipe_id,
                        'action': 'data_received',
                        'data_size': len(str(data))
                    })
                
                return data
            except Exception as e:
                with self._lock:
                    pipe_info['status'] = 'error'
                    self._log_event({
                        'time': time.time(),
                        'pipe_id': pipe_id,
                        'action': 'receive_error',
                        'error': str(e)
                    })
                return None
        return None
    
    def close_pipe(self, pipe_id):
        """Close a pipe and clean up resources"""
        if pipe_id not in self.active_pipes:
            raise ValueError(f"Pipe {pipe_id} not found")
        
        with self._lock:
            pipe_info = self.active_pipes[pipe_id]
            pipe_info['reader'].close()
            pipe_info['writer'].close()
            pipe_info['status'] = 'closed'
            
            self._log_event({
                'time': time.time(),
                'pipe_id': pipe_id,
                'action': 'pipe_closed'
            })
    
    def unregister_pipe(self, pipe_id):
        """Completely remove a pipe from tracking"""
        if pipe_id not in self.active_pipes:
            return False
        
        # First close the pipe if it's not already closed
        with self._lock:
            pipe_info = self.active_pipes[pipe_id]
            if pipe_info['status'] != 'closed':
                try:
                    pipe_info['reader'].close()
                except:
                    pass
                
                try:
                    pipe_info['writer'].close()
                except:
                    pass
            
            # Remove from active pipes
            del self.active_pipes[pipe_id]
            
            self._log_event({
                'time': time.time(),
                'pipe_id': pipe_id,
                'action': 'pipe_unregistered'
            })
            
            return True
    
    def cleanup_inactive_pipes(self, timeout=600):
        """Clean up pipes that have been inactive for the specified timeout (in seconds)"""
        current_time = time.time()
        pipes_to_remove = []
        
        with self._lock:
            for pipe_id, pipe_info in self.active_pipes.items():
                # Check if the pipe is closed or has been inactive
                if pipe_info['status'] == 'closed' or \
                   (pipe_info['status'] == 'idle' and 
                    current_time - pipe_info.get('last_activity_time', pipe_info['create_time']) > timeout):
                    pipes_to_remove.append(pipe_id)
        
        # Remove the pipes outside the lock
        for pipe_id in pipes_to_remove:
            self.unregister_pipe(pipe_id)
            
        return len(pipes_to_remove)
    
    def get_pipe_status(self, pipe_id=None):
        """Get status of all pipes or a specific pipe"""
        with self._lock:
            if pipe_id is not None:
                return {pipe_id: self.active_pipes.get(pipe_id, {})}
            return self.active_pipes.copy()
    
    def update_pipe_status(self, pipe_id, status_update):
        """Update status information for a pipe"""
        if pipe_id not in self.active_pipes:
            raise ValueError(f"Pipe {pipe_id} not found")
            
        with self._lock:
            # Update the pipe status
            for key, value in status_update.items():
                self.active_pipes[pipe_id][key] = value
                
            # Update last activity time
            self.active_pipes[pipe_id]['last_activity'] = time.time()
            
            # Log the update
            self._log_event({
                'time': time.time(),
                'action': 'update',
                'pipe_id': pipe_id,
                'message': f"Updated pipe {pipe_id} status: {', '.join([f'{k}={v}' for k, v in status_update.items()])}"
            })
            
        return True
    
    def add_log_entry(self, pipe_id, message):
        """Add a custom log entry for a pipe"""
        self._log_event({
            'time': time.time(),
            'action': 'info',
            'pipe_id': pipe_id,
            'message': message
        })
    
    def get_logs(self):
        """Get all log entries"""
        return list(self.transfer_log)
    
    def get_log_entries(self):
        """Get formatted log entries for UI display"""
        logs = []
        for entry in self.transfer_log:
            logs.append({
                'timestamp': entry.get('time', 0),
                'component_id': f"pipe_{entry.get('pipe_id', 'unknown')}",
                'message': entry.get('message', entry.get('action', 'unknown action'))
            })
        return logs
    
    def simulate_pipe_bottleneck(self, pipe_id, duration=5):
        """Simulate a bottleneck in pipe communication"""
        if pipe_id not in self.active_pipes:
            raise ValueError(f"Pipe {pipe_id} not found")
        
        pipe_info = self.active_pipes[pipe_id]
        
        with self._lock:
            pipe_info['status'] = 'bottleneck'
            self._log_event({
                'time': time.time(),
                'pipe_id': pipe_id,
                'action': 'bottleneck_started',
                'duration': duration
            })
        
        # Simulate bottleneck in a separate thread
        def _bottleneck():
            time.sleep(duration)
            with self._lock:
                if pipe_id in self.active_pipes and pipe_info['status'] == 'bottleneck':
                    pipe_info['status'] = 'idle'
                    self._log_event({
                        'time': time.time(),
                        'pipe_id': pipe_id,
                        'action': 'bottleneck_resolved'
                    })
        
        threading.Thread(target=_bottleneck).start()
        return True 