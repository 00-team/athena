import logging
from datetime import datetime
from logging import FileHandler, Formatter, StreamHandler

from .settings import BASE_DIR

MAIN_FORMATTER = Formatter(
    fmt='%(asctime)s.%(msecs)03d <%(levelname)s> [%(module)s]: %(message)s',
    datefmt='%H:%M:%S'
)


class DailyRotating(FileHandler):
    def __init__(self, dirname: str):
        now = datetime.now()
        self.day = now.day
        self.path = BASE_DIR / f'logs/{dirname}'

        self.path.mkdir(parents=True, exist_ok=True)
        filename = str(self.path / (now.strftime('%m-%d') + '.log'))

        super().__init__(filename, 'a', 'utf-8')

    def emit(self, record):
        try:
            now = datetime.now()

            if now.day != self.day:
                if self.stream:
                    self.stream.close()
                    self.stream = None

                self.path.mkdir(parents=True, exist_ok=True)
                fn = (now.strftime('%m-%d') + '.log')
                self.baseFilename = str(self.path / fn)

                self.day = now.day
                if not self.delay:
                    self.stream = self._open()

            super().emit(record)

        except Exception:
            self.handleError(record)


def get_logger(package='main'):
    logger = logging.getLogger(package)

    logger.setLevel(logging.DEBUG)

    file_handler = DailyRotating(package)
    file_handler.setFormatter(MAIN_FORMATTER)
    logger.addHandler(file_handler)

    strm_handler = StreamHandler()
    strm_handler.setFormatter(MAIN_FORMATTER)
    logger.addHandler(strm_handler)

    return logger


logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'main': MAIN_FORMATTER
    }
})
