import unittest
from nose_parameterized import parameterized

from main import _extract_instance_id


class QCUnitTest(unittest.TestCase):

    @parameterized.expand([
        ("simple", "abc <id:i-324>", "i-324"),
    ])
    def test_extract_instance_id(self, name, inp, expected):
        self.assertEqual(_extract_instance_id(inp), expected, name)
