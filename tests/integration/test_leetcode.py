import os
import pytest
from leetcode_gpt.leetcode import LeetCode

class TestLeetCodeIntegration:
    @pytest.fixture
    def leetcode_client(self):
        """Create a LeetCode client with real credentials from environment variables"""
        csrf_token = os.getenv("LEETCODE_CSRF_TOKEN")
        session_id = os.getenv("LEETCODE_SESSION_ID")
        
        if not csrf_token or not session_id:
            pytest.skip("LEETCODE_CSRF_TOKEN and LEETCODE_SESSION_ID environment variables are required")
        
        return LeetCode(csrf_token=csrf_token, session_id=session_id)
    
    @pytest.mark.integration
    def test_submit_solution(self, leetcode_client):
        """Test submitting a real solution to LeetCode"""
        problem_slug = "two-sum"
        code = """
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        indices = {}
        for i, num in enumerate(nums):
            rest = target - num
            if rest in indices:
                return [indices[rest], i]
            indices[num] = i
        """

        # Get question ID first (for debugging)
        question_id = leetcode_client._get_question_id(problem_slug)
        print(f"Question ID: {question_id}")

        # Submit solution
        result = leetcode_client.submit(problem_slug, code)
        print(f"Submission result: {result}")

        # Updated assertions based on the actual response structure
        assert result is not None
        assert isinstance(result, int)
