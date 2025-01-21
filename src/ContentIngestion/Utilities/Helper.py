import logging
import time


def log_execution_time(func):
    """
    A decorator that logs the duration of method execution.

    Args:
    func (callable): The function to be decorated.

    Returns:
    The decorated function.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"{func.__name__} took {duration} seconds to execute.")
        return result

    return wrapper