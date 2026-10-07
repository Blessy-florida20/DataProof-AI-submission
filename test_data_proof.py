import unittest

from data_proof import analyze_data


class DataProofTests(unittest.TestCase):
    def test_expected_answers(self):
        results = analyze_data("data")
        self.assertEqual(results["Q1"], 2)
        self.assertEqual(results["Q2"], 20)
        self.assertEqual(results["Q3"], 596330.0)
        self.assertEqual(results["Q4"], 297730.0)
        self.assertEqual(results["Q5"], "Laptop")
        self.assertEqual(results["Q6"], 248450.0)
        self.assertEqual(results["Q7"], 2)
        self.assertEqual(results["Q8"], "AMBIGUOUS")
        self.assertEqual(results["Q9"], "CANNOT_DETERMINE")
        self.assertEqual(results["Q10"], "CANNOT_DETERMINE")


if __name__ == "__main__":
    unittest.main()
