# --- Prompts ---

# Prompt for microservices extraction agent (1)
EXTRACT_MICROSERVICES_TEXT = """
Imagine you are a software architect expert in microservices design, and you are designing a small scale new system.
You will be asked to extract a list of microservices from specifications and user stories.
Keep the microservices as small and focused as possible, trying to include the minimum number of microservices.
Report the list in a format like this:
{       
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

# Prompt for context retrieval agent (3)
FIND_CONTEXT_TEXT = """
What are the best microservices patterns to use for this microservices list {{microservices_list}} given these user stories: {{user_stories}} and descriptions:{{specs}}?
Only these patterns are allowed: Communication style patterns (shared database, database per service) and Data style patterns (api composition, cqrs, saga, aggregate, event sourcing, domain event) and DO NOT USE OTHER PATTERNS.
"""

# Prompt for output parsing agent (4)
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
Keep the patterns to the minimum necessary to have a coherent microservices architecture, not all services need to have a pattern.
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

GENERATE_CODE_TEXT = """
You are an expert software developer. You will be asked to generate java code for a list of microservices based on a given json architecture.
Given a microservice list in json format, generate code snippets for each microservice based on the architecture.
You are implementing a microservices architecture in Java with Spring Boot. Add a simple frontend to test the microservices.
Create the proper Dockerfile and docker-compose.yml files to deploy the microservices in the indicated patterns.
Add to the Readme.md file a simple explanation of the microservices implemented with the patterns used.
Output files in a json format like this and add no other text:
{
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
        {
            name: "user_service",
            folders: [],
            files: [
                {
                    name: "UserService.java",
                    content: "public class UserService { ... }"
                }
            ]
        }
    ],
    files: [
        {
            name: "README.md",
            content: "# Title

                      ## Microservices Implemented

                      - **Service 1**: description of service 1. It uses pattern 1, pattern 2.
                      - **Service 2**: description of service 2. It uses pattern 3
                      
                      ...

        },
    ]
}
The input json is:
input json:
--------------------
{{input_json}}
--------------------

The output json is:
"""

GENERATE_PATTERN_CODE_TEXT = """
You are an expert software developer. You will be asked to generate java code for a list of microservices based on a given json architecture.
Given a microservice file list in json format, generate code snippets specifically for implementing patterns from the input json.
You are implementing a microservices architecture in Java with Spring Boot. 
Output files in a json format like this and add no other text:  
{
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
        {
            name: "user_service",
            folders: [],
            files: [
                {
                    name: "UserService.java",
                    content: "public class UserService { ... }"
                }
            ]
        }
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
} 
The input json,where reference patterns are, is:
input json:
--------------------
{{input_json}}
--------------------
The json with the microservices implemented to enhance is:
--------------------
{{microservice_list}}
--------------------
The output json is:
"""

GENERATE_DATASTORE_CODE_TEXT = """
You are an expert software developer. You will be asked to generate java code for a list of microservices based on a given json architecture.
Given a microservice file list in json format, generate code snippets specifically for implementing datastores from the input json.
Output files in a json format like this and add no other text:   
{
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
        {
            name: "user_service",
            folders: [],
            files: [
                {
                    name: "UserService.java",
                    content: "public class UserService { ... }"
                }
            ]
        }
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
} 
The input json,where reference datastores are, is:
input json:
--------------------
{{input_json}}
--------------------
The json with the microservices implemented to enhance is:
--------------------
{{patterns}}
--------------------
The output json is:
"""

GENERATE_FRONTEND_CODE_TEXT = """
You are an expert software developer. You will be asked to generate java code for a list of microservices based on a given json architecture.
Given a microservice file list in json format, generate code snippets specifically for implementing a basic frontend to test the microservices from the input json.
You are implementing a microservices architecture in Java with Spring Boot.
Output files in a json format like this and add no other text:   
{
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
        {
            name: "user_service",
            folders: [],
            files: [
                {
                    name: "UserService.java",
                    content: "public class UserService { ... }"
                }
            ]
        }
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
} 
--------------------
The json with the microservices implemented to enhance is:
--------------------
{{datastore}}
--------------------
The output json is:
"""

GENERATE_COMPOSE_CODE_TEXT = """
You are an expert software developer. You will be asked to generate a docker-compose file for a list of microservices based on a given json architecture.
Given a microservice file list in json format, add Dockerfile and docker-compose.yml files to deploy all the microservices and the frontend from the input json.
The input is microservices architecture in Java with Spring Boot. In particular, you need to combine the frontend and the backend json and add the correct docker files.
Output files in a json format like this and add no other text:   
{
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
        {
            name: "user_service",
            folders: [],
            files: [
                {
                    name: "UserService.java",
                    content: "public class UserService { ... }"
                }
            ]
        }
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
} 

