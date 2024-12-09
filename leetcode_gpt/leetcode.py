from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import time
import logging


# Some leetcode problem slugs are not good names, need to map to more readable ones
PROBLEM_SLUG_MAPPING = {
    "merge-two-sorted-arrays": "merge-sorted-array",
}

class LeetCode:
    def __init__(self, csrf_token: str, session_id: str):
        """
        Initialize LeetCode API client with authentication.

        Args:
            csrf_token (str): CSRF token for authentication
            session_id (str): Session ID for authentication
        """
        if not csrf_token or not session_id:
            raise ValueError("Both csrf_token and session_id must be provided")

        self.base_url = "https://leetcode.com"
        self.session = requests.Session()

        # Retry strategy for transient errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        # Set authentication headers and cookies
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": self.base_url,
            "X-Csrftoken": csrf_token,
        }
        self.session.cookies.set("csrftoken", csrf_token)
        self.session.cookies.set("LEETCODE_SESSION", session_id)

        # Validate authentication
        self._validate_authentication()

    def _validate_authentication(self):
        """Check if the CSRF token and session ID are valid."""
        endpoint = f"{self.base_url}/graphql"
        payload = {
            "query": "{ user { username } }"
        }
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError("Invalid csrf_token or session_id") from e


    def get_question_id(self, problem_slug: str) -> Optional[int]:
        """Retrieve the question ID from the problem slug using GraphQL."""
        problem_slug = PROBLEM_SLUG_MAPPING.get(problem_slug, problem_slug)
        endpoint = f"{self.base_url}/graphql"
        query = {
            "query": """
                query getQuestionId($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        questionId
                    }
                }
            """,
            "variables": {"titleSlug": problem_slug},
        }
        response = self.session.post(endpoint, json=query, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        tmp = data.get("data", {}).get("question")
        if not tmp: # data can be: {'data': {'question': None}}
            return None
        question_id = tmp.get("questionId")
        return int(question_id) if question_id else None

    def submit(self, problem_slug: str, code: str, language: str = "python3") -> str:
        """Submit a solution to a LeetCode problem and return the submission ID."""
        problem_slug = PROBLEM_SLUG_MAPPING.get(problem_slug, problem_slug)
        question_id = self.get_question_id(problem_slug)
        if not question_id:
            raise ValueError(f"Invalid problem slug '{problem_slug}'.")

        endpoint = f"{self.base_url}/problems/{problem_slug}/submit/"
        payload = {"question_id": question_id, "lang": language, "typed_code": code}
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()["submission_id"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to submit solution: {str(e)}")

    def check_submission(self, submission_id: int, max_retries: int = 10, retry_delay: float = 2.0) -> dict:
        """Check the status of a submitted solution.

        Args:
            submission_id: The submission ID to check
            max_retries: Maximum number of retries for pending submissions
            retry_delay: Delay between retries in seconds

        Returns:
            dict: Submission result containing status, runtime, memory usage, etc.

        Raises:
            TimeoutError: If submission takes too long to process
            Exception: If submission check fails
        """
        endpoint = f"{self.base_url}/submissions/detail/{submission_id}/check/"
        retries = 0

        while retries < max_retries:
            try:
                response = self.session.get(endpoint, headers=self.headers)
                response.raise_for_status()

                result = response.json()
                status = result.get('state')

                if status in ['SUCCESS', 'FAILED']:
                    return result

                if status in ['PENDING', 'STARTED']:
                    retries += 1
                    time.sleep(retry_delay)
                    continue

                raise Exception(f"Unknown submission status: {status}")

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {str(e)}")
                retries += 1
                time.sleep(retry_delay)

        raise TimeoutError(f"Submission check timed out after {max_retries} retries")
