title = "htfe"
desc = """
A Home for the elderly is divided in departments.  Each department consists of a number of rooms and each room has a number of beds.  Each inhabitant is assigned a bed for his/her stay.  A bed belongs to a particular category.  Each category has a price.  The home offers different types of stays (=category): rest home (RH), rest & nursing home (RNH), service flat (SF).  An inhabitant can do more than one stay at a time. Suppose John stays in a service flat but breaks his leg and therefore has to stay in rest&nursing for a while. His stay in the service flat will then be suspended but not ended. The switch to rest&nursing doesn't require a proposal either as John is already an inhabitant.

People wishing to reside in the home go through a registration process.  This registration process involves answering a set of questions concerning the person's basic identification data. As a final step, the data of the person is registered in the system. Once the basic registration is done, the abilities of a person are assessed by means of questions that gauge the person's needs for help for basic activities such as eating, dressing, personal care (like taking a shower), as this will give an indication of the type of stay best suited for that person. The assessment results in a type of stay defined for the person. As soon as a person has been assessed, the person is considered to be on the waiting list for the corresponding type of stay. The position on the waiting list is determined by the registration date only. When a bed of the corresponding category is free, it is proposed to the person that is on the highest position of the waiting list. The person needs then to inform the Rest & Nursing Home within three days about whether s/he accepts or refuses the proposal. If the proposal is refused, the person stays on the waiting list and a new proposal is made to the next person on the list who requested this type of stay, ... and so on until a person accepts the proposal.  Once a proposal is accepted, the person's abilities are re-assessed such as to validate the requested type of stay. After this validation, the date of intake is determined and the effective stay will start on that day.  In case the type of stay needs to be changed after the re-assessment, the proposal is marked as invalidated, and the requested type of stay is updated, but the person remains in the same position on the waiting list.

Stays are invoiced once a month. For the sake of simplicity, payments will not be treated as objects, but as events. When a payment is received, this is registered and the outstanding amount of the invoice is reduced with the amount paid.  If the remaining amount is zero, the invoice is registered as "paid". If the remaining amount is still positive (paid amount too low), then the outstanding amount is adjusted, and the invoice is re-sent, indicating the remaining amount to pay.  If a person pays too much, the following actions are undertaken: the outstanding amount is set to zero, invoice is registered as paid and a credit note is created and the refund is executed immediately.  As long as an invoice is not registered as paid, it can be modified: if the inhabitant or his/her representative complains about the items that have been invoiced, this can be corrected.

When a stay comes to an end (because of the inhabitant's death or because this person decides to move to another place), the invoicing processes will continue until all invoices are paid.  The type of the stay will determine the amount that is invoiced.  In case e.g. a service flat stay goes on while an inhabitant resides in rest & nursing for a while, both stays will be invoiced, but a discount will apply to the service flat stay.
"""

BACKEND_PROMPT = """
## Task
Create a new Spring Boot backend project by adapting the provided DAO files to implement the specified business logic.

## Background
The application domain is described as follows:
{desc}

## Requirements
1. List and analyze the files in `projects/{title}/merode_application/src/dao`.
2. Adapt these DAO files to create a fully functional Spring Boot project with the same logic.
3. Produce an `openapi.yaml` file accurately describing the REST API.
4. Save the generated project into a new folder named `backend` inside the working directory `run/{title}`.

## Constraints
- The project must use Java and Spring Boot.

## Success Criteria
- The generated application compiles without errors.
- The application runs successfully.
- The `openapi.yaml` file correctly reflects the implemented endpoints.
"""

