import logging
import sys
import os

# ANSI color codes — Dracula theme matching term.html
class C:
    CYAN = "\033[96m"       # info messages
    GREEN = "\033[92m"      # success messages
    YELLOW = "\033[93m"     # highlight messages
    GRAY = "\033[90m"       # separators, dim text
    ORANGE = "\033[38;5;208m"  # warnings
    WHITE = "\033[97m"      # command/progress messages
    RESET = "\033[0m"

# enable ANSI on Windows
if os.name == "nt":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# set up logging
logger = logging.getLogger("pysack")

class CleanFormatter(logging.Formatter):
    def format(self, record):
        msg = record.getMessage()
        if record.levelno == logging.INFO:
            return msg
        elif record.levelno == logging.WARNING:
            return f"{C.ORANGE}WARNING: {msg}{C.RESET}"
        elif record.levelno == logging.ERROR:
            return f"\033[91mERROR: {msg}{C.RESET}"
        return msg

formatter = CleanFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.stream = sys.stdout

logger.addHandler(handler)
logger.setLevel(logging.INFO)