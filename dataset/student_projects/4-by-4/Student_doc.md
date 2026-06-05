# SYSTEM DESCRIPTION:
4-by-4 is an online platform that allows users to play the classic adversarial (m, n, k) games with gravity in a digital environment. The website features a standard login system, enabling users to create accounts, log in, and track their game statistics. Players can customize their gaming experience by adjusting board sizes and implementing chess-like timing settings to add a competitive edge. The platform is designed to provide a seamless and engaging experience for enthusiasts of all skill levels.

# USER STORIES:
1. As a Connect Four fan, I want to play Connect Four online against other users so that I can enjoy the game more or less competitively.
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
37. As a beginner player, I want to be able to easily read who won the game and how it ended, so that I have a clear situation of who won and how.

# CONTAINERS:

## CONTAINER_NAME: db

### DESCRIPTION:
The db container hosts a PostgreSQL database that stores all persistent data for the 4-by-4 platform. It manages user accounts, game statistics, challenges, and other relevant data. The database is initialized with tables for users, games, and challenges, and it is accessed by both the web and websocket containers for data retrieval and storage.

### USER STORIES:
2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15

### PORTS: 
PostgreSQL default port: 5432 (internal use only, not exposed externally).

### PERSISTENCE EVALUATION
The db container is responsible for persistent data storage. All user accounts, game histories, and challenges are stored in the PostgreSQL database. Data persists across container restarts and deployments, ensuring continuity for users.

### EXTERNAL SERVICES CONNECTIONS
None. The db container is only accessed internally by the web and websocket containers.

### MICROSERVICES:

#### MICROSERVICE: PostgreSQL Database

- TYPE: backend
- DESCRIPTION: The PostgreSQL database stores all persistent data for the 4-by-4 platform, including user accounts, game histories, and challenges.
- PORTS: 5432 (internal)
- TECHNOLOGICAL SPECIFICATION:
	Database: PostgreSQL
    ORM: PDO (PHP Data Objects) for database interactions.
- SERVICE ARCHITECTURE:
    The database is accessed via the Database class, which provides a singleton instance for connection management and table initialization.
- DB STRUCTURE:

    users:
	| id | username | password_hash | token |
	|---|---|---|---|
    
	games:
    | id | player1_id | player2_id | starting_player_id | winner_id | rows | cols| win | end_type | start_time | end_time | time | increment | move_sequence |
	|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
    
	challenges:
    | id | user_id | rows | cols | win | time | increment |
	|---|---|---|---|---|---|---|

## CONTAINER_NAME: web

### DESCRIPTION
The web container handles all HTTP connections for the 4-by-4 platform. It serves HTML, CSS, and JavaScript files to the client and provides backend functionality for authentication and token handling. It communicates with the db container to retrieve and store user and game data, and with the redis container for handling volatile session data.

### USER STORIES:
All of them, because it handles the main interface of the website.

### PORTS:
HTTP: 8080 (exposed externally for client access).

### PERSISTENCE EVALUATION
The web container does not store persistent data directly. It relies on the db container for all data persistence.

### EXTERNAL SERVICES CONNECTIONS
Communicates with the db container for data storage and retrieval and with redis for session storage.

### MICROSERVICES:

#### MICROSERVICE: Authentication Service
- TYPE: backend
- DESCRIPTION: Handles user authentication, including login and token validation
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION:
	- Language: PHP
	- Web Server: Apache
	- Database: PostgreSQL (via PDO)
- SERVICE ARCHITECTURE: Provides RESTful endpoints for authentication and token handling.
- ENDPOINTS:
	|HTTP METHOD|URL|Description|User Stories|
	|---|---|---|---|
	POST|`/login.php`|Handles user logins and logouts|2, 3, 5
	GET|`/check-token.php`|Validates user tokens for session management.|3, 4

#### MICROSERVICE: Profile Handling Service
- TYPE: backend
- DESCRIPTION: Handles profile data retreival and updates
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION:
	- Language: PHP
	- Web Server: Apache
	- Database: PostgreSQL (via PDO)
