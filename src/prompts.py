from langchain.prompts import PromptTemplate
# --- Prompts ---

EXTRACT_MICROSERVICES_TEXT = """
You will be asked to extract a list of microservices from specifications and user stories.
Report the list in a format like this:
{ 
            name: "name1",
            description: "description of the microservice",
            user_stories: ["1"]
        }, 
        {
            name: "name2",
            description: "description of the microservice",
            user_stories: ["2", "3"]
        }
},

The context is:
Specifications:
--------------------
{{specs}}
--------------------
User Stories:
--------------------
{{user_stories}}
--------------------

The microservice list is:
"""

FIND_CONTEXT_TEXT = """
What are the best microservices patterns to use for this microservices list {{microservices_list}} given these user stories: {{user_stories}} and descriptions:{{specs}}?
Only these patterns are allowed: Communication style patterns (shared database, database per service) and Data style patterns (api composition, cqrs, saga, aggregate, event sourcing, domain event) and DO NOT USE OTHER PATTERNS.
"""

USE_CONTEXT_TEXT = """
Given a microservice list, text specifications and user stories of a software,
use context to find the best implementation pattern for each microservice. Not all microservices will have an implementation pattern.
Include an explaination on what source made you make a certain choice.
For every microservice, include the following information:
- Name of the microservice
- Endpoints with their inputs and outputs (specify the RESTful methods) 
- Parameters of the microservice (what status variables are used in the microservice)
- Description of the microservice
- User stories implemented by this microservice (All user stories must be implemented across the microservices)
Only these patterns are allowed: Communication style patterns (shared database, database per service) and Data style patterns (api composition, cqrs, saga, aggregate, event sourcing, domain event) and DO NOT USE OTHER PATTERNS.
Make sure to include all necessary endpoints and parameters in microservices, even if not explicitly mentioned in the user stories or specifications.
Find also which microservices require a datastore and provide a brief description of it by saying what user stories influenced your choices. Keep in mind what pattern require what kind of dataset.
Note that the microservices can be grouped together in a pattern, so you can have a microservice that is part of a pattern and not have any endpoints.
Note also that every microservice/pattern should have a database associated with it, even if it is not explicitly mentioned in the user stories or specifications.
Make the database association coherent with the microservices and patterns.

Output data in a json format like this and add no other text:

{
    microservices: [
        {
            name: "login_service",
            endpoints: [
                { 
                    name: "/login",
                    inputs: ["email", "password"],
                    method: "POST",
                    outputs: ["login result"],
                    description: "takes user email and password as inputs and outputs the login result"
                }, 
                {
                    name:"/register",
                    inputs: ["email", "password"],
                    method: "POST",
                    outputs: ["registration result"],
                    description: "takes user email and password as inputs and outputs the registration result"
                }
            ],
            parameters: [
                "email",
                "password"
            ],
            description: "description of the microservice",
            user_stories: ["2", "3"]
        },
    ],
    patterns: [
            {
                group_name : "meaningful name",
                implementation_pattern: "saga",
                involved_microservices: ["name1", "name2"],
                explaination: "I chose this pattern because..."
                
            },
            {
                group_name : "meaningful name2",
                implementation_pattern: "api gateway",
                involved_microservices: ["name3"],
                explaination: "I chose this pattern because..."
            }
    ],
    datastore: [
            {
                datastore_name: "meaningful name",
                associated_microservice: "name3",
                description: "desc"
            },
    ]

}



The context is:

Retrieved Context
--------------------
{{context}}
--------------------

Microservice List
--------------------
{{microservice_list}}
--------------------

Specifications:
--------------------
{{specs}}
--------------------

User Stories:
--------------------
{{user_stories}}
--------------------

The output json is:
"""


JUDGE_TEXT = """
You are an expert in software architecture and microservices design. You will be asked to evaluate the output of a microservices architecture generation process.
Given a microservice list, text specifications and user stories of a software,
you will be given context to evaluate a json output of a microservices architecture generation process.

The json will be in this format:
{
    microservices: [
        {
            name: "login_service",
            endpoints: [
                { 
                    name: "/login",
                    inputs: ["email", "password"],
                    method: "POST",
                    outputs: ["login result"],
                    description: "takes user email and password as inputs and outputs the login result"
                }, 
                {
                    name:"/register",
                    inputs: ["email", "password"],
                    method: "POST",
                    outputs: ["registration result"],
                    description: "takes user email and password as inputs and outputs the registration result"
                }
            ],
            parameters: [
                "email",
                "password"
            ],
            description: "description of the microservice",
            user_stories: ["2", "3"]
        },
    ],
    patterns: [
            {
                group_name : "meaningful name",
                implementation_pattern: "saga",
                involved_microservices: ["name1", "name2"],
                explaination: "I chose this pattern because..."
                
            },
            {
                group_name : "meaningful name2",
                implementation_pattern: "api gateway",
                involved_microservices: ["name3"],
                explaination: "I chose this pattern because..."
            }
    ],
    datastore: [
            {
                datastore_name: "meaningful name",
                associated_microservice: "name3",
                description: "desc"
            },
    ]

}


The output will be a json object with the following fields that for every pattern in the input json will contain a boolean value and an explanation:
- "is_correct": true if the pattern is correct, false otherwise
- "explanation": a string explaining why the pattern is correct or not .
E.g.:
{
    microservices: [    
        {
            name: "login_service",
            is_correct: true,
            explanation: "The microservice is correct because it has all the necessary endpoints and parameters, and it implements the user stories correctly."
        },
    ],
}

The context is:

Retrieved Context
--------------------
{{context}}
--------------------

Microservice Json Input
--------------------
{{microservice_list}}
--------------------

Specifications:
--------------------
{{specs}}
--------------------

User Stories:
--------------------
{{user_stories}}
--------------------

The output json is:
"""

