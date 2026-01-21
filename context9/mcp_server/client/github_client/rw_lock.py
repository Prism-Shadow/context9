import threading


class ReadWriteLock:
    """
    A read-write lock implementation that allows multiple readers or a single writer.

    Multiple readers can acquire the lock simultaneously, but writers require exclusive access.
    This implementation prevents writer starvation by giving priority to waiting writers.
    Uses separate conditions for readers and writers to ensure writer priority.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._readers = 0
        self._writers_waiting = 0
        self._writer_active = False
        self._readers_waiting = 0
        # Separate conditions for readers and writers to ensure writer priority
        self._read_condition = threading.Condition(self._lock)
        self._write_condition = threading.Condition(self._lock)

    def acquire_read(self):
        """Acquire a read lock. Multiple readers can hold this simultaneously."""
        with self._lock:
            # Wait if a writer is active or waiting (prevents writer starvation)
            while self._writer_active or self._writers_waiting > 0:
                self._readers_waiting += 1
                try:
                    self._read_condition.wait()
                finally:
                    self._readers_waiting -= 1
            self._readers += 1

    def release_read(self):
        """Release a read lock."""
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                # Prioritize waiting writers to prevent starvation
                # If there are writers waiting, notify them first
                if self._writers_waiting > 0:
                    # Notify one writer using write condition
                    self._write_condition.notify()
                elif self._readers_waiting > 0:
                    # If no writers waiting, notify all waiting readers
                    self._read_condition.notify_all()

    def acquire_write(self):
        """Acquire a write lock. Exclusive access - blocks all readers and other writers."""
        with self._lock:
            self._writers_waiting += 1
            try:
                # Wait until no readers or writers are active
                while self._readers > 0 or self._writer_active:
                    self._write_condition.wait()
            finally:
                self._writers_waiting -= 1
            self._writer_active = True

    def release_write(self):
        """Release a write lock."""
        with self._lock:
            self._writer_active = False
            # Prioritize waiting writers to prevent starvation
            # If there are other writers waiting, notify only one writer
            if self._writers_waiting > 0:
                self._write_condition.notify()
            elif self._readers_waiting > 0:
                # If no writers waiting, notify all waiting readers
                self._read_condition.notify_all()

    def __enter__(self):
        """Context manager support for read lock."""
        self.acquire_read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support for read lock."""
        self.release_read()


class ReadLockContext:
    """Context manager for read lock."""

    def __init__(self, rw_lock: ReadWriteLock):
        self.rw_lock = rw_lock

    def __enter__(self):
        self.rw_lock.acquire_read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rw_lock.release_read()


class WriteLockContext:
    """Context manager for write lock."""

    def __init__(self, rw_lock: ReadWriteLock):
        self.rw_lock = rw_lock

    def __enter__(self):
        self.rw_lock.acquire_write()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rw_lock.release_write()