- SERVICE ARCHITECTURE: Provides RESTful endpoints for profile data retreival and updates
- ENDPOINTS:
	|HTTP METHOD|URL|Description|User Stories|
	|---|---|---|---|
	GET|`/profile.php`|Handles retreival of profile data|7, 10, 11, 12, 13, 14, 15, 18
	POST|`/update-profile.php`|Updates own profile's data|8, 9

#### MICROSERVICE: Frontend Service
- TYPE: frontend
- DESCRIPTION: Serves HTML, CSS and JavaScript files to the client for rendering the 4-by-4 platform.
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION:
	- Languages: HTML, CSS, Javascript
	- Web Server: Apache
- SERVICE ARCHITECTURE: Static file serving with dynamic content loaded via Fetch API and WebSocket connections.
- PAGES:
	Name|Description|Related Microservice|User Stories
	---|---|---|---
	Index|Landing page, mainly used for creating and joining game challenges|Authentication Service, Websocket Service, Session Storage Service|1, 4, 6, 16, 17, 18, 19, 29
	Register|Page for registering a new user account|PostgreSQL Database, Session Storage Service|2, 6
	Login|Page for logging into an existing account|Authentication Service, Session Storage Service|3, 6
	Game|Page where matches are played|Authentication Service, Websocket Service, Session Storage Service|1, 6, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32 
	Profile|Page for viewing players' game history and performance and editing own data|PostgreSQL Database, Authentication Service, Session Storage Service, Profile Handling Service|6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18
	Replay|Page for replaying a past match move by move|PostgreSQL Database, Websocket Service| 6, 30, 33, 34, 35, 36, 37

## CONTAINER_NAME: websocket
### DESCRIPTION:
The websocket container handles real-time communication between the server and clients. It manages matchmaking, game logic, and real-time updates for ongoing games. It communicates with the db container to retrieve and update game data and with the redis container for session data.
### USER STORIES:
1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 20, 30, 31
### PORTS:
WebSocket: 8081 (exposed externally for real-time communication)

### PERSISTENCE EVALUATION:
The websocket container does not store persistent data directly. It relies on the db container for all data persistence.

### EXTERNAL SERVICES CONNECTIONS:
Communicates with the db container for data storage and retrieval and updates and with redis for session storage.

### MICROSERVICES:

#### MICROSERVICE: WebSocket Service
- TYPE: backend
- DESCRIPTION: Manages real-time communication for matchmaking, game logic and turn-based updates
- PORTS: 8081
- TECHNOLOGICAL SPECIFICATION:
	- Protocol: WebSocket
	- Language: PHP
- SERVICE ARCHITECTURE:
	Handles WebSocket connections for real-time game updates
- ENDPOINTS:
	- WebSocket URL: `ws://<server-address>:8081`

## CONTAINER_NAME: redis

### DESCRIPTION:
The redis container provides session storage for all PHP pages, enabling efficient session management across the 4-by-4 platform. It helps in maintaining session persistence, reducing database load, and improving response times by storing temporary session data in memory.

### USER STORIES:
The redis container is indirectly involved in almost all user stories, because session storage is used troughout the webiste troughout navigation.

### PORTS:
Redis default port: 6379 (internal use only, not exposed externally).

### PERSISTENCE EVALUATION:
The redis container stores session data temporarily. It is not responsible for long-term data persistence, as session data is volatile and cleared upon container restarts.

### EXTERNAL SERVICES CONNECTIONS:
- Communicates with the web and websocket containers for session management and caching.

### MICROSERVICES:

#### MICROSERVICE: Session Storage Service

- TYPE: backend
- DESCRIPTION: Manages session storage for user authentication and temporary data caching.
- PORTS: 6379 (internal)
- TECHNOLOGICAL SPECIFICATION:
  - Technology: Redis (in-memory data store)
  - PHP Session Handler: Uses Redis as a session storage backend instead of file-based storage
- SERVICE ARCHITECTURE:
  - PHP applications connect to Redis via `session.save_handler = redis`.
