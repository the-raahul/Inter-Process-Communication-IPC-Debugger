"""
Shared memory debugging functionality for IPC Debugger.
"""

import time
import threading
import multiprocessing
from multiprocessing import shared_memory
from queue import Queue, Full as QueueFull
import struct
import random
import uuid

class SharedMemoryDebugger:
    def __init__(self):
        self.shared_memories = {}
        self.log_queue = Queue(maxsize=1000)  # Limit to 1000 log entries
        self._running = False
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start monitoring shared memory"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_shared_mem)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring shared memory"""
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
    
    def _monitor_shared_mem(self):
        """Monitor shared memory and log activities"""
        while self._running:
            time.sleep(0.1)
            
            # Take a snapshot of shared memory states under the lock
            memories_to_check = {}
            with self._lock:
                for shm_id, shm_info in self.shared_memories.items():
                    if shm_info['status'] == 'active' and shm_info['access_count'] > 0:
                        # Make a copy of the necessary information
                        memories_to_check[shm_id] = {
                            'last_write_time': shm_info['last_write_time'],
                            'last_writer': shm_info['last_writer'],
                            'recent_readers': shm_info['recent_readers'].copy() if shm_info['recent_readers'] else []
                        }
            
            # Process shared memory data outside the lock
            conflicts_to_log = []
            for shm_id, info in memories_to_check.items():
                # Check for conflicts (simulated)
                if info['last_write_time'] is not None and \
                   time.time() - info['last_write_time'] < 0.5 and \
                   random.random() < 0.05:  # 5% chance of simulated conflict
                    conflicts_to_log.append({
                        'shm_id': shm_id,
                        'writer': info['last_writer'],
                        'readers': info['recent_readers']
                    })
            
            # Log conflicts under the lock
            if conflicts_to_log:
                with self._lock:
                    for conflict in conflicts_to_log:
                        self._log_event({
                            'time': time.time(),
                            'shm_id': conflict['shm_id'],
                            'action': 'potential_conflict',
                            'writer': conflict['writer'],
                            'readers': conflict['readers']
                        })
    
    def create_shared_memory(self, size=1024, name=None):
        """Create a new shared memory segment and return its ID"""
        if name is None:
            # Generate a unique name if not provided
            name = f"shm_{uuid.uuid4().hex[:8]}"
        
        # Generate a unique ID for this memory segment
        shm_id = f"shm_{len(self.shared_memories) + 1}"
        
        try:
            # Create the shared memory
            shm = shared_memory.SharedMemory(
                name=name,
                create=True,
                size=size
            )
            
            with self._lock:
                # Store memory info
                self.shared_memories[shm_id] = {
                    'shm': shm,
                    'name': name,
                    'size': size,
                    'create_time': time.time(),
                    'last_activity': time.time(),
                    'status': 'active',
                    'access_count': 0,
                    'last_writer': None,
                    'last_write_time': None,
                    'recent_readers': [],
                    'locked_regions': [],
                    'locks': {}  # Simulated lock regions
                }
                
                # Log the creation
                self._log_event({
                    'time': time.time(),
                    'action': 'create',
                    'shm_id': shm_id,
                    'message': f"Created shared memory {shm_id} with name {name} and size {size}"
                })
                
            return shm_id
        except Exception as e:
            self._log_event({
                'time': time.time(),
                'action': 'error',
                'message': f"Error creating shared memory: {str(e)}"
            })
            raise
    
    def register_memory_segment(self, shm_id=None, size=1024, name=None):
        """Register a memory segment for monitoring (or create a new one if shm_id is None)"""
        if shm_id is None:
            return self.create_shared_memory(size, name)
            
        # If shm_id is provided, check if it already exists
        if shm_id in self.shared_memories:
            return shm_id
            
        # Generate a unique name if not provided
        if name is None:
            name = f"shm_{uuid.uuid4().hex[:8]}"
            
        try:
            # Create the shared memory
            shm = shared_memory.SharedMemory(
                name=name,
                create=True,
                size=size
            )
            
            with self._lock:
                # Store memory info
                self.shared_memories[shm_id] = {
                    'shm': shm,
                    'name': name,
                    'size': size,
                    'create_time': time.time(),
                    'last_activity': time.time(),
                    'status': 'active',
                    'access_count': 0,
                    'last_writer': None,
                    'locked_regions': [],
                    'locks': {}  # Simulated lock regions
                }
                
                # Log the creation
                self._log_event({
                    'time': time.time(),
                    'action': 'create',
                    'shm_id': shm_id,
                    'message': f"Registered shared memory {shm_id} with name {name} and size {size}"
                })
                
            return shm_id
        except Exception as e:
            self._log_event({
                'time': time.time(),
                'action': 'error',
                'message': f"Error registering shared memory: {str(e)}"
            })
            raise
    
    def write_to_memory(self, shm_id, offset, data, process_id='main'):
        """Write data to shared memory and track activity"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        shm_info = self.shared_memories[shm_id]
        shm = shm_info['shm']
        
        # Check if the write is in a locked region
        with self._lock:
            for (start, end), lock_info in shm_info['locks'].items():
                # If this write overlaps with a locked region
                if offset >= start and offset < end:
                    if lock_info['owner'] != process_id:
                        self._log_event({
                            'time': time.time(),
                            'shm_id': shm_id,
                            'action': 'write_blocked',
                            'region': (start, end),
                            'offset': offset,
                            'process_id': process_id,
                            'owner': lock_info['owner']
                        })
                        return False
        
        # Perform the write
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                data = str(data).encode('utf-8')
            
            # Check if write extends beyond the shared memory size
            if offset + len(data) > shm_info['size']:
                with self._lock:
                    self._log_event({
                        'time': time.time(),
                        'shm_id': shm_id,
                        'action': 'write_error',
                        'reason': 'out_of_bounds',
                        'offset': offset,
                        'size': len(data),
                        'shm_size': shm_info['size']
                    })
                return False
            
            # Write the data
            shm.buf[offset:offset+len(data)] = data
            
            # Update tracking info
            with self._lock:
                shm_info['access_count'] += 1
                shm_info['last_write_time'] = time.time()
                shm_info['last_writer'] = process_id
                shm_info['last_activity_time'] = time.time()
                
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'memory_written',
                    'offset': offset,
                    'size': len(data),
                    'process_id': process_id
                })
            
            return True
        except Exception as e:
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'write_error',
                    'error': str(e),
                    'offset': offset,
                    'process_id': process_id
                })
            return False
    
    def read_from_memory(self, shm_id, offset, size, process_id='main'):
        """Read data from shared memory and track activity"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        shm_info = self.shared_memories[shm_id]
        shm = shm_info['shm']
        
        # Check if read extends beyond the shared memory size
        if offset + size > shm_info['size']:
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'read_error',
                    'reason': 'out_of_bounds',
                    'offset': offset,
                    'size': size,
                    'shm_size': shm_info['size']
                })
            return None
        
        # Perform the read
        try:
            data = bytes(shm.buf[offset:offset+size])
            
            # Update tracking info
            with self._lock:
                shm_info['access_count'] += 1
                shm_info['last_activity_time'] = time.time()
                
                # Keep track of readers for potential conflict detection
                if process_id not in shm_info['recent_readers']:
                    shm_info['recent_readers'].append(process_id)
                    if len(shm_info['recent_readers']) > 5:
                        shm_info['recent_readers'] = shm_info['recent_readers'][-5:]
                
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'memory_read',
                    'offset': offset,
                    'size': size,
                    'process_id': process_id
                })
            
            return data
        except Exception as e:
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'read_error',
                    'error': str(e),
                    'offset': offset,
                    'process_id': process_id
                })
            return None
    
    def lock_region(self, shm_id, start, end, process_id='main'):
        """Lock a region of shared memory for exclusive access"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        shm_info = self.shared_memories[shm_id]
        
        # Check for overlapping locks
        with self._lock:
            for (lock_start, lock_end), lock_info in shm_info['locks'].items():
                if (start < lock_end and end > lock_start):
                    self._log_event({
                        'time': time.time(),
                        'shm_id': shm_id,
                        'action': 'lock_conflict',
                        'region_requested': (start, end),
                        'region_locked': (lock_start, lock_end),
                        'process_id': process_id,
                        'lock_owner': lock_info['owner']
                    })
                    return False
            
            # No conflicts, create the lock
            region_key = (start, end)
            shm_info['locks'][region_key] = {
                'owner': process_id,
                'lock_time': time.time()
            }
            
            # Update last activity time
            shm_info['last_activity_time'] = time.time()
            
            self._log_event({
                'time': time.time(),
                'shm_id': shm_id,
                'action': 'region_locked',
                'start': start,
                'end': end,
                'process_id': process_id
            })
            
            return True
    
    def unlock_region(self, shm_id, start, end, process_id='main'):
        """Unlock a previously locked region of shared memory"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        shm_info = self.shared_memories[shm_id]
        region_key = (start, end)
        
        with self._lock:
            if region_key in shm_info['locks']:
                lock_info = shm_info['locks'][region_key]
                
                # Check if the process owns the lock
                if lock_info['owner'] != process_id:
                    self._log_event({
                        'time': time.time(),
                        'shm_id': shm_id,
                        'action': 'unlock_error',
                        'region': (start, end),
                        'process_id': process_id,
                        'lock_owner': lock_info['owner']
                    })
                    return False
                
                # Remove the lock
                del shm_info['locks'][region_key]
                
                # Update last activity time
                shm_info['last_activity_time'] = time.time()
                
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'region_unlocked',
                    'start': start,
                    'end': end,
                    'process_id': process_id
                })
                
                return True
            else:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'unlock_error',
                    'reason': 'region_not_locked',
                    'region': (start, end),
                    'process_id': process_id
                })
                return False
    
    def close_shared_memory(self, shm_id):
        """Close and unlink a shared memory segment"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        shm_info = self.shared_memories[shm_id]
        
        try:
            shm_info['shm'].close()
            shm_info['shm'].unlink()
            
            with self._lock:
                shm_info['status'] = 'closed'
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'shm_closed'
                })
            
            return True
        except Exception as e:
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'close_error',
                    'error': str(e)
                })
            return False
    
    def get_memory_status(self, shm_id=None):
        """Get status information about shared memory segments"""
        with self._lock:
            if shm_id:
                if shm_id in self.shared_memories:
                    return {shm_id: self.shared_memories[shm_id]}
                return {}
            return self.shared_memories
    
    def update_memory_status(self, shm_id, status_update):
        """Update status information for a shared memory segment"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
            
        with self._lock:
            # Update the memory status
            for key, value in status_update.items():
                self.shared_memories[shm_id][key] = value
                
            # Update last activity time
            self.shared_memories[shm_id]['last_activity'] = time.time()
            
            # Log the update
            self._log_event({
                'time': time.time(),
                'action': 'update',
                'shm_id': shm_id,
                'message': f"Updated shared memory {shm_id} status: {', '.join([f'{k}={v}' for k, v in status_update.items()])}"
            })
            
        return True
    
    def add_log_entry(self, shm_id, message):
        """Add a custom log entry for a shared memory segment"""
        self._log_event({
            'time': time.time(),
            'action': 'info',
            'shm_id': shm_id,
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
                'component_id': f"shm_{entry.get('shm_id', 'unknown')}",
                'message': entry.get('message', entry.get('action', 'unknown action'))
            })
        return logs
    
    def simulate_race_condition(self, shm_id, region=(0, 100), duration=2):
        """Simulate a race condition in shared memory access"""
        if shm_id not in self.shared_memories:
            raise ValueError(f"Shared memory {shm_id} not found")
        
        with self._lock:
            self._log_event({
                'time': time.time(),
                'shm_id': shm_id,
                'action': 'race_condition_simulation_started',
                'region': region,
                'duration': duration
            })
        
        # Simulate multiple writers to the same region
        def _race_simulation():
            start_time = time.time()
            processes = [f"process_{i}" for i in range(3)]
            
            while time.time() - start_time < duration:
                for process in processes:
                    # Simulate simultaneous writes to the same region
                    offset = random.randint(region[0], region[1] - 10)
                    data = f"data-{random.randint(1, 100)}".encode('utf-8')
                    
                    try:
                        self.write_to_memory(shm_id, offset, data, process_id=process)
                        time.sleep(0.05)  # Small delay to simulate near-simultaneous access
                    except Exception:
                        pass
            
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'shm_id': shm_id,
                    'action': 'race_condition_simulation_ended',
                    'region': region
                })
        
        threading.Thread(target=_race_simulation).start()
        return True
    
    def unregister_shared_memory(self, shm_id):
        """Unregister shared memory and clean up resources"""
        if shm_id not in self.shared_memories:
            return False
            
        with self._lock:
            shm_info = self.shared_memories[shm_id]
            
            # First close it if not already closed
            if shm_info['status'] != 'closed':
                try:
                    shm_info['shm'].close()
                    shm_info['shm'].unlink()
                except Exception as e:
                    self._log_event({
                        'time': time.time(),
                        'shm_id': shm_id,
                        'action': 'unregister_error',
                        'error': str(e)
                    })
            
            # Remove from shared memories
            del self.shared_memories[shm_id]
            
            self._log_event({
                'time': time.time(),
                'shm_id': shm_id,
                'action': 'shm_unregistered'
            })
            
            return True
    
    def cleanup_inactive_memory(self, timeout=600):
        """Clean up shared memory segments that have been inactive for the specified timeout (in seconds)"""
        current_time = time.time()
        shm_to_remove = []
        
        with self._lock:
            for shm_id, shm_info in self.shared_memories.items():
                # Check if the shared memory is closed or inactive
                if shm_info['status'] == 'closed' or \
                   (shm_info['status'] == 'active' and 
                    current_time - shm_info.get('last_activity_time', shm_info['creation_time']) > timeout):
                    shm_to_remove.append(shm_id)
        
        # Remove the shared memory segments outside the lock
        for shm_id in shm_to_remove:
            self.unregister_shared_memory(shm_id)
            
        return len(shm_to_remove) 