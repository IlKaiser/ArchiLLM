from typing import Any
from pydantic import BaseModel
from llama_index.core.workflow.events import Event

# --- Workflow Events ---

class MicroservicesCodeExtractedEvent(Event):
    """Get list of microservices from specs and user stories"""
    microservices_list: Any

class PatternsCodeGeneratedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    patterns: Any

class DatastoreCodeGeneratedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    datastore: Any

class FrontendCodeGeneratedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    frontend: Any

class ComposeCodeGeneratedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    code: Any

class ExtractMicroservice(Event):
    microservice: Any

