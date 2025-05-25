import unittest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch
from app.auth import create_jwt_token, decode_jwt_token

class TestAuth(unittest.TestCase):

    @patch.dict('os.environ', {'SECRET_KEY': 'test-secret'})
    def test_create_jwt_token(self):
        user_id = 123
        token = create_jwt_token(user_id)
        decoded = jwt.decode(token, 'test-secret', algorithms=['HS256'])
        self.assertEqual(decoded['sub'], user_id)

    @patch.dict('os.environ', {'SECRET_KEY': 'test-secret'})
    def test_decode_jwt_token(self):
        user_id = 456
        token = create_jwt_token(user_id)
        self.assertEqual(decode_jwt_token(token)['sub'], user_id)

        expired = jwt.encode(
            {
                'exp': datetime.utcnow() - timedelta(days=1),
                'iat': datetime.utcnow() - timedelta(days=2),
                'sub': user_id
            },
            'test-secret',
            algorithm='HS256'
        )
        self.assertIsNone(decode_jwt_token(expired))

    @patch.dict('os.environ', {'SECRET_KEY': 'test-secret'})
    def test_invalid_token(self):
        self.assertIsNone(decode_jwt_token("invalid.token.string"))

if __name__ == '__main__':
    unittest.main()
