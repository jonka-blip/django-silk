from django.test import TestCase
from mock import Mock, NonCallableMock, NonCallableMagicMock, patch

from silky.collector import DataCollector
from silky.models import SQLQuery, Request
from silky.sql import execute_sql


def mock_sql():
    mock_sql_query = Mock(spec_set=['_execute_sql', 'query', 'as_sql'])
    mock_sql_query._execute_sql = Mock()
    mock_sql_query.query = NonCallableMock(spec_set=['model'])
    mock_sql_query.query.model = Mock()
    query_string = 'SELECT * from table_name'
    mock_sql_query.as_sql = Mock(return_value=(query_string, ()))
    return mock_sql_query, query_string


class TestCall(TestCase):
    @classmethod
    def setUpClass(cls):
        SQLQuery.objects.all().delete()
        cls.mock_sql, cls.query_string = mock_sql()
        kwargs = {
            'one': 1,
            'two': 2
        }
        cls.args = [1, 2]
        cls.kwargs = kwargs
        execute_sql(cls.mock_sql, *cls.args, **cls.kwargs)

    def test_called(self):
        self.mock_sql._execute_sql.assert_called_once_with(*self.args, **self.kwargs)

    def test_count(self):
        self.assertEqual(1, SQLQuery.objects.count())

    def _get_query(self):
        try:
            query = SQLQuery.objects.all()[0]
        except IndexError:
            self.fail('No queries created')
        return query

    def test_no_request(self):
        query = self._get_query()
        self.assertFalse(query.request)

    def test_query(self):
        query = self._get_query()
        self.assertEqual(query.query, self.query_string)


class TestCallSilky(TestCase):
    def test_no_effect(self):
        SQLQuery.objects.all().delete()
        sql, _ = mock_sql()
        sql.query.model = NonCallableMagicMock(spec_set=['__module__'])
        sql.query.model.__module__ = 'silky.models'
        # No SQLQuery models should be created for silky requests for obvious reasons
        with patch('silky.sql.models.SQLQuery') as mock_SQLQuery:
            execute_sql(sql)
            self.assertFalse(mock_SQLQuery.call_count)


class TestCollectorInteraction(TestCase):

    def _query(self):
        try:
            query = SQLQuery.objects.all()[0]
        except IndexError:
            self.fail('No queries created')
        return query

    def test_request(self):
        SQLQuery.objects.all().delete()
        sql, _ = mock_sql()
        DataCollector().request = Request.objects.create(path='/path/to/somewhere')
        execute_sql(sql)
        query = self._query()
        self.assertEqual(query.request, DataCollector().request)

    def test_registration(self):
        SQLQuery.objects.all().delete()
        sql, _ = mock_sql()
        DataCollector().request = Request.objects.create(path='/path/to/somewhere')
        execute_sql(sql)
        query = self._query()
        self.assertIn(query, DataCollector().queries)
