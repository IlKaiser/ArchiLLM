# SYSTEM DESCRIPTION:

ExamRush is a mobile application designed to help students study interactively through multiple-choice quizzes. The application allows users to create a profile, choose a question deck, and answer questions using both touch and the phone's motion sensor. The system integrates Firebase Authentication for user registration and login, and provides user profile management, including profile picture upload and cartoonization using OpenCV. The backend is Docker-based, utilizing Flask for the CRUD interface, MinIO for image storage, and MongoDB for data management. The application supports multi-user functionality, an interactive and animated UI, and utilizes the phone's accelerometer for navigation between questions.

# USER STORIES:

1. As a new user, I want to register an account using my email and password so that I can access the application.
2. As a user, I want to log in using my credentials so that I can resume using the application.
3. As a user, I want to upload and edit my profile picture so that I can personalize my account.
4. As a user, I want to apply a cartoon filter to my profile picture so that it looks fun and unique.
5. As a user, I want an interactive and animated user interface so that the application is engaging and easy to use.
6. As a student, I want to browse and select from multiple question decks so that I can choose a topic to study.
7. As a student, I want to answer multiple-choice questions interactively so that I can test my knowledge.
8. As a student, I want to search for decks using a search bar so that I can quickly find decks by topic, subject, or keyword.
9. As a student, I want to see statistics about my performance (e.g., average score, strengths, weaknesses, progress over time) so that I can track my knowledge and identify areas for improvement.
10. As a teacher, I want to create and upload multiple-choice question decks so that my students can use them for studying.
11. As a teacher, I want to test the decks I upload by answering the questions myself so that I can ensure they are accurate and functional.


# CONTAINERS:

## CONTAINER_NAME: server-api

### DESCRIPTION:  
This container hosts the Flask-based REST API backend for the ExamRush application. It handles user authentication, profile management, question deck interactions, and statistics tracking. It connects to MongoDB for data storage and MinIO for image storage.

### USER STORIES:
1. As a new user, I want to register an account using my email and password so that I can access the application.  
2. As a user, I want to log in using my credentials so that I can resume using the application.  
3. As a user, I want to upload and edit my profile picture so that I can personalize my account.  
4. As a user, I want to apply a cartoon filter to my profile picture so that it looks fun and unique.  
6. As a student, I want to browse and select from multiple question decks so that I can choose a topic to study.  
7. As a student, I want to answer multiple-choice questions interactively so that I can test my knowledge.  
8. As a student, I want to search for decks using a search bar so that I can quickly find decks by topic, subject, or keyword.  
9. As a student, I want to see statistics about my performance (e.g., average score, strengths, weaknesses, progress over time) so that I can track my knowledge and identify areas for improvement.  
10. As a teacher, I want to create and upload multiple-choice question decks so that my students can use them for studying.  
11. As a teacher, I want to test the decks I upload by answering the questions myself so that I can ensure they are accurate and functional.

### PORTS:  
5000:5000

### PERSISTENCE EVALUATION:  
The container itself is stateless, but it relies on MongoDB for persistent data storage (e.g., user profiles, question decks, statistics) and MinIO for persistent image storage (e.g., profile pictures).

### EXTERNAL SERVICES CONNECTIONS:  
- MongoDB: Used for storing user data, question decks, and statistics.  
- MinIO: Used for storing and retrieving profile pictures.  
- Firebase Authentication: Used for user registration and login.

### MICROSERVICES:

#### MICROSERVICE: flask-api
- TYPE: backend  
- DESCRIPTION: The core Flask application that provides REST API endpoints for user authentication, profile management, deck interactions, and statistics.  
- PORTS: 5000:5000  
- TECHNOLOGICAL SPECIFICATION:  
  - Built with Python and Flask.  
  - Uses Flask-RESTful for API development.  
  - Connects to MongoDB via PyMongo and MinIO via the MinIO Python SDK.  
- SERVICE ARCHITECTURE:  
  - Follows a RESTful architecture with endpoints for CRUD operations.  
  - Stateless design, with all persistent data stored in MongoDB and MinIO.  

- ENDPOINTS:  

  | HTTP METHOD | URL | Description | User Stories |
  | ----------- | --- | ----------- | ------------ |
  | POST        | /api/register | Register a new user | 1 |
  | GET         | /api/users/<user_id> | Retrieve user information | 2, 3, 4 |
  | DELETE      | /api/users/<user_id> | Delete a user | - |
  | PUT         | /api/users/<user_id> | Update user statistics | 9 |
  | POST        | /api/users | Retrieve user by email | 2 |
  | GET         | /api/decks | Retrieve available question decks | 6, 8 |
  | POST        | /api/decks | Upload a new question deck (teacher only) | 10 |
  | GET         | /api/decks/<deck_id> | Retrieve questions for a specific deck | 7 |
  | GET         | /api/users/<user_id>/profile-image | Retrieve user profile image | 3, 4 |
  | POST        | /api/users/<user_id>/profile-image | Upload user profile image | 3, 4 |

