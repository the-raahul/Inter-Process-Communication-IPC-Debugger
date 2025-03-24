"""
Message queue debugging functionality for IPC Debugger.
"""

import time
import threading
from multiprocessing import Queue as MPQueue
from queue import Queue, Full as QueueFull
import random

class QueueDebugger:
    def __init__(self):
        self.active_queues = {}
        self.log_queue = Queue(maxsize=1000)  # Limit to 1000 log entries
        self._running = False
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start monitoring message queues"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_queues)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring message queues"""
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
    
    def _monitor_queues(self):
        """Monitor active queues and log activities"""
        while self._running:
            time.sleep(0.1)
            
            # Take a snapshot of queue states under the lock
            queues_to_check = {}
            with self._lock:
                for queue_id, queue_info in self.active_queues.items():
                    # Copy only the necessary data
                    queues_to_check[queue_id] = {
                        'message_count': queue_info['message_count'],
                        'capacity': queue_info['capacity']
                    }
            
            # Process queue data outside the lock
            alerts_to_log = []
            for queue_id, info in queues_to_check.items():
                # Check for potential issues
                if info['message_count'] > info['capacity'] * 0.8:
                    alerts_to_log.append({
                        'queue_id': queue_id,
                        'fill_percent': (info['message_count'] / info['capacity']) * 100
                    })
            
            # Log alerts under the lock
            if alerts_to_log:
                with self._lock:
                    for alert in alerts_to_log:
                        self._log_event({
                            'time': time.time(),
                            'queue_id': alert['queue_id'],
                            'action': 'queue_nearly_full',
                            'fill_percent': alert['fill_percent']
                        })
    
    def create_queue(self, capacity=100):
        """Create a new message queue and return its ID"""
        queue_id = f"queue_{len(self.active_queues) + 1}"
        
        with self._lock:
            # Create queue
            queue = MPQueue(maxsize=capacity)
            
            # Store queue info
            self.active_queues[queue_id] = {
                'queue': queue,
                'create_time': time.time(),
                'last_activity': time.time(),
                'status': 'idle',
                'producer_pid': None,
                'consumer_pid': None,
                'capacity': capacity,
                'message_count': 0,
                'enqueue_count': 0,
                'dequeue_count': 0
            }
            
            # Log the creation
            self._log_event({
                'time': time.time(),
                'action': 'create',
                'queue_id': queue_id,
                'message': f"Created queue {queue_id} with capacity {capacity}"
            })
            
        return queue_id
    
    def register_queue(self, queue_id=None, capacity=100):
        """Register a queue for monitoring (or create a new one if queue_id is None)"""
        if queue_id is None:
            return self.create_queue(capacity)
            
        # If queue_id is provided, check if it already exists
        if queue_id in self.active_queues:
            return queue_id
            
        # Register a new queue with the given ID
        with self._lock:
            # Create queue
            queue = MPQueue(maxsize=capacity)
            
            # Store queue info
            self.active_queues[queue_id] = {
                'queue': queue,
                'create_time': time.time(),
                'last_activity': time.time(),
                'status': 'idle',
                'producer_pid': None,
                'consumer_pid': None,
                'capacity': capacity,
                'message_count': 0,
                'enqueue_count': 0,
                'dequeue_count': 0
            }
            
            # Log the creation
            self._log_event({
                'time': time.time(),
                'action': 'create',
                'queue_id': queue_id,
                'message': f"Registered queue {queue_id} with capacity {capacity}"
            })
            
        return queue_id
    
    def enqueue_message(self, queue_id, message):
        """Add a message to a queue"""
        if queue_id not in self.active_queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue_info = self.active_queues[queue_id]
        
        # Check if queue is full (for demonstration only - real MP.Queue would block)
        if queue_info['message_count'] >= queue_info['capacity']:
            with self._lock:
                queue_info['status'] = 'full'
                queue_info['last_activity_time'] = time.time()
                self._log_event({
                    'time': time.time(),
                    'queue_id': queue_id,
                    'action': 'enqueue_failed',
                    'reason': 'queue_full'
                })
            return False
        
        # Simulate message enqueue
        def _enqueue():
            try:
                # Non-blocking put with timeout for demonstration
                queue_info['queue'].put(message, block=True, timeout=1)
                
                with self._lock:
                    queue_info['message_count'] += 1
                    queue_info['status'] = 'active'
                    queue_info['last_activity_time'] = time.time()
                    self._log_event({
                        'time': time.time(),
                        'queue_id': queue_id,
                        'action': 'message_enqueued',
                        'message_size': len(str(message))
                    })
            except Exception as e:
                with self._lock:
                    queue_info['status'] = 'error'
                    queue_info['last_activity_time'] = time.time()
                    self._log_event({
                        'time': time.time(),
                        'queue_id': queue_id,
                        'action': 'enqueue_error',
                        'error': str(e)
                    })
        
        threading.Thread(target=_enqueue).start()
        return True
    
    def dequeue_message(self, queue_id):
        """Remove a message from the queue"""
        if queue_id not in self.active_queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue_info = self.active_queues[queue_id]
        
        # Check if queue is empty
        if queue_info['message_count'] <= 0:
            with self._lock:
                queue_info['status'] = 'empty'
                queue_info['last_activity_time'] = time.time()
                self._log_event({
                    'time': time.time(),
                    'queue_id': queue_id,
                    'action': 'dequeue_failed',
                    'reason': 'queue_empty'
                })
            return None
        
        try:
            # Non-blocking get with timeout for demonstration
            message = queue_info['queue'].get(block=False)
            
            with self._lock:
                queue_info['message_count'] = max(0, queue_info['message_count'] - 1)
                queue_info['status'] = 'active'
                queue_info['last_activity_time'] = time.time()
            
            self._log_event({
                'time': time.time(),
                'queue_id': queue_id,
                'action': 'message_dequeued',
                'message_size': len(str(message))
            })
            
            return message
        except Exception as e:
            with self._lock:
                queue_info['status'] = 'error'
                queue_info['last_activity_time'] = time.time()
                self._log_event({
                    'time': time.time(),
                    'queue_id': queue_id,
                    'action': 'dequeue_error',
                    'error': str(e)
                })
            return None
    
    def get_queue_status(self, queue_id=None):
        """Get status information about queues"""
        with self._lock:
            if queue_id:
                if queue_id in self.active_queues:
                    return {queue_id: self.active_queues[queue_id]}
                return {}
            return self.active_queues
    
    def update_queue_status(self, queue_id, status_update):
        """Update status information for a queue"""
        if queue_id not in self.active_queues:
            raise ValueError(f"Queue {queue_id} not found")
            
        with self._lock:
            # Update the queue status
            for key, value in status_update.items():
                self.active_queues[queue_id][key] = value
                
            # Update last activity time
            self.active_queues[queue_id]['last_activity'] = time.time()
            
            # Log the update
            self._log_event({
                'time': time.time(),
                'action': 'update',
                'queue_id': queue_id,
                'message': f"Updated queue {queue_id} status: {', '.join([f'{k}={v}' for k, v in status_update.items()])}"
            })
            
        return True
    
    def add_log_entry(self, queue_id, message):
        """Add a custom log entry for a queue"""
        self._log_event({
            'time': time.time(),
            'action': 'info',
            'queue_id': queue_id,
            'message': message
        })
    
    def get_logs(self):
        """Get all log entries"""
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())
        return logs
    
    def get_log_entries(self):
        """Get formatted log entries for UI display"""
        logs = []
        raw_logs = self.get_logs()  # This empties the queue, so we need to work with the returned logs
        for entry in raw_logs:
            logs.append({
                'timestamp': entry.get('time', 0),
                'component_id': f"queue_{entry.get('queue_id', 'unknown')}",
                'message': entry.get('message', entry.get('action', 'unknown action'))
            })
        return logs
    
    def simulate_slow_consumer(self, queue_id, duration=5):
        """Simulate a slow consumer with backlogged messages"""
        if queue_id not in self.active_queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue_info = self.active_queues[queue_id]
        
        with self._lock:
            queue_info['status'] = 'slow_consumer'
            self._log_event({
                'time': time.time(),
                'queue_id': queue_id,
                'action': 'slow_consumer_started',
                'duration': duration
            })
        
        # Add messages at a fast rate to simulate buildup
        def _add_messages():
            start_time = time.time()
            while time.time() - start_time < duration:
                if queue_info['message_count'] < queue_info['capacity']:
                    with self._lock:
                        queue_info['message_count'] += 1
                        self._log_event({
                            'time': time.time(),
                            'queue_id': queue_id,
                            'action': 'message_buildup',
                            'queue_size': queue_info['message_count']
                        })
                time.sleep(0.1)
            
            with self._lock:
                queue_info['status'] = 'active'
                self._log_event({
                    'time': time.time(),
                    'queue_id': queue_id,
                    'action': 'slow_consumer_ended'
                })
        
        threading.Thread(target=_add_messages).start()
        return True
    
    def unregister_queue(self, queue_id):
        """Unregister a queue and clean up resources"""
        if queue_id not in self.active_queues:
            return False
            
        with self._lock:
            queue_info = self.active_queues[queue_id]
            
            # If we're using a real MP.Queue, we should close it
            # MP.Queue doesn't have a close method, but good practice would be to
            # ensure no references remain
            queue_info['queue'] = None
            
            # Remove from active queues
            del self.active_queues[queue_id]
            
            self._log_event({
                'time': time.time(),
                'queue_id': queue_id,
                'action': 'queue_unregistered'
            })
            
            return True
    
    def cleanup_inactive_queues(self, timeout=600):
        """Clean up queues that have been inactive for the specified timeout (in seconds)"""
        current_time = time.time()
        queues_to_remove = []
        
        with self._lock:
            for queue_id, queue_info in self.active_queues.items():
                # Check if the queue is inactive
                if (queue_info['status'] == 'idle' or queue_info['status'] == 'empty') and \
                   current_time - queue_info.get('last_activity_time', queue_info['creation_time']) > timeout:
                    queues_to_remove.append(queue_id)
        
        # Remove the queues outside the lock
        for queue_id in queues_to_remove:
            self.unregister_queue(queue_id)
            
        return len(queues_to_remove) 