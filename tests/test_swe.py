import unittest
from swe.context import SweContext
import os

class TestSweContext(unittest.TestCase):
    def test_init(self):
        swe_context = SweContext()
        swe_context.init()
        self.assertTrue(os.path.exists(swe_context.swe_dir))

if __name__ == '__main__':
    unittest.main()