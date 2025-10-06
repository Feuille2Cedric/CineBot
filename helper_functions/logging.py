
import logging

def setup_logger():
    logger = logging.getLogger("quizbot")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger

# tiny alias when a logger is optional
def get_logger():
    return setup_logger()
