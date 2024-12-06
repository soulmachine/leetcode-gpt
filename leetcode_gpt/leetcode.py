import requests

class LeetCode:
    def __init__(self, csrf_token: str = None, session_id: str = None):
        """
        Initialize LeetCode API client with authentication.
        
        Args:
            csrf_token (str): CSRF token for authentication
            session_id (str): Session ID for authentication
        """
        self.base_url = "https://leetcode.com"
        self.session = requests.Session()
        
        # Set up authentication headers and cookies
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": self.base_url,
        }
        
        if not csrf_token or not session_id:
            raise ValueError("Both csrf_token and session_id must be provided")

        self.headers["X-Csrftoken"] = csrf_token
        self.session.cookies.set("csrftoken", csrf_token)
        self.session.cookies.set("LEETCODE_SESSION", session_id)

    def submit(self, problem_slug: str, code: str, language: str = "python3") -> dict:
        """
        Submit a solution to a LeetCode problem.
        
        Args:
            problem_slug (str): The problem's slug/title (e.g., "two-sum")
            code (str): The solution code to submit
            language (str): Programming language (default: "python3")
            
        Returns:
            dict: Submission result containing status and details
        """
        endpoint = f"{self.base_url}/problems/{problem_slug}/submit/"
        
        payload = {
            "question_id": self._get_question_id(problem_slug),
            "lang": language,
            "typed_code": code,
        }

        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to submit solution: {str(e)}")

    def _get_question_id(self, problem_slug: str) -> int:
        """
        Helper method to get the question ID from the problem slug.
        Uses authenticated requests to access the API.
        
        Args:
            problem_slug (str): The problem's slug/title
            
        Returns:
            int: The question ID
        """
        endpoint = f"{self.base_url}/api/problems/{problem_slug}/"
        
        try:
            response = self.session.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("question", {}).get("id")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get question ID: {str(e)}")
