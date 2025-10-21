from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
)

from llama_index.llms.openai import OpenAI



from llama_index.core.prompts import RichPromptTemplate, PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core import SimpleDirectoryReader


import streamlit as st
import json

from typing import Any
from pathlib import Path

from input import (
    MicroservicesCodeExtractedEvent,
    PatternsCodeGeneratedEvent,
    ExtractMicroservice,
    DatastoreCodeGeneratedEvent,
    ComposeCodeGeneratedEvent,
    FrontendCodeGeneratedEvent
)
from output import DalleOutput, DalleOutputCode22
from utils import single_quote_to_double, single_quote_to_double_with_content, to_dict, _content
from updates_utils import apply_project_update_from_json

from utils import main as text_to_fs
from prompts import (
    GEN_CODE_FROM_MS,
    UPDATE_PLAN_SPEC,
    UPDATE_DATASTORE_PLAN_SPEC,
    UPDATE_COMPOSE_PLAN_SPEC,
    UPDATE_FRONTEND_PLAN_SPEC,
)


import io
import zipfile
import base64
import posixpath

# Load environment variables from .env file
from dotenv import load_dotenv
assert load_dotenv()



# --- Workflow Definitions ---

class DalleCodeWorkflow2(Workflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> ExtractMicroservice | None:
        # parse input_json
        input_json = json.loads(single_quote_to_double(str(to_dict(ev.input_json))))

        microservices = input_json["microservices"]
        patterns = input_json["patterns"]
        datastore = input_json["datastore"]


        #print(microservices)
        print("Detected", len(microservices), "microservices")

        await ctx.store.set("num_microservices", len(microservices))
        await ctx.store.set("patterns", patterns)
        await ctx.store.set("datastore", datastore)
        

        for microservice in microservices:
            ctx.send_event(ExtractMicroservice(microservice=microservice))

        return None


    @step(num_workers=8)
    async def extract_microservices_code(self, ctx: Context, ev: ExtractMicroservice ) -> MicroservicesCodeExtractedEvent:
        llm = OpenAI(model="gpt-4.1", timeout=9999.0, reasoning_effort="low", temperature=0)
        await ctx.store.set("llm", llm)
        
        try:

            program = LLMTextCompletionProgram.from_defaults(
                output_cls=DalleOutputCode2,
                prompt_template_str=GEN_CODE_FROM_MS,
                llm=llm,
                verbose=True,
            )

            output = program(
                microservice=ev.microservice,
            )
                
            print(output)
            with open(str(ev.microservice["name"]) +  ".txt", "w") as f:
                f.write(str(output.code))
        except Exception as e:
            print(f"Error processing microservice {ev.microservice.get('name', 'unknown')}: {e}")
            return MicroservicesCodeExtractedEvent(microservices_list="")

        return MicroservicesCodeExtractedEvent(microservices_list=output.code)
    
    @step
    async def generate_patterns_code(self, ctx: Context, ev: MicroservicesCodeExtractedEvent) -> PatternsCodeGeneratedEvent | None:
        patterns = await ctx.store.get("patterns")
        print("Patterns to implement:", patterns)
        llm = await ctx.store.get("llm")

        num_microservices = await ctx.store.get("num_microservices")
        result = ctx.collect_events(ev, [MicroservicesCodeExtractedEvent] * num_microservices)

        if result is None:
            return None

        # Write each microservice’s code into the output folder (as before)
        project_root = Path("./output_project")
        
        for r in result:
            text_to_fs(r.microservices_list, root=project_root)

        # === NEW: Load the whole project as documents using SimpleDirectoryReader ===
        # You can tweak `required_exts` to restrict what’s loaded.
        documents = SimpleDirectoryReader(
            input_dir=str(project_root),
            recursive=True,
            required_exts=[
                ".py", ".ts", ".tsx", ".js", ".json", ".yml", ".yaml", ".toml",
                ".md", ".txt", ".go", ".java", ".cs", ".rs", ".php", ".html",
                ".css", ".scss", ".sql", ".proto", ".graphql", ".dockerfile",
                ".sh", ".env", ".ini", ".cfg", ".conf"
            ],
            errors="ignore",
        ).load_data()


        # Limit per-doc bytes to keep the prompt safe; adjust as needed
        PER_DOC_LIMIT = 18_000
        project_documents = "\n\n".join(
            (content[:PER_DOC_LIMIT] if (content := _content(d)) else "")
            for d in documents
        )

        print("Project documents:", project_documents)

        """
        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode2,  # code will contain the JSON string
            prompt_template_str=(
                "You are updating a microservices project with cross-cutting PATTERNS.\n"
                "Project documents (truncated):\n{{project_documents}}\n\n"
                "Patterns to implement:\n{{patterns}}\n\n"
                "Focus only on API Gateway, CQRS, Saga and Event Sourcing patterns.\n\n"
                "{{update_plan_spec}}\n"
                "Return ONLY the JSON object."
            ),
            llm=llm,
            verbose=True,
        )

        output = program(
            patterns=patterns,
            project_documents=project_documents,
            update_plan_spec=UPDATE_PLAN_SPEC,
        ).code
        
        """

        # Run the model directly
        extract_template = RichPromptTemplate("You are updating a microservices project with cross-cutting PATTERNS.\n"
                "Project documents (truncated):\n{{project_documents}}\n\n"
                "Patterns to implement:\n{{patterns}}\n\n"
                "Focus only on API Gateway, CQRS, Saga and Event Sourcing patterns.\n\n"
                "{{update_plan_spec}}\n"
                "Return ONLY the JSON object.")
    
        extract_query = extract_template.format(project_documents=project_documents, patterns=patterns, update_plan_spec=UPDATE_PLAN_SPEC)

        print("Extract Query:", extract_query)

        output = llm.complete(extract_query).text
        

        print("Patterns:", output)
    
        # Persist raw plan for audit/debug
        plan_path = Path("patterns.plan.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(str(output))

        # Apply it to the project
        try:
            summary = apply_project_update_from_json(str(output), project_root)
        except Exception as e:
            # Persist the failure context and bubble up a structured error
            with open("patterns.plan.error.txt", "w", encoding="utf-8") as f:
                f.write(f"Failed to apply plan:\n{e}\n\nPLAN:\n{output}")
            raise

        # Save summary for visibility
        with open("patterns.apply-summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Optionally also write the (LLM) code field as a text log
        with open("patterns.txt", "w", encoding="utf-8") as f:
            f.write(str(output))


        return PatternsCodeGeneratedEvent(patterns=output)
    
    @step
    async def generate_datastore_code(
        self, ctx: Context, ev: PatternsCodeGeneratedEvent
    ) -> DatastoreCodeGeneratedEvent | None:
        # Get shared state
        llm = await ctx.store.get("llm")
        datastore_spec = await ctx.store.get("datastore")
        

        # Materialize (again/safely) into ./output_project to ensure the folder is current
        project_root = Path("./output_project")
       

        # Load repository as documents for context
        documents = SimpleDirectoryReader(
            input_dir=str(project_root),
            recursive=True,
            required_exts=[
                ".py",".ts",".tsx",".js",".json",".yml",".yaml",".toml",
                ".md",".txt",".go",".java",".cs",".rs",".php",".html",
                ".css",".scss",".sql",".proto",".graphql",".dockerfile",
                ".sh",".env",".ini",".cfg",".conf"
            ],
            errors="ignore",
        ).load_data()

        def _content(doc):
            try:
                return doc.get_content()
            except Exception:
                return getattr(doc, "text", "")

        PER_DOC_LIMIT = 18_000
        
        
        project_documents = "\n\n".join(
            (content[:PER_DOC_LIMIT] if (content := _content(d)) else "")
            for d in documents
        )
        """
        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode2,  # code will contain the JSON string
            prompt_template_str=UPDATE_DATASTORE_PLAN_SPEC,
            llm=llm,
            verbose=True,
        )

        output = program(
            datastore=datastore_spec,
            project_documents=project_documents,
            update_plan_spec=UPDATE_PLAN_SPEC,
        ).code
        """

        extract_query = RichPromptTemplate(UPDATE_DATASTORE_PLAN_SPEC).format(project_documents=project_documents, datastore=datastore_spec, update_plan_spec=UPDATE_PLAN_SPEC)

        print("Extract Query:", extract_query)
        output = llm.complete(extract_query).text
        # Persist the plan
        Path("datastore.plan.json").write_text(output, encoding="utf-8")

        # Apply to the project
        summary = apply_project_update_from_json(output, project_root)
        Path("datastore.apply-summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        # Also log the raw plan to a generic text file if you like symmetry with patterns
        Path("datastore.txt").write_text(output, encoding="utf-8")

        return DatastoreCodeGeneratedEvent(datastore=output)
    
    @step
    async def generate_frontend_code(
        self, ctx: Context, ev: DatastoreCodeGeneratedEvent
    ) -> FrontendCodeGeneratedEvent | None:
        # Get shared state
        llm = await ctx.store.get("llm")
        
        # Ensure latest code exists in ./output_project
        project_root = Path("./output_project")
       

        # Load repository as documents for context
        documents = SimpleDirectoryReader(
            input_dir=str(project_root),
            recursive=True,
            required_exts=[
                ".py",".ts",".tsx",".js",".json",".yml",".yaml",".toml",
                ".md",".txt",".go",".java",".cs",".rs",".php",".html",
                ".css",".scss",".sql",".proto",".graphql",".dockerfile",
                ".sh",".env",".ini",".cfg",".conf"
            ],
            errors="ignore",
        ).load_data()

        def _content(doc):
            try:
                return doc.get_content()
            except Exception:
                return getattr(doc, "text", "")

        PER_DOC_LIMIT = 18_000
        
        project_documents = "\n\n".join(
            (content[:PER_DOC_LIMIT] if (content := _content(d)) else "")
            for d in documents
        )

        extract_query = RichPromptTemplate(UPDATE_FRONTEND_PLAN_SPEC).format(project_documents=project_documents, update_plan_spec=UPDATE_PLAN_SPEC)

        # Call the LLM and get raw JSON
        output = llm.complete(extract_query).text
        

        # Persist the plan
        Path("frontend.plan.json").write_text(output, encoding="utf-8")

        # Apply to the project
        summary = apply_project_update_from_json(output, project_root)
        Path("frontend.apply-summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        # Optional: mirror to a text log
        Path("frontend.txt").write_text(output, encoding="utf-8")

        return FrontendCodeGeneratedEvent(frontend=output)

    @step
    async def generate_compose_code(
        self, ctx: Context, ev: FrontendCodeGeneratedEvent
    ) -> ComposeCodeGeneratedEvent | None:
        # Shared state
        llm = await ctx.store.get("llm")
        project_root = Path("./output_project")

        # Load repository as documents for context
        documents = SimpleDirectoryReader(
            input_dir=str(project_root),
            recursive=True,
            required_exts=[
                ".py",".ts",".tsx",".js",".json",".yml",".yaml",".toml",
                ".md",".txt",".go",".java",".cs",".rs",".php",".html",
                ".css",".scss",".sql",".proto",".graphql",".dockerfile",
                ".sh",".env",".ini",".cfg",".conf"
            ],
            errors="ignore",
        ).load_data()

        def _content(doc):
            try:
                return doc.get_content()
            except Exception:
                return getattr(doc, "text", "")

        PER_DOC_LIMIT = 18_000
        project_documents = "\n\n".join(
            (content[:PER_DOC_LIMIT] if (content := _content(d)) else "")
            for d in documents
        )

        extract_query = RichPromptTemplate(UPDATE_COMPOSE_PLAN_SPEC).format(project_documents=project_documents, update_plan_spec=UPDATE_PLAN_SPEC)


        # Call the LLM and get raw JSON
        output = llm.complete(extract_query).text


        # Persist the plan
        Path("compose.plan.json").write_text(output, encoding="utf-8")

        # Apply to project
        summary = apply_project_update_from_json(output, project_root)
        Path("compose.apply-summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        # Optional: keep a plain text mirror
        Path("compose.txt").write_text(output, encoding="utf-8")

        return ComposeCodeGeneratedEvent(code=output)
    @step
    async def final_step(self, ctx: Context, ev: ComposeCodeGeneratedEvent) -> StopEvent:
        
        return StopEvent(result="result")



INPUT_JSON_EXAMPLE = """{'microservices': [{'name': 'Authentication Service', 'endpoints': [{'name': '/register', 'method': 'POST', 'inputs': ['email', 'password', 'role (client|company|admin)', 'name', 'company_id (optional for company role)', 'remember_me (boolean, optional)'], 'outputs': ['user_id', 'role', 'created_at', 'auth_token (if remember_me)', 'result'], 'description': 'Registers a user (Client, Agricultural Company account or Administrator). Returns created user id and optionally persistent token when remember_me is requested.'}, {'name': '/login', 'method': 'POST', 'inputs': ['email', 'password', 'remember_me (boolean, optional)'], 'outputs': ['auth_token', 'refresh_token (optional)', 'user_id', 'role', 'expires_at'], 'description': 'Authenticates user credentials and returns tokens. remember_me issues long-lived token.'}, {'name': '/logout', 'method': 'POST', 'inputs': ['auth_token', 'refresh_token (optional)'], 'outputs': ['result'], 'description': 'Invalidates current tokens and ends session.'}, {'name': '/refresh', 'method': 'POST', 'inputs': ['refresh_token'], 'outputs': ['auth_token', 'refresh_token', 'expires_at'], 'description': 'Refreshes auth token using a valid refresh token.'}, {'name': '/validate', 'method': 'GET', 'inputs': ['auth_token'], 'outputs': ['user_id', 'role', 'valid', 'expires_at'], 'description': 'Validates token and returns associated user identity and role.'}], 'user_stories': ['1', '2', '3', '4', '17', '18', '19', '20', '22', '23', '24'], 'parameters': ['email', 'password', 'role', 'user_id', 'auth_token', 'refresh_token', 'token_expires_at', 'remember_me'], 'description': 'Handles registration, login, token issuance (persistent sessions/remember me), logout and token validation for Clients, Agricultural Companies and Administrators. Implements authentication aggregate behavior and owns its credential/session datastore.'}, {'name': 'User Profile Service', 'endpoints': [{'name': '/profiles/{user_id}', 'method': 'GET', 'inputs': ['user_id', 'auth_token'], 'outputs': ['user_id', 'name', 'email (if permitted)', 'phone', 'address', 'role', 'company_id (if company user)', 'created_at', 'updated_at'], 'description': 'Retrieves personal information for a Client or Agricultural Company user. Authenticated users see their own profile; admins may view others.'}, {'name': '/profiles/{user_id}', 'method': 'PUT', 'inputs': ['user_id', 'auth_token', 'name (optional)', 'phone (optional)', 'address (optional)', 'profile_picture (optional)'], 'outputs': ['user_id', 'updated_at', 'result'], 'description': "Updates a user's personal information. Only the owner or admin may update."}, {'name': '/companies/{company_id}/profile', 'method': 'GET', 'inputs': ['company_id', 'auth_token'], 'outputs': ['company_id', 'company_name', 'description', 'location', 'contact_info', 'opening_hours', 'created_at', 'updated_at'], 'description': 'Retrieves company profile information for inspection by clients or company owner.'}, {'name': '/companies/{company_id}/profile', 'method': 'PUT', 'inputs': ['company_id', 'auth_token', 'company_name (optional)', 'description (optional)', 'location (optional)', 'contact_info (optional)', 'opening_hours (optional)'], 'outputs': ['company_id', 'updated_at', 'result'], 'description': 'Updates agricultural company profile. Only company owner or admin may update.'}], 'user_stories': ['5', '21'], 'parameters': ['user_id', 'company_id', 'name', 'email', 'phone', 'address', 'location', 'contact_info', 'opening_hours', 'profile_picture'], 'description': 'Manages viewing and updating of user and agricultural company profile information. Modeled as aggregates (user aggregate, company profile aggregate). Publishes domain events when company profile changes so other services can react (e.g., Product Catalog, Order).'}, {'name': 'Product Catalog Service', 'endpoints': [{'name': '/companies/{company_id}/products', 'method': 'GET', 'inputs': ['company_id', 'auth_token (for create/update/delete)', 'pagination (page, size)', 'filters (category, season, hot flag)'], 'outputs': ['products[] (product_id, name, description, price, quantity_available, images, hot_flag, created_at, updated_at)'], 'description': 'Lists products for a company. Supports filtering (hot products for story 6). Publicly viewable.'}, {'name': '/products/hot', 'method': 'GET', 'inputs': ['pagination (page,size)', 'season (optional)'], 'outputs': ['hot_products[] (product_id, name, company_id, price, images, season)'], 'description': 'Lists hot/seasonal products across companies for discovery (implements user story 6).'}, {'name': '/companies/{company_id}/products', 'method': 'POST', 'inputs': ['company_id', 'auth_token', 'name', 'description', 'price', 'quantity', 'category (optional)', 'images (optional)', 'hot_flag (optional)'], 'outputs': ['product_id', 'created_at', 'result'], 'description': "Create a new product in a company's inventory (story 14). Emits domain event ProductAdded."}, {'name': '/companies/{company_id}/products/{product_id}', 'method': 'PUT', 'inputs': ['company_id', 'product_id', 'auth_token', 'name (optional)', 'description (optional)', 'price (optional)', 'quantity (optional)', 'images (optional)', 'hot_flag (optional)'], 'outputs': ['product_id', 'updated_at', 'result'], 'description': 'Modify an existing product (story 16). Emits domain event ProductUpdated.'}, {'name': '/companies/{company_id}/products/{product_id}', 'method': 'DELETE', 'inputs': ['company_id', 'product_id', 'auth_token'], 'outputs': ['product_id', 'result'], 'description': 'Remove a product from inventory (story 15). Emits domain event ProductRemoved.'}, {'name': '/products/{product_id}', 'method': 'GET', 'inputs': ['product_id'], 'outputs': ['product_id', 'name', 'description', 'price', 'quantity_available', 'company_id', 'images', 'hot_flag'], 'description': 'Gets a single product detail.'}], 'user_stories': ['6', '8', '14', '15', '16'], 'parameters': ['product_id', 'company_id', 'name', 'description', 'price', 'quantity', 'quantity_available', 'category', 'images', 'hot_flag', 'season'], 'description': 'Manages product listings and inventory for agricultural companies. Each product is modeled as an aggregate. Emits domain events (ProductAdded/ProductUpdated/ProductRemoved) so Cart and Order can react to availability changes. Owns its product datastore for isolation and scalability.'}, {'name': 'Agricultural Company Service', 'endpoints': [{'name': '/companies', 'method': 'POST', 'inputs': ['auth_token (for company registration)', 'company_name', 'description', 'location (lat,long or address)', 'contact_info', 'opening_hours'], 'outputs': ['company_id', 'created_at', 'result'], 'description': 'Register a new agricultural company (story 17). Emits CompanyRegistered domain event.'}, {'name': '/companies/{company_id}', 'method': 'GET', 'inputs': ['company_id'], 'outputs': ['company_id', 'company_name', 'description', 'location', 'contact_info', 'opening_hours', 'created_at', 'updated_at'], 'description': 'Retrieve company details for discovery (story 7).'}, {'name': '/companies/nearby', 'method': 'GET', 'inputs': ['latitude', 'longitude', 'radius_km', 'filters (optional, e.g., category)'], 'outputs': ['companies[] (company_id, company_name, location, distance, contact_info)'], 'description': 'Discover agricultural companies in a given area (story 7).'}, {'name': '/companies/{company_id}/location/map', 'method': 'GET', 'inputs': ['company_id'], 'outputs': ['map_url (google maps link with coordinates)'], 'description': "Returns a Google Maps URL for the company's location to open directions (story 13)."}, {'name': '/companies/{company_id}', 'method': 'PUT', 'inputs': ['company_id', 'auth_token', 'company_name (optional)', 'description (optional)', 'location (optional)', 'contact_info (optional)', 'opening_hours (optional)'], 'outputs': ['company_id', 'updated_at', 'result'], 'description': 'Update company profile (story 21). Emits CompanyUpdated domain event.'}], 'user_stories': ['7', '13', '17', '21'], 'parameters': ['company_id', 'company_name', 'description', 'location', 'latitude', 'longitude', 'contact_info', 'opening_hours'], 'description': 'Handles company registration, profile management and discovery. Each company is modeled as an aggregate and emits domain events (CompanyRegistered, CompanyUpdated) so Product Catalog and other services can respond. Owns a company datastore.'}, {'name': 'Cart Service', 'endpoints': [{'name': '/carts/{user_id}', 'method': 'GET', 'inputs': ['user_id', 'auth_token'], 'outputs': ['cart_id', 'user_id', 'items[] (product_id, company_id, name, price, quantity_selected)', 'total_price', 'updated_at'], 'description': 'Retrieve the current shopping cart for a user (story 11).'}, {'name': '/carts/{user_id}/items', 'method': 'POST', 'inputs': ['user_id', 'auth_token', 'product_id', 'company_id', 'quantity'], 'outputs': ['cart_id', 'item_id', 'result', 'updated_cart'], 'description': "Add a product to the user's cart (story 9). Emits CartItemAdded domain event to support analytics and optionally to notify inventory watchers."}, {'name': '/carts/{user_id}/items/{item_id}', 'method': 'DELETE', 'inputs': ['user_id', 'item_id', 'auth_token'], 'outputs': ['result', 'updated_cart'], 'description': 'Remove an item from the cart (story 10). Emits CartItemRemoved domain event.'}, {'name': '/carts/{user_id}/clear', 'method': 'POST', 'inputs': ['user_id', 'auth_token'], 'outputs': ['result'], 'description': "Clears the user's cart (used after order completion)."}], 'user_stories': ['9', '10', '11'], 'parameters': ['cart_id', 'user_id', 'items', 'product_id', 'company_id', 'quantity', 'total_price', 'updated_at'], 'description': 'Manages user shopping carts as aggregates. Stores cart state (items and quantities). Emits domain events on item add/remove so Order and Product services can react. Uses its own datastore to maintain isolation and fast operations.'}, {'name': 'Order Service', 'endpoints': [{'name': '/orders', 'method': 'POST', 'inputs': ['user_id', 'auth_token', 'cart_id', 'pickup_date', 'pickup_company_id', 'payment_info (if applicable)'], 'outputs': ['order_id', 'status (pending|confirmed|cancelled|failed)', 'estimated_pickup_date', 'result'], 'description': "Creates an order from a user's cart and starts a Saga to coordinate inventory validation, reservation and confirmation (story 12). Emits OrderCreated domain event."}, {'name': '/orders/{order_id}', 'method': 'GET', 'inputs': ['order_id', 'auth_token'], 'outputs': ['order_id', 'user_id', 'items[] (product_id, company_id, qty, price)', 'status', 'pickup_date', 'pickup_company_id', 'created_at', 'updated_at'], 'description': 'Retrieve order details and status.'}, {'name': '/orders/{order_id}/cancel', 'method': 'POST', 'inputs': ['order_id', 'auth_token', 'reason (optional)'], 'outputs': ['order_id', 'status', 'result'], 'description': 'Cancels an order and triggers compensation steps in the Saga (inventory release, cart restore).'}, {'name': '/orders/{order_id}/status', 'method': 'GET', 'inputs': ['order_id', 'auth_token'], 'outputs': ['order_id', 'status', 'progress_log[]'], 'description': 'Returns the current status and saga progress for the order.'}], 'user_stories': ['12'], 'parameters': ['order_id', 'user_id', 'cart_id', 'items', 'status', 'pickup_date', 'pickup_company_id', 'created_at', 'updated_at'], 'description': 'Handles order lifecycle and orchestration of multi-step operations across services using the Saga pattern. Each order is an aggregate in its own datastore. Publishes domain events (OrderCreated, OrderConfirmed, OrderCancelled) for other services to respond (e.g., Product Catalog to decrement inventory).'}, {'name': 'Administration Service', 'endpoints': [{'name': '/admin/users/{user_id}', 'method': 'DELETE', 'inputs': ['admin_auth_token', 'user_id', 'reason (optional)'], 'outputs': ['result', 'deleted_user_id'], 'description': 'Allows administrators to delete malicious or problematic users (story 25). Emits UserDeleted domain event so other services can clean up related data (carts, orders, profiles).'}, {'name': '/admin/users', 'method': 'GET', 'inputs': ['admin_auth_token', 'filters (role, created_before, suspicious_flag)'], 'outputs': ['users[] (user_id, email, role, created_at, status)'], 'description': 'List users for administration and moderation.'}], 'user_stories': ['25'], 'parameters': ['admin_auth_token', 'user_id', 'deleted_user_id', 'reason', 'status'], 'description': 'Provides administrative actions and aggregates admin operations. Owns an admin datastore to persist audit logs and administrative decisions. Emits domain events upon user deletion to propagate changes.'}], 'patterns': [{'group_name': 'Auth Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['Authentication Service'], 'explaination': 'Authentication stores credentials and session tokens and must be isolated for security and independent scaling. The retrieved context recommended Database per Service and aggregate modelling for authentication, so we keep a dedicated datastore.'}, {'group_name': 'Profiles Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['User Profile Service'], 'explaination': 'User and company profile data are updated independently and must be isolated; aggregate pattern applies to user and company profiles as suggested in the context.'}, {'group_name': 'Product Inventory', 'implementation_pattern': 'database per service', 'involved_microservices': ['Product Catalog Service'], 'explaination': 'Products require their own datastore for inventory control. Context recommended Database per Service and Aggregate; domain events are used to notify other services of changes, so Product Catalog owns its data.'}, {'group_name': 'Company Management', 'implementation_pattern': 'database per service', 'involved_microservices': ['Agricultural Company Service'], 'explaination': 'Company registration and location data should be autonomous for scalability and to publish CompanyRegistered/Updated events. Context recommended Database per Service and Aggregate.'}, {'group_name': 'Cart Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['Cart Service'], 'explaination': 'Carts are frequently updated, need low-latency writes and isolation from other services; modeled as aggregates per user. Context recommends a dedicated cart datastore and domain events for item changes.'}, {'group_name': 'Order Orchestration', 'implementation_pattern': 'saga', 'involved_microservices': ['Order Service', 'Product Catalog Service', 'Cart Service', 'User Profile Service', 'Agricultural Company Service', 'Administration Service', 'Authentication Service'], 'explaination': 'Creating an order requires coordinating multiple services (reserve inventory, confirm pickup with company, clear cart). The context explicitly recommended Saga for Order to manage multi-step distributed transactions with compensation steps.'}, {'group_name': 'Cross-Service Queries', 'implementation_pattern': 'api composition', 'involved_microservices': ['Product Catalog Service', 'Agricultural Company Service', 'User Profile Service', 'Cart Service', 'Order Service'], 'explaination': 'Displaying combined views (company with its products, user orders with product details) will be implemented via API Composition: the frontend (or aggregator) will call multiple services and compose responses. The context recommends API Composition and optionally CQRS for heavier reporting.'}, {'group_name': 'Event-driven consistency', 'implementation_pattern': 'domain event', 'involved_microservices': ['Product Catalog Service', 'Cart Service', 'Order Service', 'User Profile Service', 'Agricultural Company Service', 'Administration Service'], 'explaination': 'Domain events (ProductAdded, ProductUpdated, ProductRemoved, OrderCreated, CompanyRegistered, UserDeleted) keep services loosely-coupled and allow eventual consistency. The context recommended domain events for product and company changes and admin actions.'}, {'group_name': 'Query optimization (optional)', 'implementation_pattern': 'cqrs', 'involved_microservices': ['Product Catalog Service', 'Order Service', 'User Profile Service'], 'explaination': 'For complex queries such as dashboards or combined views, materialized read models may be maintained. The context suggested CQRS for complex queries; this group would maintain read-optimized views aggregated from multiple domain events.'}], 'datastore': [{'datastore_name': 'auth_db', 'associated_microservices': ['Authentication Service'], 'description': 'Stores user credentials (hashed), refresh tokens, persistent sessions and auth audit logs. Chosen because many user stories require registration, login, remember-me and logout (stories 1-4,17-20,22-24). Database per service is required for security and isolation.'}, {'datastore_name': 'profiles_db', 'associated_microservices': ['User Profile Service'], 'description': 'Holds user profile aggregates and company profile snapshots. Influenced by stories 5 and 21 requiring viewing and updating personal/company information. Database per service allows independent updates and aggregate transactions.'}, {'datastore_name': 'product_catalog_db', 'associated_microservices': ['Product Catalog Service'], 'description': 'Contains product aggregates (product details, price, quantity, hot flag). Domain events are emitted on changes to support cart and order flows. Chosen because stories 6,8,14-16 require product listing and inventory operations; database per service supports inventory isolation.'}, {'datastore_name': 'company_db', 'associated_microservices': ['Agricultural Company Service'], 'description': 'Stores agricultural company aggregates, locations (lat/long), contact and opening hours. Influenced by stories 7,13,17,21 (registration, discovery, maps). Database per service supports search and emits domain events.'}, {'datastore_name': 'cart_db', 'associated_microservices': ['Cart Service'], 'description': 'Stores cart aggregates per user with items, quantities and timestamps. Required by stories 9-11 for adding/removing/viewing cart. Domain events optionally published when items change; database per service supports fast updates.'}, {'datastore_name': 'orders_db', 'associated_microservices': ['Order Service'], 'description': 'Persists order aggregates and saga state (progress logs, compensating actions). Influenced by story 12: order completion and pickup date selection requires coordination. Saga orchestration requires storing state and events for compensation.'}, {'datastore_name': 'admin_db', 'associated_microservices': ['Administration Service'], 'description': 'Stores admin actions, audit logs, moderation decisions and lists of banned/deleted users. Story 25 (delete malicious user) required persistent admin decisions and emission of UserDeleted events to allow other services to purge or anonymize data.'}, {'datastore_name': 'read_models_db (optional CQRS)', 'associated_microservices': ['Product Catalog Service', 'Order Service', 'User Profile Service'], 'description': 'Materialized read views for combined queries (e.g., company with products, user order history with product details). Influenced by API Composition and the optional CQRS recommendation for optimized cross-service queries and reporting.'}]}
"""


import asyncio

wf = DalleCodeWorkflow2(timeout=None)

async def main():
    res = await wf.run(input_json=INPUT_JSON_EXAMPLE)
    print("Final result:", res)

asyncio.run(main())