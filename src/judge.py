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
from llama_index.core.prompts import RichPromptTemplate, PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram

import streamlit as st
import json

from typing import Any

from output import DalleOutput
from utils import single_quote_to_double, to_dict
from prompts import (
    FIND_CONTEXT_TEXT,
    JUDGE_TEXT
)


from archi import CitationQueryEngineWorkflow, ContextRetrievedEvent

from pydantic import BaseModel, Field
from typing import List

class JudgedMicroservice(BaseModel):
    """Model for a microservice in the judged architecture."""
    name: str = Field(..., description="Name of the microservice")
    is_correct: bool = Field(..., description="Indicates if the microservice is correct")
    explaination: str = Field(..., description="Brief description of the microservice and its purpose")

class JudgeOutput(BaseModel):
    """
    Output model for the DalleJudge workflow.
    Contains the final architecture in JSON format.
    """
    microservices: List[JudgedMicroservice] = Field(..., description="List of microservices in the architecture")

class DalleJudge(Workflow):
    
    @step
    async def retrieve_context(self, ctx: Context, ev: StartEvent) -> ContextRetrievedEvent:
        print("Retrieving context for microservices:", ev.microservices_list)
        specs =  ev.specs
        user_stories =  ev.user_stories
        retriever = ev.retriever
        llm = OpenAI(model="gpt-4.1")  # Use the appropriate model for your use case
        microservice_list = ev.microservices_list
        #sllm = llm.as_structured_llm(output_cls=DalleOutput)

        find_context_template = RichPromptTemplate(FIND_CONTEXT_TEXT)
        
        context_query = find_context_template.format(
            specs=specs,
            user_stories=user_stories,
            microservices_list=ev.microservices_list
        )



        citation_workflow = CitationQueryEngineWorkflow(timeout=None)
        context_response = await citation_workflow.run(query=context_query, retriever=retriever)

        print("Context response:", context_response)
        
        

        #use_context_template = RichPromptTemplate(USE_CONTEXT_TEXT)
    

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=JudgeOutput,
            prompt_template_str=JUDGE_TEXT,
            verbose=True,
            llm=llm,
        )

        
        output = program(
            specs=specs,
            context=str(context_response),
            user_stories=user_stories,
            microservice_list=microservice_list,
        )

        print("Output from LLM:", to_dict(output))

        #resp = single_quote_to_double(str(sllm.complete(final_query).raw.dict()))
        #print("Final response:", resp)
        
        
        return ContextRetrievedEvent(context=single_quote_to_double(str(to_dict(output))))

    @step
    async def format_output(self, ctx: Context, ev: ContextRetrievedEvent) -> StopEvent:
        """Format the final output into a structured JSON format."""
        
        return StopEvent(result=json.dumps(ev.context, indent=2, ensure_ascii=False))




from gen import get_retrievers

