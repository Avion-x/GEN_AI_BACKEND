
import inspect
import logging



class CustomLogger():
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.registry = {
            "DEBUG" : self.logger.debug,
            "INFO" : self.logger.info,
            "WARNING" : self.logger.warning,
            "ERROR" : self.logger.error,
            "CRITICAL" : self.logger.critical,
        }

    def get_logger(self, level="DEBUG"):
        return self.registry.get(level.upper())
    
    def log(self, level = "DEBUG", message="", *args, **kwargs):
        caller_details = self.get_caller_details()
        _logger = self.get_logger(level.upper())
        try:
            _logger(f"{level}:{message} ::: Caller Details:{caller_details}")
        except Exception as e:
            self.logger.error(f"ERROR :  while logging - {message} ::: Caller details are {caller_details}, Error Message is {e} ")

    def get_caller_details(self):
        try:
            frame_info = inspect.stack()[2]
            frame = frame_info[0]
            return {
                "filename" : frame.f_code.co_filename,
                "line_number" : frame.f_lineno,
                "function_name" : frame.f_code.co_name,
                "class_name" : frame.f_locals.get('self', None).__class__.__name__
            }
        except Exception as e:
            self.logger.error(f"ERROR : while getting caller details in logger: %s" % e)
            return {}

logger = CustomLogger()
