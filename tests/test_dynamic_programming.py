"""
Tests for Dynamic Programming Algorithms.
Covers Requirements:
16. Knapsack optimal value
17. LCS result
18. Matrix Chain Multiplication result
And Resource Allocation DP.
"""

import unittest
from app.dynamic_programming import (
    solve_knapsack_01,
    solve_resource_allocation,
    solve_lcs,
    solve_matrix_chain_multiplication,
)


class TestDynamicProgramming(unittest.TestCase):
    def test_16_knapsack_01_optimal_value_and_selection(self):
        """Test 16: 0/1 Knapsack optimal value and item reconstruction."""
        items = [
            {"name": "file_1.zip", "size": 10, "utility": 60},
            {"name": "file_2.zip", "size": 20, "utility": 100},
            {"name": "file_3.zip", "size": 30, "utility": 120},
        ]
        budget = 50  # Max capacity 50

        # Best combination: file_2 (20, 100) + file_3 (30, 120) = size 50, utility 220
        res = solve_knapsack_01(items, budget)

        self.assertEqual(res["optimal_value"], 220)
        self.assertEqual(res["total_selected_size"], 50)
        selected_names = {it["name"] for it in res["selected_items"]}
        self.assertEqual(selected_names, {"file_2.zip", "file_3.zip"})

    def test_17_longest_common_subsequence(self):
        """Test 17: LCS length, string reconstruction, and DP matrix."""
        s1 = "ABCBDAB"
        s2 = "BDCABA"

        res = solve_lcs(s1, s2)

        self.assertEqual(res["lcs_length"], 4)
        # Length 4 subsequences include 'BCBA', 'BDAB', etc.
        self.assertEqual(len(res["lcs_string"]), 4)

        # Check DP table dimensions (8 x 7)
        self.assertEqual(len(res["dp_table"]), len(s1) + 1)
        self.assertEqual(len(res["dp_table"][0]), len(s2) + 1)
        self.assertEqual(res["dp_table"][len(s1)][len(s2)], 4)

    def test_18_matrix_chain_multiplication(self):
        """Test 18: Matrix Chain Multiplication optimal parenthesization."""
        # Textbook standard example: dimensions [10, 30, 5, 60] -> 3 matrices
        # A1: 10x30, A2: 30x5, A3: 5x60
        # ((A1 A2) A3): 10*30*5 + 10*5*60 = 1500 + 3000 = 4500 scalar multiplications
        dimensions = [10, 30, 5, 60]

        res = solve_matrix_chain_multiplication(dimensions)

        self.assertEqual(res["minimum_multiplications"], 4500)
        self.assertEqual(res["matrix_count"], 3)
        self.assertEqual(res["optimal_parenthesization"], "((A1 × A2) × A3)")

    def test_resource_allocation_dp(self):
        """Test Resource Allocation DP."""
        activities = ["Project_A", "Project_B"]
        # Utility function for 0, 1, 2 units of budget
        utilities = [
            [0, 5, 8],  # Project A
            [0, 6, 9],  # Project B
        ]
        budget = 2

        res = solve_resource_allocation(activities, utilities, budget)

        # Best allocation: 1 to A (5) + 1 to B (6) = 11 total utility
        self.assertEqual(res["maximum_utility"], 11)
        self.assertEqual(res["allocations"]["Project_A"], 1)
        self.assertEqual(res["allocations"]["Project_B"], 1)


if __name__ == "__main__":
    unittest.main()
