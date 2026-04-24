import unittest
from pathlib import Path
from src.domain.sanitizer import Sanitizer


class TestSanitizer(unittest.TestCase):
    def setUp(self):
        self.sanitizer = Sanitizer()

    def test_redact_posix_paths(self):
        text = "Error in /Users/felipe/Developer/project/main.py at line 10"
        redacted = self.sanitizer.redact(text)
        self.assertIn("<ABS_PATH_REDACTED>", redacted)
        self.assertNotIn("/Users/felipe", redacted)

    def test_redact_windows_paths(self):
        text = "File C:\\Users\\Admin\\AppData\\Local\\Temp\\log.txt not found"
        redacted = self.sanitizer.redact(text)
        self.assertIn("<ABS_PATH_REDACTED>", redacted)
        self.assertNotIn("C:\\Users\\Admin", redacted)

    def test_redact_secrets(self):
        text = "Connecting with api_key=FAKEKEY_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        redacted = self.sanitizer.redact(text)
        self.assertIn("***REDACTED***", redacted)
        self.assertNotIn("FAKEKEY_XXXXXXX", redacted)

    def test_redact_emails(self):
        text = "Contact support@trifecta.io for help"
        redacted = self.sanitizer.redact(text)
        self.assertIn("***@***.***", redacted)
        self.assertNotIn("support@trifecta.io", redacted)

    def test_sanitize_dict(self):
        data = {
            "path": "/Users/felipe/repo",
            "metadata": {
                "user_email": "felipe@example.com",
                "nested": ["/home/runner/work", "normal_string"]
            },
            "token": "secret_token_1234567890abcdef12345"
        }
        sanitized = self.sanitizer.sanitize_dict(data)
        self.assertEqual(sanitized["path"], "<ABS_PATH_REDACTED>")
        self.assertEqual(sanitized["metadata"]["user_email"], "***@***.***")
        self.assertEqual(sanitized["metadata"]["nested"][0], "<ABS_PATH_REDACTED>")
        self.assertEqual(sanitized["token"], "***REDACTED***")

if __name__ == "__main__":
    unittest.main()
