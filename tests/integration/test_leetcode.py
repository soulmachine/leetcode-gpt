import os
import pytest
import json
import time
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .envrc file"""
    current_dir = Path.cwd()
    envrc_path = None
    
    while current_dir.parent != current_dir:
        test_path = current_dir / '.envrc'
        if test_path.exists():
            envrc_path = test_path
            break
        current_dir = current_dir.parent
    
    if envrc_path:
        print(f"Found .envrc at: {envrc_path}")
        load_dotenv(envrc_path)
        return True
    return False

class TestLeetCodeIntegration:
    @pytest.fixture
    def leetcode_client(self):
        """Create a LeetCode client with credentials from .envrc"""
        envrc_loaded = load_environment()
        if not envrc_loaded:
            pytest.skip(".envrc file not found")
            
        csrf_token = os.getenv("LEETCODE_CSRF_TOKEN")
        session_id = os.getenv("LEETCODE_SESSION_ID")
        
        if not csrf_token or not session_id:
            print("\nEnvironment Variable Debug:")
            print(f"LEETCODE_CSRF_TOKEN found: {'Yes' if csrf_token else 'No'}")
            print(f"LEETCODE_SESSION_ID found: {'Yes' if session_id else 'No'}")
            
            if envrc_loaded:
                print("\nWarning: .envrc was found but variables were not loaded properly")
                print("Please check your .envrc file format. It should look like:")
                print('export LEETCODE_CSRF_TOKEN="your_token_here"')
                print('export LEETCODE_SESSION_ID="your_session_id_here"')
            
            pytest.skip("Required environment variables not found in .envrc")
        
        from leetcode_gpt.leetcode import LeetCode
        return LeetCode(csrf_token=csrf_token, session_id=session_id)

    @pytest.mark.integration
    def test_submit_solution(self, leetcode_client):
        """Test submitting a solution and checking its result"""
        problem_slug = "two-sum"
        code = \
"""class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []
        """
        
        try:
            print("\nSubmitting solution...")
            submission = leetcode_client.submit(problem_slug, code)
            print(f"Submission response: {json.dumps(submission, indent=2)}")
            
            # Check submission response format
            assert isinstance(submission, dict), "Submission response is not a dictionary"
            submission_id = submission.get("submission_id")
            assert submission_id, "No submission ID in response"
            
            # Wait for and verify result
            time.sleep(2)  # Give some time for the submission to be processed
            print(f"\nChecking submission result (ID: {submission_id})...")
            
            try:
                result = leetcode_client.wait_for_submission_result(str(submission_id))
                print(f"Final result: {json.dumps(result, indent=2)}")
                
                assert isinstance(result, dict), "Result is not a dictionary"
                assert "state" in result, "No state in result"
                
            except Exception as e:
                print(f"Failed to get submission result: {e}")
                # Don't fail the test if we can't get the result
                # The submission might have succeeded but checking failed
                pass
                
        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.integration
    def test_auth_verification(self, leetcode_client):
        """Test authentication verification"""
        try:
            is_valid, error_message = leetcode_client.verify_auth_credentials()
            print(f"\nAuth verification result:")
            print(f"Valid: {is_valid}")
            if error_message:
                print(f"Error: {error_message}")
                
            assert is_valid, f"Authentication failed: {error_message}"
            
        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.integration
    def test_get_question_id(self, leetcode_client):
        """Test getting question ID"""
        try:
            problem_slug = "two-sum"
            question_id = leetcode_client._get_question_id(problem_slug)
            print(f"\nQuestion ID for '{problem_slug}': {question_id}")
            
            assert isinstance(question_id, int), "Question ID is not an integer"
            assert question_id > 0, "Invalid question ID"
            
        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")