S = """
4-by-4 is an online platform that allows users to play the classic adversarial (m, n, k) games with gravity in a digital environment. The website features a standard login system, enabling users to create accounts, log in, and track their game statistics. Players can customize their gaming experience by adjusting board sizes and implementing chess-like timing settings to add a competitive edge. The platform is designed to provide a seamless and engaging experience for enthusiasts of all skill levels.
"""
US = """1. As a Connect Four fan, I want to play Connect Four online against other users so that I can enjoy the game more or less competitively.
2. As a player, I want to be able to register to the site so that I can customize my username.
3. As a player, I want to be able to log in the site so that I can access the same account every time.
4. As a user, I want to my credentials to be remembered so that I can access the site without typing them every time.
5. As a user, I want to be able to logout, so that other people on the same computer can't access my account.
6. As a user, I want to have helpful navigation buttons on all pages, so that it's easy to find my way around the site.
7. As a user, I want to look at my own profile, so that I can see details about my account.
8. As a user, I want to be able to change my username, so that I am not bound to a single name option forever.
9. As a user, I want to be able to change my password, so that I can be sure it is secure.
10. As a casual player, I want to be able to look at my aggregate statistics, so that I can estimate my skills and track my performance over time.
11. As a competitive player, I want to look at the winners of my previous games, so that I can see if there are common patterns between losses/wins.
12. As a competitive player, I want to look at replays of my previous matches, so that I can improve my gameplay.
13. As a player, I want to look at the settings (dimension and timing) of previous games, so that I can easily filter novel games.
14. As a competitive player, I want to look at the replays of other player's previous games, so that I can learn study their gameplay.
15. As a competitive player, I want to be able to know who created previous matches, to learn patterns in the games used.
16. As a player, I want to be able to look at active challenges, so that I can see if there's any open match I can join.
17. As a casual player, I want to be able to see who created a challenge, so that I can choose to play only with people I know.
18. As a competitive player, I want to look at a challenge creator's profile, so that I can check out whether they are a good player.
19. As a player, I want to be able to set varying board sizes when creating the challenge, to have a more novel experience
20. As a competitive player, I want to set chess-like timing settings (e.g., blitz, rapid, or custom time limits) so that I can challenge myself and others under time pressure.
21. As a player, I want all of the game logic to be handled automatically and fairly so that it isn't possible to cheat.
22. As a player, I want to be able to see whose turn it is, so that I am not waiting aimlessly.
23. As a player, I want to be able to chat with my opponent, so that I can have a conversation with them about the game.
24. As a competitive player, I want to view how much time me or my opponent have left, so that I can manage my time-per-move more effectively.
25. As a player, I want to click on the grid, so that I can place a piece during my turn.
26. As a player, I want to have the option to concede, so that I can end a losing gaming without having to wait.
27. As a player, I want to be able to offer a and accept a draw, so that I end a drawing game without having to wait.
28. As a competitive player, I want to be able to retire a draw offer if the opponent doesn't accept it, so that I can still try to win the game if they miss-play.
29. As a player, I want to be able to deny a draw offer, so that I can go for a win instead of settling for a draw.
30. As a player, I want to be able to immediately look at the match replay once it ends, so that I can review what happened.
31. As a beginner player, I want to be able to easily read who won the game and how it ended, so that I have a clear situation of whether I have won or not and how.
32. As a avid player, I want to have a button to exit the game once it ends, so that I can quickly start another one.
33. As a player, I want to have a button to go back to the profile from a replay, so that I am not forced to go through the entire replay.
34. As a player, I want to know how many moves there were in a previous match, so that I know how long it's going to take.
35. As a player, I want to be able to go through the replay move-by-move, so that I can see what happened gradually.
36. As a competitive Player, I want to be able to go back to the previous move in the replay, so that I can better analyse what happened more carefully.
37. As a beginner player, I want to be able to easily read who won the game and how it ended, so that I have a clear situation of who won and how."""
MSL ="""{"microservices": [{"name": "User Management Service", "endpoints": [{"name": "/register", "method": "POST", "inputs": ["email", "password"], "outputs": ["registration result"], "description": "takes user email and password as inputs and outputs the registration result"}, {"name": "/login", "method": "POST", "inputs": ["email", "password"], "outputs": ["login result"], "description": "takes user email and password as inputs and outputs the login result"}, {"name": "/logout", "method": "POST", "inputs": [], "outputs": ["logout result"], "description": "logs out the user"}, {"name": "/profile", "method": "GET", "inputs": [], "outputs": ["user profile"], "description": "retrieves user profile details"}, {"name": "/change-username", "method": "PUT", "inputs": ["new_username"], "outputs": ["username change result"], "description": "changes the user's username"}, {"name": "/change-password", "method": "PUT", "inputs": ["new_password"], "outputs": ["password change result"], "description": "changes the user's password"}], "user_stories": ["2", "3", "4", "5", "7", "8", "9"], "parameters": ["email", "password", "new_username", "new_password"], "description": "Handles user registration, login, logout, profile management, and credential storage."}, {"name": "Game Management Service", "endpoints": [{"name": "/create-game", "method": "POST", "inputs": ["board_settings", "timing_settings"], "outputs": ["game_id"], "description": "creates a new game with specified settings"}, {"name": "/update-game-state", "method": "PUT", "inputs": ["game_id", "new_state"], "outputs": ["update result"], "description": "updates the state of a game"}], "user_stories": ["1", "19", "20", "21", "22", "25", "26"], "parameters": ["board_settings", "timing_settings", "game_id", "new_state"], "description": "Manages game creation, game logic, board settings, timing settings, and game state updates."}, {"name": "Challenge Service", "endpoints": [{"name": "/active-challenges", "method": "GET", "inputs": [], "outputs": ["list of active challenges"], "description": "retrieves a list of active challenges"}, {"name": "/create-challenge", "method": "POST", "inputs": ["challenge_details"], "outputs": ["challenge_id"], "description": "creates a new challenge with specified details"}, {"name": "/join-challenge", "method": "POST", "inputs": ["challenge_id"], "outputs": ["join result"], "description": "allows a user to join a challenge"}], "user_stories": ["16", "17", "18", "19", "20"], "parameters": ["challenge_details", "challenge_id"], "description": "Manages active challenges, challenge creation, joining challenges, and challenge metadata."}, {"name": "Statistics and History Service", "endpoints": [{"name": "/user-statistics", "method": "GET", "inputs": [], "outputs": ["user statistics"], "description": "retrieves user statistics"}, {"name": "/game-winners", "method": "GET", "inputs": [], "outputs": ["list of game winners"], "description": "retrieves a list of game winners"}, {"name": "/match-settings", "method": "GET", "inputs": ["game_id"], "outputs": ["settings for a specific match"], "description": "retrieves settings for a specific match"}], "user_stories": ["10", "11", "13", "15", "34"], "parameters": ["game_id"], "description": "Tracks and provides access to user statistics, game winners, match settings, and game history."}, {"name": "Replay Service", "endpoints": [{"name": "/replay", "method": "GET", "inputs": ["game_id"], "outputs": ["game replay"], "description": "retrieves the replay of a specific game"}, {"name": "/move-by-move", "method": "GET", "inputs": ["game_id", "move_number"], "outputs": ["specific move in the replay"], "description": "retrieves a specific move in the replay of a game"}], "user_stories": ["12", "14", "30", "33", "35", "36"], "parameters": ["game_id", "move_number"], "description": "Handles storage, retrieval, and navigation of game replays including move-by-move playback and replay metadata."}, {"name": "Game Interaction Service", "endpoints": [{"name": "/chat", "method": "POST", "inputs": ["message"], "outputs": ["chat message"], "description": "allows users to chat with each other during a game"}, {"name": "/turn-management", "method": "GET", "inputs": ["game_id"], "outputs": ["current turn"], "description": "retrieves information about whose turn it is in a game"}], "user_stories": ["23", "24", "27", "28", "29"], "parameters": ["message", "game_id"], "description": "Manages in-game interactions such as chat, draw offers, conceding, and turn management."}, {"name": "Navigation Service", "endpoints": [{"name": "/exit-game", "method": "POST", "inputs": ["game_id"], "outputs": ["exit result"], "description": "allows a user to exit a game"}], "user_stories": ["6", "32", "31", "37"], "parameters": ["game_id"], "description": "Provides navigation elements and user interface helpers across the platform."}], "patterns": [{"group_name": "Data Consistency", "implementation_pattern": "Saga", "involved_microservices": ["Challenge Service", "Game Management Service"], "explaination": "I chose this pattern to maintain data consistency across services during distributed transactions like challenge creation and game management."}, {"group_name": "Queries", "implementation_pattern": "API Composition", "involved_microservices": ["Statistics and History Service"], "explaination": "API Composition is used to aggregate data for user statistics and game history queries."}, {"group_name": "Queries", "implementation_pattern": "CQRS", "involved_microservices": ["Statistics and History Service"], "explaination": "CQRS is used to maintain materialized views for complex read scenarios like statistics and replay data."}, {"group_name": "Data Consistency", "implementation_pattern": "Transactional Outbox", "involved_microservices": ["Game Management Service"], "explaination": "Transactional Outbox is used to reliably send messages as part of database transactions for game state changes."}], "datastore": [{"datastore_name": "User Management Database", "associated_microservices": ["User Management Service"], "description": "Database for storing user credentials, profiles, and related information."}, {"datastore_name": "Game Management Database", "associated_microservices": ["Game Management Service"], "description": "Database for managing game state, logic, board settings, and timing settings."}, {"datastore_name": "Challenge Database", "associated_microservices": ["Challenge Service"], "description": "Database for storing active challenges, challenge metadata, and related information."}, {"datastore_name": "Statistics and History Database", "associated_microservices": ["Statistics and History Service"], "description": "Database for tracking user statistics, game winners, match settings, and game history."}, {"datastore_name": "Replay Database", "associated_microservices": ["Replay Service"], "description": "Database for storing game replays, move-by-move data, and replay metadata."}]}
"""

async def main():
    retrievers = get_retrievers()
    wf = DalleJudge(timeout=None)
    result_event = await wf.run(retriever=retrievers, specs=S, user_stories=US, microservices_list=MSL)
    print("Workflow completed successfully!")
    print("Result:", json.loads(result_event))


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Apply nest_asyncio to allow nested event loop
    import asyncio
    asyncio.run(main())