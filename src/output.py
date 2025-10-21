from typing import List, Any
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

"""
folders: [
        {
            name: "login_service",
            folders: [],
            files: [
                {
                    name: "LoginService.java",
                    content: "public class LoginService { ... }"
                },
                {
                    name: "RegisterService.java",
                    content: "public class RegisterService { ... }"
                }
            ]
        },
    ],
    files: [
        {
            name: "README.md",
            content: "This is the README file for the project."
        },
        {
            name: "pom.xml",
            content: "<project> ... </project>"
    ] 
"""
class File(BaseModel):
    """Model for a file in the code generation output."""
    name: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Content of the file")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the file."""
        return {
            "name": self.file_path,
            "content": self.content
        }
class Folder(BaseModel):
    """Model for a folder in the code generation output."""
    name: str = Field(..., description="Path of the folder")
    folders: List['Folder'] = Field(..., description="List of subfolders in the folder")
    files: List[File] = Field(..., description="List of files in the folder")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the folder."""
        return {
            "name": self.name,
            "folders": [folder.__dict__() for folder in self.folders],
            "files": [file.__dict__() for file in self.files],
        }

class DalleOutputCode2(BaseModel):
    """Output model for the Dalle workflow."""
    code : Any



class DalleOutputCode(BaseModel):
    """Output model for the Dalle workflow."""
    folders: List[Folder] = Field(..., description="List of folders in the generated code")
    files: List[File] = Field(..., description="List of files in the generated code")

    def __dict__(self, *args, **kwargs):
        """Override dict method to return a dictionary representation of the output."""
        return {
            "folders": [folder.__dict__() for folder in self.folders],
            "files": [file.__dict__() for file in self.files],
        }