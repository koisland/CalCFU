import re
import logging
import traceback

logger = logging.getLogger(__name__)


def check_if_unittest():
    stack = repr(traceback.extract_stack())
    # pprint.pprint(stack)
    if re.search(r"test_(calc|reader)\.py", stack):
        return True
    else:
        return False


class ReaderError(Exception):
    def __init__(self, msg):
        is_unittest = check_if_unittest()
        if not is_unittest:
            logger.error(msg)
        super().__init__(msg)


class CalCFUError(Exception):
    def __init__(self, msg):
        is_unittest = check_if_unittest()
        if not is_unittest:
            logger.error(msg)
        super().__init__(msg)


class PlateError(Exception):
    def __init__(self, msg):
        is_unittest = check_if_unittest()
        if not is_unittest:
            logger.error(msg)
        super().__init__(msg)
