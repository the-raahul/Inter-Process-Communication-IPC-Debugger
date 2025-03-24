"""
Deadlock detection functionality for IPC Debugger.
"""

import time
import threading
import random
from queue import Queue, Full as QueueFull

class DeadlockDetector:
    def __init__(self):
        self.resources = {}  # Resource ID -> {owner, waiters, state}
        self.processes = {}  # Process ID -> {owns, waiting_for}
        self.log_queue = Queue(maxsize=1000)  # Limit to 1000 log entries
        self._running = False
        self._lock = threading.Lock()
        self.nx = None
        try:
            import networkx as nx
            self._has_networkx = True
            self.nx = nx
        except ImportError:
            self._has_networkx = False
    
    def start_monitoring(self):
        """Start monitoring for deadlocks"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_deadlocks)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring for deadlocks"""
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
    
    def _monitor_deadlocks(self):
        """Periodically check for deadlocks"""
        while self._running:
            time.sleep(0.5)
            
            # Grab a snapshot of the current state under the lock
            with self._lock:
                # Create a deep copy of necessary data to detect deadlocks
                resources_copy = {}
                for r_id, r_info in self.resources.items():
                    resources_copy[r_id] = {
                        'owner': r_info['owner'],
                        'waiters': r_info['waiters'].copy(),
                        'state': r_info['state']
                    }
                
                processes_copy = {}
                for p_id, p_info in self.processes.items():
                    processes_copy[p_id] = {
                        'owns': p_info['owns'].copy(),
                        'waiting_for': p_info['waiting_for']
                    }
            
            # Perform deadlock detection on the copied data
            deadlocks = self._detect_deadlocks_from_snapshot(resources_copy, processes_copy)
            
            # Log any detected deadlocks
            if deadlocks:
                with self._lock:
                    for cycle in deadlocks:
                        self._log_event({
                            'time': time.time(),
                            'action': 'deadlock_detected',
                            'processes': cycle
                        })
    
    def _detect_deadlocks_from_snapshot(self, resources, processes):
        """Detect deadlocks using a snapshot of resources and processes"""
        # Build a wait-for graph as adjacency list
        wait_for = {}
        for process_id, process in processes.items():
            if process['waiting_for'] is not None:
                resource_id = process['waiting_for']
                if resource_id in resources:
                    owner = resources[resource_id]['owner']
                    if owner is not None:
                        if process_id not in wait_for:
                            wait_for[process_id] = []
                        wait_for[process_id].append(owner)
        
        # Check if we can use networkx
        if self._has_networkx and self.nx:
            # Use networkx for cycle detection
            G = self.nx.DiGraph()
            
            # Add all processes as nodes
            for process_id in processes:
                G.add_node(process_id)
            
            # Add edges for wait relationships
            for process_id, neighbors in wait_for.items():
                for neighbor in neighbors:
                    G.add_edge(process_id, neighbor)
            
            # Find cycles (deadlocks) with timeout protection
            try:
                # For large graphs, simple_cycles can be expensive
                # So we use a timeout mechanism
                if len(processes) > 50:  # Only apply timeout for large graphs
                    import signal
                    
                    class TimeoutException(Exception):
                        pass
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutException()
                    
                    # Set a 2-second timeout
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(2)
                    
                    try:
                        deadlocks = list(self.nx.simple_cycles(G))
                        signal.alarm(0)  # Disable the alarm
                        return deadlocks
                    except TimeoutException:
                        # Cycle detection timed out, fall back to simple detection
                        pass
                    finally:
                        signal.alarm(0)  # Ensure the alarm is disabled
                else:
                    # For small graphs, use regular detection
                    deadlocks = list(self.nx.simple_cycles(G))
                    return deadlocks
            except Exception:
                # Fallback to simple detection on any error
                pass
        
        # Simple cycle detection using DFS (as a fallback)
        deadlocks = []
        
        def find_cycle(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            if node in wait_for:
                for neighbor in wait_for[node]:
                    cycle = find_cycle(neighbor, path, visited)
                    if cycle:
                        return cycle
            
            path.pop()
            return None
        
        # Check each process as a potential starting point
        for process_id in processes:
            visited = set()
            cycle = find_cycle(process_id, [], visited)
            if cycle:
                deadlocks.append(cycle)
        
        return deadlocks
    
    def register_resource(self, resource_id, resource_type='lock'):
        """Register a resource for deadlock tracking"""
        with self._lock:
            if resource_id in self.resources:
                return False
            
            self.resources[resource_id] = {
                'type': resource_type,
                'owner': None,
                'waiters': [],
                'waiter_timestamps': {},  # Track when processes started waiting
                'state': 'free'
            }
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_registered',
                'resource_id': resource_id,
                'resource_type': resource_type
            })
            
            return True
    
    def register_process(self, process_id):
        """Register a process for deadlock tracking"""
        with self._lock:
            if process_id in self.processes:
                return False
            
            self.processes[process_id] = {
                'owns': [],
                'waiting_for': None
            }
            
            self._log_event({
                'time': time.time(),
                'action': 'process_registered',
                'process_id': process_id
            })
            
            return True
    
    def request_resource(self, process_id, resource_id):
        """Track a process requesting a resource"""
        with self._lock:
            if process_id not in self.processes or resource_id not in self.resources:
                return False
            
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # If resource is free, assign it
            if resource['state'] == 'free':
                resource['state'] = 'owned'
                resource['owner'] = process_id
                process['owns'].append(resource_id)
                
                self._log_event({
                    'time': time.time(),
                    'action': 'resource_acquired',
                    'resource_id': resource_id,
                    'process_id': process_id
                })
                
                return True
            else:
                # Resource is owned, add process to waiters
                if process_id not in resource['waiters']:
                    resource['waiters'].append(process_id)
                    # Record timestamp when process started waiting
                    resource['waiter_timestamps'][process_id] = time.time()
                
                # Mark that this process is waiting for this resource
                process['waiting_for'] = resource_id
                
                self._log_event({
                    'time': time.time(),
                    'action': 'resource_waiting',
                    'resource_id': resource_id,
                    'process_id': process_id,
                    'owner': resource['owner']
                })
                
                return False
    
    def release_resource(self, process_id, resource_id):
        """Track a process releasing a resource"""
        with self._lock:
            if process_id not in self.processes or resource_id not in self.resources:
                return False
            
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Check if process owns this resource
            if resource['owner'] != process_id:
                self._log_event({
                    'time': time.time(),
                    'action': 'release_error',
                    'resource_id': resource_id,
                    'process_id': process_id,
                    'owner': resource['owner']
                })
                return False
            
            # Release the resource
            resource['owner'] = None
            process['owns'].remove(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_released',
                'resource_id': resource_id,
                'process_id': process_id
            })
            
            # If there are waiters, select the next one based on fairness policy
            if resource['waiters']:
                # Get the longest waiting process (based on timestamp)
                oldest_wait_time = float('inf')
                next_process_id = None
                
                for waiter_id in resource['waiters']:
                    # Check if the process is still valid and waiting
                    if waiter_id in self.processes:
                        wait_process = self.processes[waiter_id]
                        if wait_process['waiting_for'] == resource_id:
                            # Get the timestamp when this process started waiting
                            wait_time = resource['waiter_timestamps'].get(waiter_id, time.time())
                            if wait_time < oldest_wait_time:
                                oldest_wait_time = wait_time
                                next_process_id = waiter_id
                
                if next_process_id:
                    # Remove from waiters list
                    resource['waiters'].remove(next_process_id)
                    if next_process_id in resource['waiter_timestamps']:
                        del resource['waiter_timestamps'][next_process_id]
                    
                    # Assign resource
                    next_process = self.processes[next_process_id]
                    resource['state'] = 'owned'
                    resource['owner'] = next_process_id
                    next_process['owns'].append(resource_id)
                    next_process['waiting_for'] = None
                    
                    self._log_event({
                        'time': time.time(),
                        'action': 'resource_acquired',
                        'resource_id': resource_id,
                        'process_id': next_process_id,
                        'wait_time': time.time() - oldest_wait_time
                    })
                else:
                    # No valid waiters
                    resource['state'] = 'free'
                    resource['waiters'] = []
                    resource['waiter_timestamps'] = {}
            else:
                resource['state'] = 'free'
            
            return True
    
    def detect_deadlocks(self):
        """Detect deadlocks using wait-for graph analysis"""
        with self._lock:
            return self._detect_deadlocks_from_snapshot(self.resources, self.processes)
    
    def get_resource_status(self):
        """Get status information about resources"""
        with self._lock:
            return {r_id: {
                'type': r_info['type'],
                'state': r_info['state'],
                'owner': r_info['owner'],
                'waiters': r_info['waiters'].copy()
            } for r_id, r_info in self.resources.items()}
    
    def get_process_status(self):
        """Get status information about processes"""
        with self._lock:
            return {p_id: {
                'owns': p_info['owns'].copy(),
                'waiting_for': p_info['waiting_for']
            } for p_id, p_info in self.processes.items()}
    
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
            # Determine if this is process or resource related
            if 'process_id' in entry:
                component_id = f"deadlock_process_{entry.get('process_id', 'unknown')}"
            elif 'resource_id' in entry:
                component_id = f"deadlock_resource_{entry.get('resource_id', 'unknown')}"
            else:
                component_id = "deadlock_detector"
                
            logs.append({
                'timestamp': entry.get('time', 0),
                'component_id': component_id,
                'message': entry.get('message', entry.get('action', 'unknown action'))
            })
        return logs
    
    def add_log_entry(self, component_id, message):
        """Add a custom log entry"""
        self._log_event({
            'time': time.time(),
            'action': 'info',
            'message': message,
            'component': component_id
        })
    
    def simulate_deadlock(self, num_processes=3, num_resources=3, timeout=10):
        """Simulate a deadlock scenario"""
        # Register processes and resources
        processes = [f"sim_process_{i}" for i in range(num_processes)]
        resources = [f"sim_resource_{i}" for i in range(num_resources)]
        
        with self._lock:
            for process_id in processes:
                self.register_process(process_id)
            
            for resource_id in resources:
                self.register_resource(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'deadlock_simulation_started',
                'processes': processes,
                'resources': resources
            })
        
        # Start simulation in a separate thread
        def _simulate():
            # First, have each process acquire one resource in order
            for i, process_id in enumerate(processes):
                resource_id = resources[i % num_resources]
                self.request_resource(process_id, resource_id)
                time.sleep(0.1)
            
            # Then, have each try to acquire the next resource, creating a circle
            for i, process_id in enumerate(processes):
                next_resource = resources[(i + 1) % num_resources]
                self.request_resource(process_id, next_resource)
                time.sleep(0.1)
            
            # Wait for detection
            time.sleep(timeout)
            
            # Release resources to resolve deadlock
            for i, process_id in enumerate(processes):
                resource_id = resources[i % num_resources]
                self.release_resource(process_id, resource_id)
            
            with self._lock:
                self._log_event({
                    'time': time.time(),
                    'action': 'deadlock_simulation_ended'
                })
        
        threading.Thread(target=_simulate).start()
        return {
            'processes': processes,
            'resources': resources
        }

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

    def unregister_process(self, process_id):
        """Unregister and cleanup a process from deadlock tracking"""
        with self._lock:
            if process_id not in self.processes:
                return False
            
            # Get the resources owned by this process
            owned_resources = self.processes[process_id]['owns'].copy()
            
            # Release all resources owned by this process
            for resource_id in owned_resources:
                if resource_id in self.resources:
                    resource = self.resources[resource_id]
                    if resource['owner'] == process_id:
                        # Clear ownership
                        resource['owner'] = None
                        
                        # If there are waiters, assign to the first one
                        if resource['waiters']:
                            next_process_id = resource['waiters'][0]
                            oldest_wait_time = resource['waiter_timestamps'].get(next_process_id, time.time())
                            
                            # Find the process that's been waiting longest
                            for waiter_id, timestamp in resource['waiter_timestamps'].items():
                                if timestamp < oldest_wait_time:
                                    oldest_wait_time = timestamp
                                    next_process_id = waiter_id
                            
                            if next_process_id in self.processes:
                                # Remove from waiters list
                                resource['waiters'].remove(next_process_id)
                                if next_process_id in resource['waiter_timestamps']:
                                    del resource['waiter_timestamps'][next_process_id]
                                
                                # Assign resource
                                next_process = self.processes[next_process_id]
                                resource['state'] = 'owned'
                                resource['owner'] = next_process_id
                                next_process['owns'].append(resource_id)
                                next_process['waiting_for'] = None
                                
                                self._log_event({
                                    'time': time.time(),
                                    'action': 'resource_reassigned',
                                    'resource_id': resource_id,
                                    'process_id': next_process_id,
                                    'previous_owner': process_id
                                })
                            else:
                                resource['state'] = 'free'
                        else:
                            resource['state'] = 'free'
                            
                        self._log_event({
                            'time': time.time(),
                            'action': 'resource_force_released',
                            'resource_id': resource_id,
                            'process_id': process_id
                        })
            
            # Remove any entries where this process is waiting for a resource
            for resource_id, resource in self.resources.items():
                if process_id in resource['waiters']:
                    resource['waiters'].remove(process_id)
                    if process_id in resource['waiter_timestamps']:
                        del resource['waiter_timestamps'][process_id]
            
            # Remove the process
            del self.processes[process_id]
            
            self._log_event({
                'time': time.time(),
                'action': 'process_unregistered',
                'process_id': process_id
            })
            
            return True
    
    def set_resource_owner(self, resource_id, process_id):
        """Set a process as the owner of a resource"""
        with self._lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False
                
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Check if resource is already owned
            if resource['state'] == 'owned' and resource['owner'] is not None:
                # Release from previous owner
                prev_owner = resource['owner']
                if prev_owner in self.processes:
                    self.processes[prev_owner]['owns'].remove(resource_id)
            
            # Set new owner
            resource['state'] = 'owned'
            resource['owner'] = process_id
            
            # Add to process's owned resources if not already there
            if resource_id not in process['owns']:
                process['owns'].append(resource_id)
            
            self._log_event({
                'time': time.time(),
                'action': 'resource_owner_set',
                'resource_id': resource_id,
                'process_id': process_id
            })
            
            return True
    
    def add_waiting_process(self, resource_id, process_id):
        """Add a process to the waiters list for a resource"""
        with self._lock:
            if resource_id not in self.resources or process_id not in self.processes:
                return False
                
            resource = self.resources[resource_id]
            process = self.processes[process_id]
            
            # Add to waiters if not already waiting
            if process_id not in resource['waiters']:
                resource['waiters'].append(process_id)
                resource['waiter_timestamps'][process_id] = time.time()
            
            # Set process waiting_for
            process['waiting_for'] = resource_id
            
            self._log_event({
                'time': time.time(),
                'action': 'process_waiting',
                'resource_id': resource_id,
                'process_id': process_id
            })
            
            return True 