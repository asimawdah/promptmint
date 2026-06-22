import unittest

from promptpack.tokens import estimate_tokens


class EstimateTokensTest(unittest.TestCase):
    def test_estimate_tokens_is_roughly_one_token_per_four_characters_minimum_one(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens("abcde"), 2)


if __name__ == "__main__":
    unittest.main()
