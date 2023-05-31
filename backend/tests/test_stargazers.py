from fastapi.testclient import TestClient
from typing import List, Optional
import pandas as pd
import pytest
from requests import Response

from ..main import app 
from ..routers.stargazers import get_response_provider, Response_Provider

client = TestClient(app)

# Mock Response Class for testing that we will inject
class Mock_Response_Provider:
    def __init__(self):
        pass
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        data = [
            ["A", 2008, 3, 1, 10, 90],
            ["A", 2008, 4, 10, 20, 90],
            ["B", 2008, 3, 20, 40, 90],
            ["C", 2008, 3, 30, 50, 90]
        ]

        columns: List[str] = ["name", "year", "month", "star_count_prev", "star_count_current", "color_num"]
        df: pd.DataFrame = pd.DataFrame(data, columns=columns)

        return df

def get_mock_response_provider() -> Mock_Response_Provider:
    return Mock_Response_Provider()

# Setup and Teardown for the tests
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Inject Dependency before each test begins
    app.dependency_overrides[get_response_provider] = get_mock_response_provider
    
    yield

    # We don't have anything for the teardown now

def test_stargazers_get_available_projects():
    response: Response = client.get("/stargazer_data/")
    assert response.status_code == 200

    all_fetched_projects: List[str] = response.json()
    # From the dummy data, we should have 3 projects
    assert len(all_fetched_projects) == 3

    all_fetched_projects.sort()
    # Test if we're getting the 3 projects we're expecting
    assert all_fetched_projects == ["A", "B", "C"] 

def test_stargazers_get_project_info():
    response: Response = client.get("/stargazer_data/A")
    assert response.status_code == 200

    fetched_project: dict = response.json()

    # Test if we are getting the data for the project we're looking for
    assert fetched_project.get("project_name", "") == "A"

    # Test if we are getting the accurate data for the number of stars
    assert fetched_project.get("number_of_stars", -1) == 20

    # Test if we are getting all of the data for displaying
    assert len(fetched_project.get("starpoints", [])) == 2

def test_stargazers_get_project_info_test_invalid_data():
    # Test if we are getting correct response if we query for an invalid project
    response: Response = client.get("/stargazer_data/NotAProject")
    assert response.status_code == 404