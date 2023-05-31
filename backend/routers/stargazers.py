from fastapi import APIRouter, Depends, HTTPException
import os
import pandas as pd
from typing import List, Optional

router = APIRouter()

# Represents a single data point that contains the number of stars at a single point in time.
class Starpoint:
    def __init__(self, year: int, month: int, total_stars: int) -> None:
        self.year = year
        self.month = month
        self.total_stars = total_stars
    
    @property
    def __dict__(self):
        return {
            "year": self.year, 
            "month": self.month, 
            "total_stars": self.total_stars
        }

# Represents a single GitHub project that contains the official project name, the total number of stars, and all of the data points that represents the number of stars at each month 
class GitHub_Project:
    def __init__(self, project_name: str, number_of_stars:int, starpoints: List[Starpoint]) -> None:
        self.project_name = project_name
        self.number_of_stars = number_of_stars
        self.starpoints = starpoints

# Response_Provider is an abstract base class to allow various data providers to conform to this interface.
# This allows us to easily swap out the data provider without having to change the code that uses the data provider.
# Furthermore, it allows us to test the behaviors of the code that uses the data provider without having to use the actual data provider.
class Response_Provider:
    def __init__(self):
        pass
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        pass

# GitHub_Response_Provider is a concrete implementation of Response_Provider that uses the GitHub API to fetch the data.
# Currently, it uses a local CSV file to store the data, but it can be modified to use the GitHub API instead.
class GitHub_Response_Provider(Response_Provider):
    def __init__(self):
        pass

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        try:
            dir_path: str = os.path.dirname(os.path.realpath(__file__))
            dataframe_file_path: str = os.path.join(dir_path, "../datasource/github_stargazers_data.csv")
            dataframe: pd.DataFrame = pd.read_csv(dataframe_file_path)
            
            return dataframe
        except:
            return None

# Dependency Injection function that returns a Response_Provider to be used
def get_response_provider() -> Response_Provider:
    return GitHub_Response_Provider()

# This api depends on the get_response_provider function to get the Response_Provider to use.
# If we can swap out the get_response_provider at test, we can test the functionality of this api without having to use the actual GitHub API.
# Returns all of the information for a single project of GitHub
@router.get("/stargazer_data/{project_name}", tags=["stargazers project info"])
async def get_github_project_info(project_name: str, response_provider = Depends(get_response_provider)):
    dataframe: pd.DataFrame = response_provider.get_dataframe()

    # The response provider could not find any data
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Dataframe Missing")
    
    dataframe_columns: List[str] = dataframe.columns.tolist()

    # At first, check if we have all the columns we need
    if "name" not in dataframe_columns or "year" not in dataframe_columns or "month" not in dataframe_columns or "star_count_current" not in dataframe_columns:
        raise HTTPException(status_code=404, detail="Dataframe Corrupted")
    
    # Filter the data to get project specific data only
    dataframe = dataframe[dataframe["name"] == project_name]

    # Handle case where we don't have any project data
    if len(dataframe) == 0:
        raise HTTPException(status_code=404, detail="No project details")

    # Get related data for the project
    last_year: int = dataframe["year"].max()
    last_month: int = dataframe[dataframe["year"] == last_year]["month"].max()
    number_of_stars: int = dataframe[(dataframe.year == last_year) & (dataframe.month == last_month)]['star_count_current'].max()
    
    # List comprehension is shorter, but might look messy
    starpoints: List[Starpoint] = []

    for i in range(len(dataframe)):
        starpoints.append(
                    Starpoint(
                        int(dataframe.iloc[i]["year"]), 
                        int(dataframe.iloc[i]["month"]), 
                        int(dataframe.iloc[i]["star_count_current"])
                        )
                    )

    return GitHub_Project(project_name, number_of_stars, starpoints)

# This api also depends on the get_response_provider function to get the Response_Provider to use.
# Therefore, we can also swap out the actual implementation with a dummy one to test the functionality
# Returns the names of all of the projects that is available in the dataset
@router.get("/stargazer_data/", tags=["stargazers all projects"])
async def get_available_projects(response_provider = Depends(get_response_provider)):
    dataframe: pd.DataFrame = response_provider.get_dataframe()

    # The response provider could not find any data
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Dataframe Missing")

    # At first, check if we have all the columns we need
    if "name" not in dataframe.columns:
        raise HTTPException(status_code=404, detail="Dataframe Corrupted")
    
    all_project_names: List[str] = dataframe["name"].unique().tolist()

    return all_project_names