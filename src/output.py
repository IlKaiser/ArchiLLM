from typing import List
from pydantic import BaseModel, Field

class MicroserviceEndpoint(BaseModel):
    """Model for an endpoint of a microservice."""
    name: str = Field(..., description="Name of the endpoint")
    method: str = Field(..., description="HTTP method used by the endpoint (e.g., GET, POST)")
    inputs: List[str] = Field(default_factory=list, description="List of input parameters for the endpoint")
    outputs: List[str] = Field(default_factory=list, description="List of output parameters for the endpoint")
    description: str = Field(..., description="Description of what the endpoint does")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the endpoint."""
        return {
            "name": self.name,
            "inputs": self.inputs,
            "method": self.method,
            "outputs": self.outputs,
            "description": self.description
        }
class Microservice(BaseModel):
    """Model for a microservice in the architecture."""
    name: str = Field(..., description="Name of the microservice")
    endpoints: List[MicroserviceEndpoint] = Field(default_factory=list, description="List of endpoints with their descriptions")
    user_stories: List[str] = Field(default_factory=list, description="List of user stories implemented by this microservice")
    parameters: List[str] = Field(default_factory=list, description="Parameters of the microservice")
    description: str = Field(..., description="Brief description of the microservice and its purpose")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the microservice."""
        return {
            "name": self.name,
            "endpoints": self.endpoints,
            "user_stories": self.user_stories,
            "parameters": self.parameters,
            "description": self.description
        }
class Pattern(BaseModel):
    """Model for a microservices pattern in the architecture."""
    group_name: str = Field(..., description="Meaningful name for the pattern group")
    implementation_pattern: str = Field(..., description="Implementation pattern used (e.g., saga, api gateway)")
    involved_microservices: List[str] = Field(..., description="List of microservices involved in this pattern")
    explaination: str = Field(..., description="Explanation of why this pattern was chosen")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the pattern."""
        return {
            "group_name": self.group_name,
            "implementation_pattern": self.implementation_pattern,
            "involved_microservices": self.involved_microservices,
            "explaination": self.explaination
        }
class Dataset(BaseModel):
    """Model for a dataset used in the architecture."""
    datastore_name: str = Field(..., description="Meaningful name for the dataset")
    associated_microservices: List[str] = Field(..., description="Microservices associated with this dataset")
    description: str = Field(..., description="Brief description of the dataset and its purpose")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the dataset."""
        return {
            "datastore_name": self.datastore_name,
            "associated_microservices": self.associated_microservices,
            "description": self.description
        }  
class DalleOutput(BaseModel):
    """Output model for the Dalle workflow."""
    microservices: List[Microservice] = Field(..., description="List of microservices in the architecture")
    patterns: List[Pattern] = Field(..., description="List of patterns used in the architecture")
    datastore: List[Dataset] = Field(..., description="List of datasets used in the architecture")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the output."""
        return {
            "microservices": [ms.__dict__() for ms in self.microservices],
            "patterns": [pattern.__dict__() for pattern in self.patterns],
            "datasets": [dataset.__dict__() for dataset in self.datasets]
        }

