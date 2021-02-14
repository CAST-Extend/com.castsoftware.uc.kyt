import collections
import logging
logger = logging.getLogger(__name__) 
logging.basicConfig(
    format='[%(levelname)-8s][%(asctime)s][%(name)-12s] %(message)s',
    level=logging.INFO
)

TQueryConfig = collections.namedtuple("TQueryConfig","countH countQ selectH selectQ")