--------------------
The json with the frontend is:
--------------------
{{frontend}}
--------------------
The json with the backend is:
--------------------
{{datastore}}
--------------------
The output json is:
"""

GEN_CODE_FROM_MS = """
# Prompt Template: Microservice → Full Java Implementation Text File

You are a **code generator** that takes a microservice description as input and outputs a **single plain-text file** containing a complete Java Spring Boot project implementation for that microservice.  

Your output must follow a **standard structure**, include **all file contents**, and be fully compilable and runnable.

------------------------------------------------------------
## INPUT

A Python dictionary or JSON-like object describing the microservice, e.g.:

```
{
  "name": "Order Management Service",
  "endpoints": [
    {
      "name": "/orders",
      "method": "POST",
      "inputs": ["product_id", "quantity", "user_id"],
      "outputs": ["order_id", "status", "created_at"],
      "description": "Creates a new order for a user."
    },
    {
      "name": "/orders/{id}",
      "method": "GET",
      "inputs": ["id"],
      "outputs": ["order_id", "product_id", "quantity", "user_id", "status"],
      "description": "Fetches details of an existing order."
    }
  ]
}
```

------------------------------------------------------------
## TASK

Given the above description, **generate a single plain-text document** named:

```
<service_name>_full_structure_and_code.txt
```

containing the **entire Java project**, structured and formatted exactly as follows:

------------------------------------------------------------
### Output Format

Each file must be represented like this:

```
<relative/path/to/file>
----------------------------------------
```<language>
<full file content>
```
```

Example:

```
src/main/java/com/example/orderservice/api/OrderController.java
---------------------------------------------------------------
```java
// code...
```
```

Do **not** include any commentary, markdown headings, or explanations outside those file sections.

------------------------------------------------------------
## REQUIRED PROJECT STRUCTURE

```
<service-slug>-service/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/example/<service-slug>/
│   │   │   ├── <ServiceNameNoSpaces>Application.java
│   │   │   ├── api/
│   │   │   │   ├── <ServiceNameNoSpaces>Controller.java
│   │   │   │   └── dto/
│   │   │   │       ├── <EndpointName>Request.java
│   │   │   │       └── <EndpointName>Response.java
│   │   │   ├── domain/
│   │   │   │   ├── <Entity>.java
│   │   │   ├── repo/
│   │   │   │   └── <Entity>Repository.java
│   │   │   ├── service/
│   │   │   │   └── <ServiceNameNoSpaces>Service.java
│   │   │   └── security/
│   │   │       ├── SecurityConfig.java
│   │   │       └── JwtTokenService.java
│   │   └── resources/
│   │       └── application.yml
```

------------------------------------------------------------
## IMPLEMENTATION RULES

- Use **Spring Boot 3.x**, **Java 17**, **H2** (in-memory DB), and **Spring Data JPA**.
- Include **Spring Security** and **JWT** (via JJWT).
- Each endpoint in the input must have:
  - A method in the controller.
  - A corresponding request & response DTO.
  - A service method with placeholder logic or in-memory mock implementation.
- Include validation for required fields.
- For any endpoint that references authentication, login, or token concepts, automatically:
  - Include `SecurityConfig` and `JwtTokenService`.
  - Handle `remember_me` and token expiration as in the authentication example.
- Generate boilerplate classes (`Application.java`, `Repository.java`, etc.) even if not explicitly mentioned.
- Preserve endpoint names and methods exactly from the input.
- Convert endpoint paths to safe Java identifiers (e.g. `/orders/{id}` → `OrdersId` DTOs).

------------------------------------------------------------
## OUTPUT REQUIREMENTS

- **Output a single plain-text document** (not markdown explanation).
- **Include full file contents** (no `...` or placeholders).
- **No extra comments** or summaries outside code fences.
- The resulting project must be **compilable**.

------------------------------------------------------------
## INSTRUCTION SUMMARY

**Prompt input:**  
→ A microservice description dict.

**Prompt output:**  
→ A `.txt` file containing a **complete Java project**, structured and formatted as above, one file per section, including all contents.
------------------------------------------------------------

The input is {{microservice}}
-
"""

UPDATE_PLAN_SPEC = """
You must output ONLY a single JSON object (no markdown, no pre/post text) matching this schema:

{
  "version": "1",
  "actions": [
    {"op":"mkdir","path":"<relative_dir>"},
    {"op":"write","path":"<relative_file>","content":"<text or base64>","encoding":"utf-8","if_exists":"overwrite"},
    {"op":"append","path":"<relative_file>","content":"<text or base64>","encoding":"utf-8"},
    {"op":"move","from":"<relative_old>","to":"<relative_new>","if_exists":"overwrite"},
    {"op":"delete","path":"<relative_path>","recursive":true}
  ],
  "notes":"Optional short notes"
}

