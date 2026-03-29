import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="gestvoice.log",   # 🔥 log file
    filemode="a"
)

def log(msg):
    print(msg)        # still show in terminal
    logging.info(msg)


# Alternative way to log to a file with less memory usage and keeping 2 last logs


# import logging
# from logging.handlers import RotatingFileHandler

# logger = logging.getLogger("GestVoice")
# logger.setLevel(logging.INFO)

# handler = RotatingFileHandler(
#     "gestvoice.log",
#     maxBytes=1_000_000,   # 1 MB
#     backupCount=2         # keep 2 old logs
# )

# formatter = logging.Formatter(
#     "%(asctime)s - %(levelname)s - %(message)s"
# )

# handler.setFormatter(formatter)
# logger.addHandler(handler)

# def log(msg):
#     print(msg)
#     logger.info(msg)