BACKEND_PROMPT_ONLY_UML = """
## Task
Create a new Spring Boot backend project by taking all information from a xml conceptual model and a textual description.

## Background
Implement all metaobject as clases, with their methods and attributes taken from metamethods and metattributes tags.
Implement all constraints from metadependencies tags. Add support for metaevents with the proper spring boot endpoints.

The application domain is described as follows:
{desc}

## Requirements
1. Analyze the xml conceptual model in `projects/{title}/merode_application/model.xmp`.
2. Use the proper xml tags to create a fully functional Spring Boot project with the same logic.
3. Produce an `openapi.yaml` file accurately describing the REST API.
4. Save the generated project into a new folder named `backend` inside the working directory `run/{title}`.

## Constraints
- The project must use Java and Spring Boot.

## Success Criteria
- The generated application compiles without errors.
- The application runs successfully.
- The `openapi.yaml` file correctly reflects the implemented endpoints.
"""

BACKEND_PROMPT_PYTHON = """
## Task
Create a new Python Flask backend project by adapting the provided Java DAO files to implement the specified business logic.

## Background
The application domain is described as follows:
{desc}

## Requirements
1. List and analyze the files in `projects/{title}/merode_application/src/dao`.
2. Adapt the logic from these DAO files to create an equivalent Python Flask project.
3. Configure CORS headers to support cross-origin requests for local testing.
4. Use a port other than 5000 as the default port.
5. Produce an `openapi.yaml` file accurately describing the REST API.
6. Save the generated project into a new folder named `backend` inside the working directory `run/{title}`.

## Constraints
- The project must use Python and Flask.

## Success Criteria
- The generated application runs successfully.
- The application correctly handles CORS for localhost.
- The application binds to a port other than 5000 by default.
- The `openapi.yaml` file correctly reflects the implemented endpoints.
"""

FRONTEND_PROMPT = """
## Task
Create a modern, responsive React frontend project that communicates with the existing backend API.

## Background
An OpenAPI specification for the backend API is available.
The application domain is described as follows:
{desc}

## Requirements
1. Use the `openapi.yaml` file produced by the backend agent inside `run/{title}/backend/` to generate the data models and API services.
2. Create a new React project using Vite.
3. Implement a modern and responsive user interface reflecting the business logic.
4. Configure the Vite setup (`vite.config.js` or similar) to correctly proxy or communicate with the backend API.
5. Save the generated project into a new folder named `frontend` inside the working directory `run/{title}`.

## Constraints
- Must use React and Vite.

## Success Criteria
- The frontend application starts and runs successfully in development mode.
- The UI is responsive and modern.
- The frontend successfully communicates with the backend.
"""

TEST_PROMPT = """
## Task
Create a Spring Boot-compatible Java testing application to execute the required test cases against the generated backend.

## Background
Test cases for this application have been pre-generated and are available in an HTML report.
The application domain is described as follows:
{desc}

## Requirements
1. Extract the test cases from the `projects/{title}/merode_application/{title}_testcases.html` file.
2. Develop a Java application compatible with Spring Boot that can execute these specific test cases against the generated backend located in the `projects/{title}/backend` folder.
3. Generate a `report.json` file containing the structured results of the test execution.
4. Generate a `report.html` file that visualizes the results from `report.json`, where are included the test cases and the results, with total and passed tests total and for each criterion.
5. Save all test artifacts into a new folder named `test` inside the working directory `run/{title}`.

## Constraints
- The testing application must be written in Java and compatible with Spring Boot testing frameworks.
- It must include all testcases from the testcases.html file.

## Success Criteria
- The testing application compiles and runs successfully.
- It correctly executes the extracted test cases against the backend.
- `report.json` and `report.html` are accurately generated.
"""

class Prompt:
    def __init__(self, title, desc):
        self.title = title
        self.desc = desc    
    
    def get_backend_prompt(self):
        return BACKEND_PROMPT.format(title=self.title, desc=self.desc)
    
    def get_backend_prompt_python(self):
        return BACKEND_PROMPT_PYTHON.format(title=self.title, desc=self.desc)
    
    def get_frontend_prompt(self):
        return FRONTEND_PROMPT.format(title=self.title, desc=self.desc)
    
    def get_test_prompt(self):
        return TEST_PROMPT.format(title=self.title, desc=self.desc)
    
    def get_backend_prompt_only_uml(self):
        return BACKEND_PROMPT_ONLY_UML.format(title=self.title, desc=self.desc)


