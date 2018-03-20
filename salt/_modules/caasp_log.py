from __future__ import absolute_import

import logging
import os
import sys

CAAS_LOG_FMT = '[%(levelname)-8s] CaaS: %(message)s'
CAAS_LOG_DATE_FMT = '%H:%M:%S'

# try to get an alternative logging level from the CAAS_LOG env
level = logging.getLevelName(os.getenv('CAAS_LOG', 'INFO'))

log = logging.getLogger(__name__)
log.setLevel(level)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(level)
formatter = logging.Formatter(CAAS_LOG_FMT, datefmt=CAAS_LOG_DATE_FMT)
ch.setFormatter(formatter)
log.addHandler(ch)


class ExecutionAborted(Exception):
    pass


def abort(*args, **kwargs):
    '''
    Abort the Salt execution with an error
    '''
    log.error(*args, **kwargs)
    raise ExecutionAborted()


def error(*args, **kwargs):
    '''
    Log a error message
    '''
    log.error(*args, **kwargs)


def warn(*args, **kwargs):
    '''
    Log a warning message
    '''
    log.warn(*args, **kwargs)


def debug(*args, **kwargs):
    '''
    Log a debug message
    '''
    log.debug(*args, **kwargs)
