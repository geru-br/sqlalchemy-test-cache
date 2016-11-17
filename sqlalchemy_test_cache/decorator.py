import logging
import os

from .sqlalchemy_test_cache import DumpManager
from .utils import generate_dump_path


logger = logging.getLogger(__name__)


def cache_sql(base_model, dbsession):

    def wrapper(test_function):

        def _wrapper(self, *args, **kwargs):

            path = generate_dump_path(self.__class__.__name__, id(self.__class__))
            dm = DumpManager(base_model, dbsession)

            if not os.path.exists(path):

                logger.info('Dump file {!r} does not exists. The queries will not be cached.'.format(path))

                result = test_function(self, *args, **kwargs)

                with open(path, 'w') as f:
                    f.write('\n'.join(dm.dump_all_tables()))

                return result

            else:

                logger.info('Loading data from cache file: {!r}'.format(path))

                with open(path, 'r') as f:
                    dm.loads(f.readlines())

                return

        _wrapper.__name__ = test_function.__name__

        return _wrapper

    return wrapper
