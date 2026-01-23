"""
Utilities for the simulator, including logging configuration.
"""
import logging

def get_logger(name: str):
    """
    Configures and returns a logger.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)