Rules:
- Paths must be RELATIVE to the project root and MUST NOT contain '..'.
- Prefer 'write' with full contents over patches.
- For binary content, set "encoding": "base64".
- Keep files reasonably small; split artifacts if needed.
- Do not wrap the JSON in backticks or explanations. Output the JSON only.
""".strip()

UPDATE_DATASTORE_PLAN_SPEC = """
            You are updating a microservices project to implement and wire DATASTORES.

            ### Context (truncated)
            {{project_documents}}

            ### Datastore Spec
            These are the datastores to create/configure and integrate:
            {{datastore_spec}}

            ### Output Format
            {{update_plan_spec}}

            Guidelines:
            - Create schema/migrations/configs, connection clients, env vars, docker-compose services (if relevant),
            and service-specific modules/adapters.
            - Update imports/wiring so services actually use the created datastore modules.
            - Keep paths RELATIVE to the project root and never use '..'.
            - Prefer full 'write' ops over diffs.
            - Output ONLY the JSON object — no markdown, no prose, no code fences.
"""

UPDATE_COMPOSE_PLAN_SPEC = """
            You are Dockerizing a microservices project. Produce a JSON update plan (ONLY) to add:
            - A root docker-compose.yml wiring ALL services (app containers + infra like db, message broker).
            - Per-service Dockerfile(s) placed alongside each service code (or in sensible build contexts).
            - A .env example and any required scripts/configs to run locally.

            ### Context (truncated)
            {{project_documents}}

            ### Requirements
            - Use Compose v2 schema. Define networks, volumes, healthchecks, and depends_on with healthcheck conditions.
            - Each service gets:
            - build: context pointing to its source directory; Dockerfile path if not default.
            - ports only for public/needed endpoints; avoid port collisions.
            - environment (use ${VAR} and provide .env.example with defaults).
            - command/entrypoint as needed.
            - healthcheck (curl or script) so dependencies can wait on healthy state.
            - Add infra services required by the project (e.g., Postgres, Redis, Kafka/RabbitMQ) with durable volumes.
            - Include profiles (e.g., "all", "dev") if helpful to toggle optional components.
            - Keep paths RELATIVE to the repo root; never use '..'.
            - Prefer 'write' ops that create full files over diffs.
            - For any binary content, set "encoding": "base64".
            - Output ONLY the JSON object (no markdown, no backticks, no prose).

            ### Output Format
            {{update_plan_spec}}
"""

UPDATE_FRONTEND_PLAN_SPEC = """
You are adding a SMALL TEST FRONTEND (React) to exercise the microservices.

### Goal
Create a minimal, developer-friendly React app to manually test key endpoints (auth, products, cart, orders, admin).
Prefer **Vite + React + TypeScript** with a simple component structure and fetch helpers.

### Requirements
- Place the app under: `frontend/`
- Include:
  - Vite config for React+TS.
  - `src/` with:
    - a tiny router (or tabs) and pages/components:
      - Authentication (login/logout/register)
      - Product list & detail (GET /products, /companies/{id}/products)
      - Cart (add/remove/view)
      - Order (create, status view)
      - Admin (delete user)
    - shared API client with base URL from env (and a simple token store).
    - basic error/loading states.
  - `.env.example` exposing:
    - `VITE_API_BASE_URL=http://localhost:8080` (or aggregator/compose URL)
    - Any other needed vars (e.g., product hot flag filter).
  - package.json scripts:
    - `dev`, `build`, `preview`, `lint` (optional).
  - `index.html`.
- Dev server proxy (optional but preferred):
  - If feasible, configure Vite dev proxy so `/api` targets your backend gateway/aggregator.
- Docker:
  - `frontend/Dockerfile` for production build + static server (e.g., node:18 build -> nginx/alpine serve).
  - healthcheck script or simple HTTP check.
- Compose:
  - Add/extend root `docker-compose.yml` with a `frontend` service:
    - `build: ./frontend`
    - `ports: ["5173:5173"]` for dev or `["3000:80"]` if serving prod build via nginx
    - `environment` using `${VITE_API_BASE_URL}`
    - `depends_on` (if backend/gateway exists)
    - proper `healthcheck`
- Keep **paths RELATIVE**; never use `..`.
- Prefer **full 'write'** ops over diffs. If any file is binary, use `"encoding": "base64"`.

### Context (truncated)
{{project_documents}}

### Output Format
{{update_plan_spec}}

Output ONLY the JSON object — no markdown, no prose, no code fences.
"""