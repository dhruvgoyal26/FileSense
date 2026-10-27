"""
Dynamic Programming Implementations for DSA-II PBL Requirements.
Includes:
1. 0/1 Knapsack for Storage Cleanup Optimization
2. Resource Allocation DP
3. Longest Common Subsequence (LCS) with DP Table
4. Matrix Chain Multiplication (MCM) with Parenthesization
"""

import time
from typing import Dict, List, Tuple, Any, Optional


# ==========================================================
# 1. 0/1 Knapsack for Storage Cleanup
# ==========================================================

def solve_knapsack_01(
    items: List[Dict[str, Any]],
    budget: int,
) -> Dict[str, Any]:
    """
    0/1 Knapsack Dynamic Programming for Storage Cleanup Recommendation.
    
    State:
        dp[i][w] = Maximum utility achievable considering items 1..i with weight limit w.
    
    Recurrence:
        dp[i][w] = dp[i-1][w]                                    if weight[i-1] > w
        dp[i][w] = max(dp[i-1][w], dp[i-1][w - weight[i-1]] + val[i-1]) otherwise
        
    Base Case:
        dp[0][w] = 0 for all w
        dp[i][0] = 0 for all i
        
    Args:
        items: List of dicts, each having {'name': str, 'size': int, 'utility': int, 'metadata': dict}
        budget: Maximum storage capacity or target cleanup limit
        
    Returns:
        Dict with selected_items, total_weight, total_utility, execution_time_ms, and compact table.
    """
    start_time = time.perf_counter()
    n = len(items)
    W = max(0, int(budget))

    # Scale down budget/weights if numbers are enormous (e.g. gigabytes)
    # to maintain O(n * W) tractability for interactive DP display
    scale_factor = 1
    if W > 5000:
        scale_factor = max(1, W // 500)
        scaled_W = W // scale_factor
        scaled_weights = [max(1, it["size"] // scale_factor) for it in items]
    else:
        scaled_W = W
        scaled_weights = [max(0, it["size"]) for it in items]

    values = [it.get("utility", 1) for it in items]

    # Initialize DP table (n + 1) x (scaled_W + 1)
    dp = [[0] * (scaled_W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        wt = scaled_weights[i - 1]
        val = values[i - 1]
        for w in range(scaled_W + 1):
            if wt <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - wt] + val)
            else:
                dp[i][w] = dp[i - 1][w]

    # Traceback to reconstruct selected items
    selected_indices: List[int] = []
    curr_w = scaled_W
    for i in range(n, 0, -1):
        if dp[i][curr_w] != dp[i - 1][curr_w]:
            selected_indices.append(i - 1)
            curr_w -= scaled_weights[i - 1]

    selected_indices.reverse()
    selected_items = [items[idx] for idx in selected_indices]
    total_selected_size = sum(it["size"] for it in selected_items)
    total_selected_utility = sum(it.get("utility", 1) for it in selected_items)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "algorithm": "0/1 Knapsack Dynamic Programming",
        "budget": budget,
        "scaled_budget": scaled_W,
        "scale_factor": scale_factor,
        "item_count": n,
        "selected_items": selected_items,
        "selected_count": len(selected_items),
        "total_selected_size": total_selected_size,
        "total_selected_utility": total_selected_utility,
        "optimal_value": dp[n][scaled_W],
        "execution_time_ms": elapsed_ms,
        "dp_table_sample": [row[:min(15, scaled_W + 1)] for row in dp[:min(10, n + 1)]],
    }


# ==========================================================
# 2. Resource Allocation DP
# ==========================================================

def solve_resource_allocation(
    activities: List[str],
    utility_functions: List[List[int]],
    total_budget: int,
) -> Dict[str, Any]:
    """
    Resource Allocation DP:
    Allocate an integer total_budget among N activities to maximize total return.
    utility_functions[i][b] = utility of allocating b units of resource to activity i.
    """
    start_time = time.perf_counter()
    n = len(activities)
    B = max(0, total_budget)

    # dp[i][b] = max utility from first i activities with budget b
    dp = [[0] * (B + 1) for _ in range(n + 1)]
    # allocation choice table
    choice = [[0] * (B + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for b in range(B + 1):
            max_val = 0
            best_alloc = 0
            # Try allocating x units (0 <= x <= b) to activity i - 1
            for x in range(b + 1):
                val = utility_functions[i - 1][x] if x < len(utility_functions[i - 1]) else 0
                candidate = dp[i - 1][b - x] + val
                if candidate >= max_val:
                    max_val = candidate
                    best_alloc = x
            dp[i][b] = max_val
            choice[i][b] = best_alloc

    # Traceback
    allocations = {}
    curr_b = B
    for i in range(n, 0, -1):
        alloc = choice[i][curr_b]
        allocations[activities[i - 1]] = alloc
        curr_b -= alloc

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "algorithm": "Resource Allocation DP",
        "total_budget": B,
        "activities": activities,
        "allocations": allocations,
        "maximum_utility": dp[n][B],
        "execution_time_ms": elapsed_ms,
    }


# ==========================================================
# 3. Longest Common Subsequence (LCS)
# ==========================================================

def solve_lcs(str1: str, str2: str) -> Dict[str, Any]:
    """
    Longest Common Subsequence (LCS) Dynamic Programming.
    Used for text similarity analysis between text snippets.
    
    Recurrence:
        L[i][j] = L[i-1][j-1] + 1                     if X[i-1] == Y[j-1]
        L[i][j] = max(L[i-1][j], L[i][j-1])          otherwise
        
    Complexity: O(m * n) time, O(m * n) space.
    """
    start_time = time.perf_counter()
    m = len(str1)
    n = len(str2)

    # Initialize (m + 1) x (n + 1) table
    L = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                L[i][j] = L[i - 1][j - 1] + 1
            else:
                L[i][j] = max(L[i - 1][j], L[i][j - 1])

    # Traceback to reconstruct the LCS string
    lcs_chars = []
    i, j = m, n
    while i > 0 and j > 0:
        if str1[i - 1] == str2[j - 1]:
            lcs_chars.append(str1[i - 1])
            i -= 1
            j -= 1
        elif L[i - 1][j] >= L[i][j - 1]:
            i -= 1
        else:
            j -= 1

    lcs_chars.reverse()
    lcs_string = "".join(lcs_chars)
    lcs_len = L[m][n]

    # Calculate similarity ratio
    sim_ratio = (2.0 * lcs_len / (m + n)) if (m + n) > 0 else 1.0

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "algorithm": "Longest Common Subsequence (LCS)",
        "str1": str1,
        "str2": str2,
        "len1": m,
        "len2": n,
        "lcs_length": lcs_len,
        "lcs_string": lcs_string,
        "similarity_ratio": sim_ratio,
        "dp_table": L,
        "execution_time_ms": elapsed_ms,
        "complexity": "Time: O(m * n), Space: O(m * n)",
    }


# ==========================================================
# 4. Matrix Chain Multiplication (MCM)
# ==========================================================

def solve_matrix_chain_multiplication(dimensions: List[int]) -> Dict[str, Any]:
    """
    Matrix Chain Multiplication DP for finding optimal parenthesization.
    
    Given chain <A1, A2, ..., An> where matrix Ai has dimension p[i-1] x p[i].
    
    Recurrence:
        m[i, j] = 0                                       if i == j
        m[i, j] = min_{i <= k < j} (m[i, k] + m[k+1, j] + p[i-1]*p[k]*p[j])
        
    Complexity: O(n^3) time, O(n^2) space.
    """
    start_time = time.perf_counter()
    n = len(dimensions) - 1
    if n < 1:
        raise ValueError("Need at least 2 dimensions to define matrices.")

    # 1-indexed tables of size (n + 1) x (n + 1)
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # l is chain length (from 2 to n)
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float("inf")
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + (dimensions[i - 1] * dimensions[k] * dimensions[j])
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    # Traceback optimal parenthesization
    def _build_parentheses(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = _build_parentheses(i, k)
        right = _build_parentheses(k + 1, j)
        return f"({left} × {right})"

    optimal_parens = _build_parentheses(1, n)
    min_cost = int(m[1][n])

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "algorithm": "Matrix Chain Multiplication (MCM)",
        "matrix_count": n,
        "dimensions": dimensions,
        "minimum_multiplications": min_cost,
        "optimal_parenthesization": optimal_parens,
        "cost_table": m,
        "split_table": s,
        "execution_time_ms": elapsed_ms,
        "complexity": "Time: O(n^3), Space: O(n^2)",
    }
