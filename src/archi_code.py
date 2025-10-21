from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event
)

from llama_index.llms.openai import OpenAI
from llama_index.core.schema import (
    NodeWithScore,
)
from llama_index.core.response_synthesizers import (
    get_response_synthesizer,
    ResponseMode
)

from llama_index.llms.anthropic import Anthropic
from llama_index.llms.groq import Groq
from llama_index.llms.gemini import Gemini


from llama_index.core.prompts import RichPromptTemplate, PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram

import streamlit as st
import json

from typing import Any

from output import DalleOutput, DalleOutputCode
from utils import single_quote_to_double, single_quote_to_double_with_content, to_dict
from prompts import (
    GENERATE_CODE_TEXT,
    GENERATE_PATTERN_CODE_TEXT,
    GENERATE_FRONTEND_CODE_TEXT,
    GENERATE_COMPOSE_CODE_TEXT,
)


import io
import zipfile
import base64
import posixpath

# Load environment variables from .env file
from dotenv import load_dotenv
assert load_dotenv()


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




# --- Workflow Definitions ---

class DalleCodeWorkflow(Workflow):
    @step
    async def extract_microservices_code(self, ctx: Context, ev: StartEvent) -> MicroservicesCodeExtractedEvent:
        llm = OpenAI(model="gpt-4.1", timeout=9999.0) #, reasoning_effort="medium", temperature=0, timeout=9999.0)
        await ctx.store.set("llm", llm)
        await ctx.store.set("input_json", ev.input_json)
        


        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            input_json=ev.input_json,
        )
        print("Output from LLM:", to_dict(output))

            
        st.write("✅ Extracted Microservices List.")
        return MicroservicesCodeExtractedEvent(microservices_list=single_quote_to_double_with_content(str(to_dict(output))))

    @step
    async def generate_pattern_code(self, ctx: Context, ev: MicroservicesCodeExtractedEvent) -> PatternsCodeGeneratedEvent:
        
        input_json = await ctx.store.get("input_json")
        await ctx.store.set("microservices_list", ev.microservices_list)

        llm = await ctx.store.get("llm")
        #llm = OpenAI(model="gpt-5-mini" , reasoning_effort="minimal", temperature=0, timeout=9999.0)
        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)

        #sllm = llm.as_structured_llm(output_cls=DalleOutput)

    

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_PATTERN_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            input_json=input_json,
            microservice_list=ev.microservices_list,
        )

        print("Output from LLM:", to_dict(output))

        #resp = single_quote_to_double(str(sllm.complete(final_query).raw.dict()))
        #print("Final response:", resp)
        
        st.write("✅ Generated Final Architecture.")
        return PatternsCodeGeneratedEvent(patterns=single_quote_to_double_with_content(str(to_dict(output))))
    @step
    async def generate_datastore_code(self, ctx: Context, ev: PatternsCodeGeneratedEvent) -> DatastoreCodeGeneratedEvent:
        """Generate code snippets for each microservice based on the architecture."""
        
        llm = await ctx.store.get("llm")
        input_json = await ctx.store.get("input_json")

        await ctx.store.set("patterns", ev.patterns)


        #llm = OpenAI(model="gpt-5-mini" , reasoning_effort="medium", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)
        #llm = Groq(model="openai/gpt-oss-120b", temperature=0, max_tokens=19_000, timeout=9999.0)

        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)


        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_PATTERN_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            input_json=input_json,
            patterns=ev.patterns,
        )
        print("Code Output from LLM:", to_dict(output))
        st.write("✅  Generated code snippets for microservices.")
        return DatastoreCodeGeneratedEvent(datastore=single_quote_to_double_with_content(str(to_dict(output))))
    
    @step
    async def generate_frontend_code(self, ctx: Context, ev: DatastoreCodeGeneratedEvent) -> FrontendCodeGeneratedEvent:
        """Generate code snippets for each microservice based on the architecture."""
        
        llm = await ctx.store.get("llm")
        await ctx.store.set("datastore", ev.datastore)

        #llm = OpenAI(model="gpt-5-mini" , reasoning_effort="medium", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)
        #llm = Groq(model="openai/gpt-oss-120b", temperature=0, max_tokens=19_000, timeout=9999.0)

        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)


        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_FRONTEND_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            datastore=ev.datastore,
        )
        print("Code Output from LLM:", to_dict(output))
        st.write("✅  Generated code snippets for microservices.")
        return FrontendCodeGeneratedEvent(frontend=single_quote_to_double_with_content(str(to_dict(output))))
    
    @step
    async def generate_compose_code(self, ctx: Context, ev: FrontendCodeGeneratedEvent) -> ComposeCodeGeneratedEvent:
        """Generate code snippets for each microservice based on the architecture."""
        
        llm = await ctx.store.get("llm")        
        datastore = await ctx.store.get("datastore")


        #llm = OpenAI(model="gpt-5-mini" , reasoning_effort="medium", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)
        #llm = Groq(model="openai/gpt-oss-120b", temperature=0, max_tokens=19_000, timeout=9999.0)

        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)


        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_COMPOSE_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            frontend=ev.frontend,
            datastore=datastore,
        )

        print("Code Output from LLM:", to_dict(output))
        st.write("✅  Generated code snippets for microservices.")
        return ComposeCodeGeneratedEvent(code=single_quote_to_double_with_content(str(to_dict(output))))
    

    
    @step
    async def package_zip(self, ctx: Context, ev: ComposeCodeGeneratedEvent) -> StopEvent:
        """
        Convert the generated microservices JSON into a ZIP archive.
        The JSON is expected to follow the schema:
        { "folders": [ { "name": str, "folders": [...], "files": [{"name": str, "content": str}] } ],
          "files":   [ { "name": str (can include nested paths like 'a/b/c.txt'), "content": str } ] }
        Returns: StopEvent(result={"filename": "...zip", "zip_base64": "<base64-zip>"})
        """
        # Parse the JSON produced by the previous step
        try:
            structure = ev.code
            print("Generated code structure:", structure)
            with open("debug_generated_code.txt", "w") as f:
                f.write(str(structure))
            if isinstance(structure, str):
                structure = json.loads(structure)
        except Exception as e:
            st.error(f"❌ Could not parse generated code JSON: {e}")
            return StopEvent(result={"error": f"Invalid JSON from CodeGeneratedEvent: {e}"})

        # Helpers to write the file-tree directly into a ZIP (no temp files needed)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

            def _write_files(files: list | None, base: str = ""):
                if not files:
                    return
                for f in files:
                    name = (f or {}).get("name", "")
                    content = (f or {}).get("content", "")
                    if not name:
                        continue
                    # Support names that already include nested paths (e.g., "src/main/.../User.java")
                    arcpath = posixpath.join(base, name).lstrip("/")
                    # Ensure directory placeholders for nicer unzip UX (optional)
                    dirpart = posixpath.dirname(arcpath)
                    if dirpart and not dirpart.endswith("/"):
                        zf.writestr(dirpart + "/", "")
                    zf.writestr(arcpath, content or "")

            def _write_folders(folders: list | None, base: str = ""):
                if not folders:
                    return
                for folder in folders:
                    if not folder:
                        continue
                    folder_name = folder.get("name", "")
                    folder_path = posixpath.join(base, folder_name).strip("/")
                    # Add an explicit directory entry
                    if folder_path:
                        zf.writestr(folder_path + "/", "")
                    # Write files in this folder
                    _write_files(folder.get("files", []), folder_path)
                    # Recurse into subfolders
                    _write_folders(folder.get("folders", []), folder_path)

            # Top-level files (may include full nested paths)
            _write_files(structure.get("files", []), "")
            # Foldered structure
            _write_folders(structure.get("folders", []), "")

        buf.seek(0)
        zip_b64 = base64.b64encode(buf.read()).decode("ascii")
        payload = {
            "filename": "microservices_project.zip",
            "zip_base64": zip_b64,
        }
        st.write("✅ Packaged microservices code as a ZIP.")
        return StopEvent(result=payload)



