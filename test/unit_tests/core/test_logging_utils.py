import os
import sys
import unittest
import logging

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestLoggingUtils(unittest.TestCase):
    def setUp(self):
        # Reset the configuration flag before each test
        import core.logging_utils
        core.logging_utils._CONFIGURED = False
        # Clear any existing handlers
        logging.root.handlers = []

    def test_get_logger_basic(self):
        from core.logging_utils import get_logger
        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")

    def test_get_logger_default_level(self):
        from core.logging_utils import get_logger
        # Default should be INFO
        os.environ.pop("LOG_LEVEL", None)
        logger = get_logger("default_test")
        self.assertEqual(logger.getEffectiveLevel(), logging.INFO)

    def test_get_logger_custom_level(self):
        from core.logging_utils import get_logger
        import core.logging_utils
        core.logging_utils._CONFIGURED = False
        os.environ["LOG_LEVEL"] = "DEBUG"
        logger = get_logger("debug_test")
        self.assertEqual(logger.getEffectiveLevel(), logging.DEBUG)
        os.environ.pop("LOG_LEVEL", None)

    def test_get_logger_invalid_level(self):
        from core.logging_utils import get_logger
        import core.logging_utils
        core.logging_utils._CONFIGURED = False
        os.environ["LOG_LEVEL"] = "INVALID_LEVEL"
        logger = get_logger("invalid_test")
        # Should fall back to INFO
        self.assertEqual(logger.getEffectiveLevel(), logging.INFO)
        os.environ.pop("LOG_LEVEL", None)

    def test_get_logger_warning_level(self):
        from core.logging_utils import get_logger
        import core.logging_utils
        core.logging_utils._CONFIGURED = False
        os.environ["LOG_LEVEL"] = "WARNING"
        logger = get_logger("warning_test")
        self.assertEqual(logger.getEffectiveLevel(), logging.WARNING)
        os.environ.pop("LOG_LEVEL", None)

    def test_get_logger_multiple_calls_same_configuration(self):
        from core.logging_utils import get_logger
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        # Both should be configured
        self.assertIsInstance(logger1, logging.Logger)
        self.assertIsInstance(logger2, logging.Logger)
        self.assertNotEqual(logger1.name, logger2.name)

    def test_get_logger_configuration_only_once(self):
        from core.logging_utils import get_logger
        import core.logging_utils
        logger1 = get_logger("first")
        # _CONFIGURED should be True now
        self.assertTrue(core.logging_utils._CONFIGURED)
        # Get another logger
        logger2 = get_logger("second")
        # Should still be configured
        self.assertTrue(core.logging_utils._CONFIGURED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