- DB STRUCTURE:  

  **_users_** : | **_id_** | user_id | email | name | surname | score | role | average_score | played_games | image |  
  **_decks_** : | **_id_** | title | description | teacher_id | cards |  
  **_cards_** : | **_id_** | question | options | correct_answer |  
  **_images_** : | **_id_** | filename | url |  

---

### Flask API Code Integration:
The Flask API code provided implements the following key functionalities:
1. **User Registration**:  
   - Endpoint: /api/register (POST)  
   - Registers a new user with details like email, name, and surname.  
   - Stores the user in the `users` collection in MongoDB.

2. **User Information Retrieval**:  
   - Endpoint: /api/users/<user_id> (GET)  
   - Retrieves user information by `user_id`.  
   - Endpoint: /api/users (POST)  
   - Retrieves user information by email.

3. **User Deletion**:  
   - Endpoint: /api/users/<user_id> (DELETE)  
   - Deletes a user by `user_id`.

4. **User Statistics Update**:  
   - Endpoint: /api/users/<user_id> (PUT)  
   - Updates user statistics like `played_games`, `score`, and `average_score`.

5. **Deck Management**:  
   - Endpoint: /api/decks (GET)  
   - Retrieves all available decks.  
   - Endpoint: /api/decks (POST)  
   - Creates a new deck (teacher only).  
   - Endpoint: /api/decks/<deck_id> (GET)  
   - Retrieves a specific deck by its ID.

6. **Profile Image Management**:  
   - Endpoint: /api/users/<user_id>/profile-image (GET)  
   - Retrieves the user's profile image from MinIO.  
   - Endpoint: /api/users/<user_id>/profile-image (POST)  
   - Uploads a new profile image to MinIO and updates the user's record in MongoDB.


CONTAINER_NAME: server-mongodb

DESCRIPTION:
This container hosts the MongoDB database used for storing user profiles, question decks, and performance statistics.

USER STORIES:
- As a new user, I want to register an account using my email and password so that I can access the application.
- As a user, I want to log in using my credentials so that I can resume using the application.
- As a user, I want to upload and edit my profile picture so that I can personalize my account.
- As a student, I want to browse and select from multiple question decks so that I can choose a topic to study.
- As a student, I want to answer multiple-choice questions interactively so that I can test my knowledge.
- As a student, I want to see statistics about my performance (e.g., average score, strengths, weaknesses, progress over time) so that I can track my knowledge and identify areas for improvement.
- As a teacher, I want to create and upload multiple-choice question decks so that my students can use them for studying.
- As a teacher, I want to test the decks I upload by answering the questions myself so that I can ensure they are accurate and functional.

PORTS:
27017:27017

PERSISTENCE EVALUATION:
Data is persisted in MongoDB using volumes to ensure durability and availability. This includes user profiles, question decks, and performance statistics.

EXTERNAL SERVICES CONNECTIONS:
- Flask API: The Flask backend connects to MongoDB to store and retrieve data.

MICROSERVICES:

#### MICROSERVICE: mongodb
- TYPE: database
- DESCRIPTION: The MongoDB instance used for storing all application data, including user profiles, question decks, and statistics.
- PORTS: 27017:27017
- TECHNOLOGICAL SPECIFICATION:
  - Uses MongoDB for NoSQL data storage.
  - Data is stored in collections such as users, decks, and stats.
- SERVICE ARCHITECTURE:
  - Acts as the primary data store for the application.
  - Supports horizontal scaling with sharding if needed.
- DB STRUCTURE:

  **_users_** : | **_id_** | email | password_hash | profile_picture_url |  
  **_decks_** : | **_id_** | name | description | questions | created_by |  
  **_stats_** : | **_id_** | user_id | deck_id | score | timestamp |  

---

CONTAINER_NAME: server-minio

DESCRIPTION:
This container hosts the MinIO object storage service used for storing and retrieving profile pictures.

USER STORIES:
- As a user, I want to upload and edit my profile picture so that I can personalize my account.
- As a user, I want to apply a cartoon filter to my profile picture so that it looks fun and unique.

PORTS:
9000:9000

PERSISTENCE EVALUATION:
Profile pictures are stored persistently in MinIO buckets. Data is retained even if the container is restarted.

EXTERNAL SERVICES CONNECTIONS:
- Flask API: The Flask backend connects to MinIO to upload and retrieve profile pictures.

MICROSERVICES:

#### MICROSERVICE: minio
- TYPE: storage
- DESCRIPTION: The MinIO object storage service used for storing profile pictures.
- PORTS: 9000:9000
- TECHNOLOGICAL SPECIFICATION:
  - Uses MinIO for S3-compatible object storage.
  - Stores profile pictures in a dedicated bucket.
- SERVICE ARCHITECTURE:
  - Acts as a centralized storage solution for images.
  - Supports scalability and high availability.