INPUT_JSON_EXAMPLE = """{'microservices': [{'name': 'Authentication Service', 'endpoints': [{'name': '/register', 'method': 'POST', 'inputs': ['email', 'password', 'role (client|company|admin)', 'name', 'company_id (optional for company role)', 'remember_me (boolean, optional)'], 'outputs': ['user_id', 'role', 'created_at', 'auth_token (if remember_me)', 'result'], 'description': 'Registers a user (Client, Agricultural Company account or Administrator). Returns created user id and optionally persistent token when remember_me is requested.'}, {'name': '/login', 'method': 'POST', 'inputs': ['email', 'password', 'remember_me (boolean, optional)'], 'outputs': ['auth_token', 'refresh_token (optional)', 'user_id', 'role', 'expires_at'], 'description': 'Authenticates user credentials and returns tokens. remember_me issues long-lived token.'}, {'name': '/logout', 'method': 'POST', 'inputs': ['auth_token', 'refresh_token (optional)'], 'outputs': ['result'], 'description': 'Invalidates current tokens and ends session.'}, {'name': '/refresh', 'method': 'POST', 'inputs': ['refresh_token'], 'outputs': ['auth_token', 'refresh_token', 'expires_at'], 'description': 'Refreshes auth token using a valid refresh token.'}, {'name': '/validate', 'method': 'GET', 'inputs': ['auth_token'], 'outputs': ['user_id', 'role', 'valid', 'expires_at'], 'description': 'Validates token and returns associated user identity and role.'}], 'user_stories': ['1', '2', '3', '4', '17', '18', '19', '20', '22', '23', '24'], 'parameters': ['email', 'password', 'role', 'user_id', 'auth_token', 'refresh_token', 'token_expires_at', 'remember_me'], 'description': 'Handles registration, login, token issuance (persistent sessions/remember me), logout and token validation for Clients, Agricultural Companies and Administrators. Implements authentication aggregate behavior and owns its credential/session datastore.'}, {'name': 'User Profile Service', 'endpoints': [{'name': '/profiles/{user_id}', 'method': 'GET', 'inputs': ['user_id', 'auth_token'], 'outputs': ['user_id', 'name', 'email (if permitted)', 'phone', 'address', 'role', 'company_id (if company user)', 'created_at', 'updated_at'], 'description': 'Retrieves personal information for a Client or Agricultural Company user. Authenticated users see their own profile; admins may view others.'}, {'name': '/profiles/{user_id}', 'method': 'PUT', 'inputs': ['user_id', 'auth_token', 'name (optional)', 'phone (optional)', 'address (optional)', 'profile_picture (optional)'], 'outputs': ['user_id', 'updated_at', 'result'], 'description': "Updates a user's personal information. Only the owner or admin may update."}, {'name': '/companies/{company_id}/profile', 'method': 'GET', 'inputs': ['company_id', 'auth_token'], 'outputs': ['company_id', 'company_name', 'description', 'location', 'contact_info', 'opening_hours', 'created_at', 'updated_at'], 'description': 'Retrieves company profile information for inspection by clients or company owner.'}, {'name': '/companies/{company_id}/profile', 'method': 'PUT', 'inputs': ['company_id', 'auth_token', 'company_name (optional)', 'description (optional)', 'location (optional)', 'contact_info (optional)', 'opening_hours (optional)'], 'outputs': ['company_id', 'updated_at', 'result'], 'description': 'Updates agricultural company profile. Only company owner or admin may update.'}], 'user_stories': ['5', '21'], 'parameters': ['user_id', 'company_id', 'name', 'email', 'phone', 'address', 'location', 'contact_info', 'opening_hours', 'profile_picture'], 'description': 'Manages viewing and updating of user and agricultural company profile information. Modeled as aggregates (user aggregate, company profile aggregate). Publishes domain events when company profile changes so other services can react (e.g., Product Catalog, Order).'}, {'name': 'Product Catalog Service', 'endpoints': [{'name': '/companies/{company_id}/products', 'method': 'GET', 'inputs': ['company_id', 'auth_token (for create/update/delete)', 'pagination (page, size)', 'filters (category, season, hot flag)'], 'outputs': ['products[] (product_id, name, description, price, quantity_available, images, hot_flag, created_at, updated_at)'], 'description': 'Lists products for a company. Supports filtering (hot products for story 6). Publicly viewable.'}, {'name': '/products/hot', 'method': 'GET', 'inputs': ['pagination (page,size)', 'season (optional)'], 'outputs': ['hot_products[] (product_id, name, company_id, price, images, season)'], 'description': 'Lists hot/seasonal products across companies for discovery (implements user story 6).'}, {'name': '/companies/{company_id}/products', 'method': 'POST', 'inputs': ['company_id', 'auth_token', 'name', 'description', 'price', 'quantity', 'category (optional)', 'images (optional)', 'hot_flag (optional)'], 'outputs': ['product_id', 'created_at', 'result'], 'description': "Create a new product in a company's inventory (story 14). Emits domain event ProductAdded."}, {'name': '/companies/{company_id}/products/{product_id}', 'method': 'PUT', 'inputs': ['company_id', 'product_id', 'auth_token', 'name (optional)', 'description (optional)', 'price (optional)', 'quantity (optional)', 'images (optional)', 'hot_flag (optional)'], 'outputs': ['product_id', 'updated_at', 'result'], 'description': 'Modify an existing product (story 16). Emits domain event ProductUpdated.'}, {'name': '/companies/{company_id}/products/{product_id}', 'method': 'DELETE', 'inputs': ['company_id', 'product_id', 'auth_token'], 'outputs': ['product_id', 'result'], 'description': 'Remove a product from inventory (story 15). Emits domain event ProductRemoved.'}, {'name': '/products/{product_id}', 'method': 'GET', 'inputs': ['product_id'], 'outputs': ['product_id', 'name', 'description', 'price', 'quantity_available', 'company_id', 'images', 'hot_flag'], 'description': 'Gets a single product detail.'}], 'user_stories': ['6', '8', '14', '15', '16'], 'parameters': ['product_id', 'company_id', 'name', 'description', 'price', 'quantity', 'quantity_available', 'category', 'images', 'hot_flag', 'season'], 'description': 'Manages product listings and inventory for agricultural companies. Each product is modeled as an aggregate. Emits domain events (ProductAdded/ProductUpdated/ProductRemoved) so Cart and Order can react to availability changes. Owns its product datastore for isolation and scalability.'}, {'name': 'Agricultural Company Service', 'endpoints': [{'name': '/companies', 'method': 'POST', 'inputs': ['auth_token (for company registration)', 'company_name', 'description', 'location (lat,long or address)', 'contact_info', 'opening_hours'], 'outputs': ['company_id', 'created_at', 'result'], 'description': 'Register a new agricultural company (story 17). Emits CompanyRegistered domain event.'}, {'name': '/companies/{company_id}', 'method': 'GET', 'inputs': ['company_id'], 'outputs': ['company_id', 'company_name', 'description', 'location', 'contact_info', 'opening_hours', 'created_at', 'updated_at'], 'description': 'Retrieve company details for discovery (story 7).'}, {'name': '/companies/nearby', 'method': 'GET', 'inputs': ['latitude', 'longitude', 'radius_km', 'filters (optional, e.g., category)'], 'outputs': ['companies[] (company_id, company_name, location, distance, contact_info)'], 'description': 'Discover agricultural companies in a given area (story 7).'}, {'name': '/companies/{company_id}/location/map', 'method': 'GET', 'inputs': ['company_id'], 'outputs': ['map_url (google maps link with coordinates)'], 'description': "Returns a Google Maps URL for the company's location to open directions (story 13)."}, {'name': '/companies/{company_id}', 'method': 'PUT', 'inputs': ['company_id', 'auth_token', 'company_name (optional)', 'description (optional)', 'location (optional)', 'contact_info (optional)', 'opening_hours (optional)'], 'outputs': ['company_id', 'updated_at', 'result'], 'description': 'Update company profile (story 21). Emits CompanyUpdated domain event.'}], 'user_stories': ['7', '13', '17', '21'], 'parameters': ['company_id', 'company_name', 'description', 'location', 'latitude', 'longitude', 'contact_info', 'opening_hours'], 'description': 'Handles company registration, profile management and discovery. Each company is modeled as an aggregate and emits domain events (CompanyRegistered, CompanyUpdated) so Product Catalog and other services can respond. Owns a company datastore.'}, {'name': 'Cart Service', 'endpoints': [{'name': '/carts/{user_id}', 'method': 'GET', 'inputs': ['user_id', 'auth_token'], 'outputs': ['cart_id', 'user_id', 'items[] (product_id, company_id, name, price, quantity_selected)', 'total_price', 'updated_at'], 'description': 'Retrieve the current shopping cart for a user (story 11).'}, {'name': '/carts/{user_id}/items', 'method': 'POST', 'inputs': ['user_id', 'auth_token', 'product_id', 'company_id', 'quantity'], 'outputs': ['cart_id', 'item_id', 'result', 'updated_cart'], 'description': "Add a product to the user's cart (story 9). Emits CartItemAdded domain event to support analytics and optionally to notify inventory watchers."}, {'name': '/carts/{user_id}/items/{item_id}', 'method': 'DELETE', 'inputs': ['user_id', 'item_id', 'auth_token'], 'outputs': ['result', 'updated_cart'], 'description': 'Remove an item from the cart (story 10). Emits CartItemRemoved domain event.'}, {'name': '/carts/{user_id}/clear', 'method': 'POST', 'inputs': ['user_id', 'auth_token'], 'outputs': ['result'], 'description': "Clears the user's cart (used after order completion)."}], 'user_stories': ['9', '10', '11'], 'parameters': ['cart_id', 'user_id', 'items', 'product_id', 'company_id', 'quantity', 'total_price', 'updated_at'], 'description': 'Manages user shopping carts as aggregates. Stores cart state (items and quantities). Emits domain events on item add/remove so Order and Product services can react. Uses its own datastore to maintain isolation and fast operations.'}, {'name': 'Order Service', 'endpoints': [{'name': '/orders', 'method': 'POST', 'inputs': ['user_id', 'auth_token', 'cart_id', 'pickup_date', 'pickup_company_id', 'payment_info (if applicable)'], 'outputs': ['order_id', 'status (pending|confirmed|cancelled|failed)', 'estimated_pickup_date', 'result'], 'description': "Creates an order from a user's cart and starts a Saga to coordinate inventory validation, reservation and confirmation (story 12). Emits OrderCreated domain event."}, {'name': '/orders/{order_id}', 'method': 'GET', 'inputs': ['order_id', 'auth_token'], 'outputs': ['order_id', 'user_id', 'items[] (product_id, company_id, qty, price)', 'status', 'pickup_date', 'pickup_company_id', 'created_at', 'updated_at'], 'description': 'Retrieve order details and status.'}, {'name': '/orders/{order_id}/cancel', 'method': 'POST', 'inputs': ['order_id', 'auth_token', 'reason (optional)'], 'outputs': ['order_id', 'status', 'result'], 'description': 'Cancels an order and triggers compensation steps in the Saga (inventory release, cart restore).'}, {'name': '/orders/{order_id}/status', 'method': 'GET', 'inputs': ['order_id', 'auth_token'], 'outputs': ['order_id', 'status', 'progress_log[]'], 'description': 'Returns the current status and saga progress for the order.'}], 'user_stories': ['12'], 'parameters': ['order_id', 'user_id', 'cart_id', 'items', 'status', 'pickup_date', 'pickup_company_id', 'created_at', 'updated_at'], 'description': 'Handles order lifecycle and orchestration of multi-step operations across services using the Saga pattern. Each order is an aggregate in its own datastore. Publishes domain events (OrderCreated, OrderConfirmed, OrderCancelled) for other services to respond (e.g., Product Catalog to decrement inventory).'}, {'name': 'Administration Service', 'endpoints': [{'name': '/admin/users/{user_id}', 'method': 'DELETE', 'inputs': ['admin_auth_token', 'user_id', 'reason (optional)'], 'outputs': ['result', 'deleted_user_id'], 'description': 'Allows administrators to delete malicious or problematic users (story 25). Emits UserDeleted domain event so other services can clean up related data (carts, orders, profiles).'}, {'name': '/admin/users', 'method': 'GET', 'inputs': ['admin_auth_token', 'filters (role, created_before, suspicious_flag)'], 'outputs': ['users[] (user_id, email, role, created_at, status)'], 'description': 'List users for administration and moderation.'}], 'user_stories': ['25'], 'parameters': ['admin_auth_token', 'user_id', 'deleted_user_id', 'reason', 'status'], 'description': 'Provides administrative actions and aggregates admin operations. Owns an admin datastore to persist audit logs and administrative decisions. Emits domain events upon user deletion to propagate changes.'}], 'patterns': [{'group_name': 'Auth Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['Authentication Service'], 'explaination': 'Authentication stores credentials and session tokens and must be isolated for security and independent scaling. The retrieved context recommended Database per Service and aggregate modelling for authentication, so we keep a dedicated datastore.'}, {'group_name': 'Profiles Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['User Profile Service'], 'explaination': 'User and company profile data are updated independently and must be isolated; aggregate pattern applies to user and company profiles as suggested in the context.'}, {'group_name': 'Product Inventory', 'implementation_pattern': 'database per service', 'involved_microservices': ['Product Catalog Service'], 'explaination': 'Products require their own datastore for inventory control. Context recommended Database per Service and Aggregate; domain events are used to notify other services of changes, so Product Catalog owns its data.'}, {'group_name': 'Company Management', 'implementation_pattern': 'database per service', 'involved_microservices': ['Agricultural Company Service'], 'explaination': 'Company registration and location data should be autonomous for scalability and to publish CompanyRegistered/Updated events. Context recommended Database per Service and Aggregate.'}, {'group_name': 'Cart Isolation', 'implementation_pattern': 'database per service', 'involved_microservices': ['Cart Service'], 'explaination': 'Carts are frequently updated, need low-latency writes and isolation from other services; modeled as aggregates per user. Context recommends a dedicated cart datastore and domain events for item changes.'}, {'group_name': 'Order Orchestration', 'implementation_pattern': 'saga', 'involved_microservices': ['Order Service', 'Product Catalog Service', 'Cart Service', 'User Profile Service', 'Agricultural Company Service', 'Administration Service', 'Authentication Service'], 'explaination': 'Creating an order requires coordinating multiple services (reserve inventory, confirm pickup with company, clear cart). The context explicitly recommended Saga for Order to manage multi-step distributed transactions with compensation steps.'}, {'group_name': 'Cross-Service Queries', 'implementation_pattern': 'api composition', 'involved_microservices': ['Product Catalog Service', 'Agricultural Company Service', 'User Profile Service', 'Cart Service', 'Order Service'], 'explaination': 'Displaying combined views (company with its products, user orders with product details) will be implemented via API Composition: the frontend (or aggregator) will call multiple services and compose responses. The context recommends API Composition and optionally CQRS for heavier reporting.'}, {'group_name': 'Event-driven consistency', 'implementation_pattern': 'domain event', 'involved_microservices': ['Product Catalog Service', 'Cart Service', 'Order Service', 'User Profile Service', 'Agricultural Company Service', 'Administration Service'], 'explaination': 'Domain events (ProductAdded, ProductUpdated, ProductRemoved, OrderCreated, CompanyRegistered, UserDeleted) keep services loosely-coupled and allow eventual consistency. The context recommended domain events for product and company changes and admin actions.'}, {'group_name': 'Query optimization (optional)', 'implementation_pattern': 'cqrs', 'involved_microservices': ['Product Catalog Service', 'Order Service', 'User Profile Service'], 'explaination': 'For complex queries such as dashboards or combined views, materialized read models may be maintained. The context suggested CQRS for complex queries; this group would maintain read-optimized views aggregated from multiple domain events.'}], 'datastore': [{'datastore_name': 'auth_db', 'associated_microservices': ['Authentication Service'], 'description': 'Stores user credentials (hashed), refresh tokens, persistent sessions and auth audit logs. Chosen because many user stories require registration, login, remember-me and logout (stories 1-4,17-20,22-24). Database per service is required for security and isolation.'}, {'datastore_name': 'profiles_db', 'associated_microservices': ['User Profile Service'], 'description': 'Holds user profile aggregates and company profile snapshots. Influenced by stories 5 and 21 requiring viewing and updating personal/company information. Database per service allows independent updates and aggregate transactions.'}, {'datastore_name': 'product_catalog_db', 'associated_microservices': ['Product Catalog Service'], 'description': 'Contains product aggregates (product details, price, quantity, hot flag). Domain events are emitted on changes to support cart and order flows. Chosen because stories 6,8,14-16 require product listing and inventory operations; database per service supports inventory isolation.'}, {'datastore_name': 'company_db', 'associated_microservices': ['Agricultural Company Service'], 'description': 'Stores agricultural company aggregates, locations (lat/long), contact and opening hours. Influenced by stories 7,13,17,21 (registration, discovery, maps). Database per service supports search and emits domain events.'}, {'datastore_name': 'cart_db', 'associated_microservices': ['Cart Service'], 'description': 'Stores cart aggregates per user with items, quantities and timestamps. Required by stories 9-11 for adding/removing/viewing cart. Domain events optionally published when items change; database per service supports fast updates.'}, {'datastore_name': 'orders_db', 'associated_microservices': ['Order Service'], 'description': 'Persists order aggregates and saga state (progress logs, compensating actions). Influenced by story 12: order completion and pickup date selection requires coordination. Saga orchestration requires storing state and events for compensation.'}, {'datastore_name': 'admin_db', 'associated_microservices': ['Administration Service'], 'description': 'Stores admin actions, audit logs, moderation decisions and lists of banned/deleted users. Story 25 (delete malicious user) required persistent admin decisions and emission of UserDeleted events to allow other services to purge or anonymize data.'}, {'datastore_name': 'read_models_db (optional CQRS)', 'associated_microservices': ['Product Catalog Service', 'Order Service', 'User Profile Service'], 'description': 'Materialized read views for combined queries (e.g., company with products, user order history with product details). Influenced by API Composition and the optional CQRS recommendation for optimized cross-service queries and reporting.'}]}
"""


import asyncio

wf = DalleCodeWorkflow(timeout=None)

async def main():
    res = await wf.run(input_json=INPUT_JSON_EXAMPLE)
    print("Final result:", res)

asyncio.run(main())