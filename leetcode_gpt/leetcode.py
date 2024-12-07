import requests
from typing import Optional, Tuple, Dict, Any

class LeetCode:
    def __init__(self, csrf_token: str = None, session_id: str = None):
        """
        Initialize LeetCode API client with authentication.
        
        Args:
            csrf_token (str): CSRF token for authentication
            session_id (str): Session ID for authentication
        """
        self.base_url = "https://leetcode.com"
        self.graphql_endpoint = f"{self.base_url}/graphql"
        self.session = requests.Session()
        
        if not csrf_token or not session_id:
            raise ValueError("Both csrf_token and session_id must be provided")

        self.csrf_token = csrf_token
        self.session_id = session_id

    def _authenticate_request(self, headers: Dict[str, str], referer: str) -> Dict[str, str]:
        """
        Add authentication headers to the request
        
        Args:
            headers: Base headers to authenticate
            referer: Referer URL for the request
            
        Returns:
            dict: Updated headers with authentication
        """
        
        cookie = f"LEETCODE_SESSION={self.session_id}; csrftoken={self.csrf_token}"
        
        auth_headers = {
            "Cookie": cookie,
            "x-csrftoken": self.csrf_token,
            "Referer": referer,
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Type": "application/json"
        }
        
        headers.update(auth_headers)
        return headers

    def submit(self, problem_slug: str, code: str, language: str = "python3") -> Dict[str, Any]:
        """
        Submit a solution to a LeetCode problem.
        
        Args:
            problem_slug (str): The problem's slug/title (e.g., "two-sum")
            code (str): The solution code to submit
            language (str): Programming language (default: "python3")
            
        Returns:
            dict: Submission result containing status and details
        """
        try:
            question_id = self._get_question_id(problem_slug)
            submission_url = f"{self.base_url}/problems/{problem_slug}/submit/"
            
            payload = {
                "question_id": str(question_id),
                "lang": language,
                "typed_code": code
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
            
            headers = self._authenticate_request(headers, submission_url)
            
            response = self.session.post(
                submission_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            try:
                result = response.json()
                
                if isinstance(result, dict) and "error" in result:
                    raise Exception(f"Submission error: {result['error']}")
                    
                return result
                
            except requests.exceptions.JSONDecodeError:
                raise Exception("Failed to parse response as JSON")
                
        except Exception as e:
            raise Exception(f"Failed to submit solution: {str(e)}")

    def _get_question_id(self, problem_slug: str) -> int:
        """
        Get the question ID from the problem slug using GraphQL.
        
        Args:
            problem_slug (str): The problem's slug/title
            
        Returns:
            int: The question ID
        """
        query = """
        query getQuestionDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                questionFrontendId
                title
                titleSlug
            }
        }
        """
        
        variables = {
            "titleSlug": problem_slug
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        
        headers = self._authenticate_request(headers, self.base_url)
        
        try:
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = self.session.post(
                self.graphql_endpoint,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                error_messages = [error.get("message", "Unknown error") for error in data["errors"]]
                raise Exception(f"GraphQL errors: {'; '.join(error_messages)}")
                
            question = data.get("data", {}).get("question", {})
            return int(question.get("questionId"))
            
        except Exception as e:
            raise Exception(f"Failed to get question ID: {str(e)}")

    def verify_auth_credentials(self) -> Tuple[bool, Optional[str]]:
        """
        Verify authentication credentials are valid.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            query = """
            query {
                userStatus {
                    userId
                    isSignedIn
                }
            }
            """
            
            headers = {
                "Content-Type": "application/json",
            }
            headers = self._authenticate_request(headers, self.base_url)
            
            response = self.session.post(
                self.graphql_endpoint,
                json={"query": query},
                headers=headers
            )
            
            if response.status_code != 200:
                return False, f"Authentication failed with status {response.status_code}"
                
            data = response.json()
            user_status = data.get("data", {}).get("userStatus", {})
            
            if not user_status.get("isSignedIn"):
                return False, "User is not signed in"
                
            return True, None
            
        except Exception as e:
            return False, str(e)