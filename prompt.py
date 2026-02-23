title = "Easy_Bank"
desc = """
An accountholder is a client of Easy Bank. This client can have zero or multiple accounts. An account is existent dependent on an accountholder.
First, model the behavior of the lowest object type. In this case, the account. The requirements are as follows (add a new FSM and select it for code generation): 
When an account is created, it exists and starts in the frozen state. In this state, it is only possible to deposit money. It is not possible to withdraw money. In addition, when an account is in the frozen state, one can open the account or end the account. If an account is open, an accountholder can deposit and withdraw money. Due to certain circumstances, it might be possible that an account is frozen again. An open account cannot be ended immediately. Before an open account can be ended, it must be frozen first.
Generate the application and test your model. Proper testing entails that the set of scenarios covers the different possible paths, and that you check if the proper constraints are in place.
"""

BACKEND_PROMPT = f"""
List the files into merode_application/src/dao, and adapt them to create a new spring boot project.
with the same logic, that implements the following textual description:
TEXTUAL_DESCRIPTION: {desc}
#############
Save the results into a new folder called backend inside the working directory called {title}.
Produce an openapi.yaml file describing the API.
"""

BACKEND_PROMPT_PYTHON = f"""
List the files into merode_application/src/dao, and adapt them to create a pyhton flask project equivalent.
with the same logic, that implements the following textual description:
#############
TEXTUAL_DESCRIPTION: {desc}
#############
Save the results into a new folder called backend inside the working directory called {title}.
Make sure to add support for CORS headers for testing in localhost. Avoid port 5000 as default.
Produce an openapi.yaml file describing the API.
"""

FRONTEND_PROMPT = f"""
From the openapi.yaml file produced by the backend agent, create a new react project.
Make its ui modern and responsive. Make sure it can communicate with the backend properly by properly configuring the vite config.
with the same logic, that implements the following textual description:
#############
TEXTUAL_DESCRIPTION: {desc}
#############
Save the results into a new folder called frontend inside the working directory called {title}.
"""