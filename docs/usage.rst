=====
Usage
=====

To use SqlAlchemy Test Cache in a project::

    import sqlalchemy_test_cache

    class MyTestCase(unittest.TestCase):

      def setUp(self):
          super(MyTestCase, self).setUp()
          self._cache_objects()

      @sqlalchemy_test_cache.cache_sql(Base, DBSession)
      def _cache_objects(self):

          # objects can be considered as reduntant for all tests

      def test_my_code(self):
          ...
