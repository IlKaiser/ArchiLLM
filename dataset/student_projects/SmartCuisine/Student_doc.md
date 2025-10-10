\# SYSTEM DESCRIPTION:

Smart Cuisine aims to develop an application to discover new recipes and check their nutritional values in order to monitor the daily intake of macronutrients.  
This application aims to improve the quality of the food intake and to give new ideas to people who want to eat in a healthier way, without giving up on tasty meals.  
The application meets the needs of the users with dietary restrictions given by health issues, intolerances and religious or moral choices.  
To achieve the previous purposes the system allows short-term and medium-term meal planning for the following days.  
The type of users which could be interested about this application are personal trainers, people who can’t afford a dietist or prefer to plan their meals by themselves.  
Another possible user could be a person who uses the application to write down his shopping list and check the nutritional values of the items in the list.

\# USER STORIES:

1\) As a not registered user, I want to subscribe with email and password so that being a registered user. 

2\) As a registered user, I want to log in with email and password so that logging in my account. 

3\) As a registered user, I want to access my profile so that I can visualize my personal data.  
   
4\) As a registered user, I want to delete my account so that being no more a registered user. 

5\) As a registered user, I want to modify my email address so that I can update it. 

6\) As a registered user, I want to modify my password so that I can update it. 

7\) As a registered user, I want to modify my gender so that I can update it. 

8\) As a registered user, I want to add my ingredients to the storage so that I can keep track of the ingredients I have at home. 

9\) As a registered user, I want to delete an ingredient from my storage so that I can delete an ingredient I used for a recipe. 

10\) As a registered user, I want to search for recipes so that I can find ideas for meals.   
11\) As a registered user, I want to save recipes so that I can access them easily in the future. 

12\) As a registered user, I want to add the ingredients to my shopping list so that I can keep track of what I need to buy. 

13\) As a registered user, I want to delete a saved recipe so that I can remove it if I don't like it. 

14\) As a registered user, I want to search recipes containing a specific ingredient so that I can find something I can cook with the ingredients I have in storage. 

15\) As a registered user, I want to move the ingredients from my shopping list to my ingredients storage so that I can keep track of what I bought. 

16\) As a registered user, I want to delete an ingredient from my shopping list so that I can remove it if I already have it. 

17\) As a registered user, I want to set the expiration date for the ingredients in my storage so that I can remember when they will expire. 

18\) As a registered user, I want to receive notifications 1 day before my ingredients expire so that I have time to cook them before the expiration date. 

19\) As a registered user, I want to set the quantity for the ingredient in my storage so that I can know the quantities of each ingredient in the storage.

20\) As a registered user, I want to create a shopping list, so that I can keep track of what I want to buy.

21\) As a registered user, I want to delete a shopping list, so that I can keep track of what I want to buy.

22\) As a registered user, I want to read my shopping lists, so that I know what to buy.

\# CONTAINERS:

\#\# CONTAINER\_NAME: AuthenticationManagement

\#\#\# DESCRIPTION:   
It creates, provides and validates the JWT tokens for user’s authentication

\#\#\# USER STORIES:  
2\) As a registered user, I want to log in with email and password so that logging in my account. 

\#\#\# PORTS:   
3000:3000

\#\#\# PERSISTENCE EVALUATION  
The Authentication container does not require data persistence to manage token creation and validation.

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The Authentication container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: AuthenticationManagement  
\- TYPE: backend  
\- DESCRIPTION: Manages the creation and verification of tokens.  
\- PORTS: 3000  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- a security directory for managing the request filters and all the security stuffs  
   \- a service directory for defining the util functions for the controller

\- ENDPOINTS:

| HTTP METHOD | URL             | Description                                                            | User Stories |  
| \----------- | \--------------- | \---------------------------------------------------------------------- | \------------ |  
| POST        | /auth/token     | Creates a token for authentication using the provided username.       | 2        |  
| GET         | /auth/validate  | Validates the provided token and returns the associated username.     | 2        |

\#\# CONTAINER\_NAME: UserProfileManagement

\#\#\# DESCRIPTION:   
The UserProfileManagement container handles user-related operations, including registration, login, profile management, and favorite recipes. It allows users to view and delete their profile data, as well as manage their favorite recipes and preferences. 

\#\#\# USER STORIES:  
1\) As a not registered user, I want to subscribe with email and password so that being a registered user.    
2\) As a registered user, I want to log in with email and password so that logging in my account.    
3\) As a registered user, I want to access my profile so that I can visualize my personal data.    
4\) As a registered user, I want to delete my account so that being no more a registered user.    
5\) As a registered user, I want to modify my email address so that I can update it.    
6\) As a registered user, I want to modify my password so that I can update it.    
7\) As a registered user, I want to modify my gender so that I can update it.    
11\) As a registered user, I want to save recipes so that I can access them easily in the future.    
13\) As a registered user, I want to delete a saved recipe so that I can remove it if I don't like it. 

\#\#\# PORTS:   
3001:3000

\#\#\# PERSISTENCE EVALUATION  
The UserProfileManagement container requires persistent storage to manage user-related data, including user profiles, notifications, and favorite recipes. It needs to store essential user-specific information such as usernames, email addresses, genders, and hashed passwords to ensure secure authentication and account management. Additionally, the system must persist details about saved recipes, associating them with individual users, as well as notification data, including content and its relationship with specific user profiles. 

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The UserProfileManagement container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: UserProfileManagement  
\- TYPE: backend  
\- DESCRIPTION: handles user operations like registration, login, profile management, and managing favorite recipes.  
\- PORTS: 3001  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- postgresql: Provides the PostgreSQL JDBC driver, enabling Java applications to interact with a PostgreSQL database for data storage and retrieval.  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- spring-boot-starter-amqp: Starter dependency for working with AMQP (Advanced Message Queuing Protocol) in Spring Boot, typically using RabbitMQ as the message broker. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a model directory for defining the entities represented in the db  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- repositories to interact with the database and make queries.  
    \- a service directory for defining the util functions for the controller  
    \- an utility directory for managing the JWT context  
    \- a security directory for managing the request filters and all the security stuffs  
    \- a RabbitMQ directory for for the queue configurations  
  

\- ENDPOINTS:

| HTTP METHOD | URL                                     | Description                                                          | User Stories |  
| \----------- | \--------------------------------------- | \-------------------------------------------------------------------- | \------------ |  
| POST        | /profiles/create                       | Creates a new user profile.                                          | 1            |  
| POST        | /profiles/login                        | Handles user login and returns appropriate response.                 | 2       |  
| GET         | /profiles/profile                      | Retrieves the profile data of the logged-in user.                    | 3            |  
| DELETE      | /profiles/profile/{username}           | Deletes the profile of the specified user.                           | 4       |  
| PUT         | /profiles/profile/{username}           | Updates the profile data of the specified user.                      | 5, 6, 7      |  
| GET         | /profiles/profile/{username}/favorites | Retrieves the favorite recipes of the logged-in user.                | 11           |  
| POST        | /profiles/profile/{username}/favorites/{recipeId} | Adds a recipe to the user's favorites.                               | 11           |  
| DELETE      | /profiles/profile/{username}/favorites/{recipeId} | Deletes a recipe from the user's favorites.                          | 13           |

\- DB STRUCTURE:

\*\*\_Favourites\_\*\* : | \*\*\_id\_\*\* | favourite\_id | user\_id |

\*\*\_Notifications\_\*\* : | \*\*\_notificationId\_\*\* | content | userProfile |

\*\*\_UserProfiles\_\*\* : | \*\*\_username\_\*\* | email | gender | hashPassword |

\*\*\_UserprofilesNotifications\_\*\* : | \*\*\_notificationID\_\*\* | \*\*\_UserProfilesUsername\_\*\*| 

\#\#\#\# MICROSERVICE: postgresql-userProfile\_db  
\- TYPE: database  
\- DESCRIPTION: stores the user’s personal data and their current notifications  
\- PORTS: 5432

\#\#\#\# MICROSERVICE: rabbitmq-notifications  
\- TYPE: queue  
\- DESCRIPTION: Contains the new notifications triggered for each user  
\- PORTS: 5672

\#\# CONTAINER\_NAME: NotificationManagement

\#\#\# DESCRIPTION: 

The NotificationManagement container is responsible for managing user notifications. It allows the creation of notifications for users, providing timely alerts such as reminders about ingredient expiration. This container ensures that users stay informed and can act on important updates related to their stored ingredients. 

\#\#\# USER STORIES:

18\) As a registered user, I want to receive notifications 1 day before my ingredients expire so that I have time to cook them before the expiration date.  

\#\#\# PORTS:   
3003:3000

\#\#\# PERSISTENCE EVALUATION  
The NotificationManagement container requires persistent storage to manage and store notifications sent to users. It needs to maintain essential data such as the unique notification ID, the content of the notification, the associated user profile, and the timestamp of when the notification was created. 

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The NotificationManagement container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE:  NotificationManagement  
\- TYPE: backend  
\- DESCRIPTION: manages user notifications, enabling timely alerts like ingredient expiration reminders to keep users informed.  
\- PORTS: 3003  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- postgresql: Provides the PostgreSQL JDBC driver, enabling Java applications to interact with a PostgreSQL database for data storage and retrieval.  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- spring-boot-starter-amqp: Starter dependency for working with AMQP (Advanced Message Queuing Protocol) in Spring Boot, typically using RabbitMQ as the message broker. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a model directory for defining the entities represented in the db  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- repositories to interact with the database and make queries.  
    \- a service directory for defining the util functions for the controller  
    \- an utility directory for managing the JWT context  
    \- a security directory for managing the request filters and all the security stuffs  
    \- a RabbitMQ directory for for the queue configurations

\- ENDPOINTS:

| HTTP METHOD | URL                  | Description                                          | User Stories |  
| \----------- | \-------------------- | \---------------------------------------------------- | \------------ |  
| POST        | /notifications/create | Creates a new notification for the user.            | 18           |

\- DB STRUCTURE:

\*\*\_Notifications\_\*\* : | \*\*\_Id\_\*\* | content | userProfile | timestamp |

\#\#\#\# MICROSERVICE: postgresql-notification\_db  
\- TYPE: database  
\- DESCRIPTION: stores the user’s notifications  
\- PORTS: 5432

\#\#\#\# MICROSERVICE: rabbitmq-notifications  
\- TYPE: queue  
\- DESCRIPTION: Contains the new notifications triggered for each user  
\- PORTS: 5672

\#\# CONTAINER\_NAME: RecipesAndIngredientManagement

\#\#\# DESCRIPTION: 

The RecipesAndIngredientManagement container is responsible for managing recipes and ingredients. It allows users to search for recipes by name or specific ingredients, as well as retrieve detailed information about individual ingredients. This container enables efficient management and retrieval of recipe and ingredient data, providing users with ideas for meals and allowing them to plan their cooking based on available ingredients. 

\#\#\# USER STORIES:

10\) As a registered user, I want to search for recipes so that I can find ideas for meals.   
12\) As a registered user, I want to add the ingredients to my shopping list so that I can keep track of what I need to buy.   
14\) As a registered user, I want to search recipes containing a specific ingredient so that I can find something I can cook with the ingredients I have in storage.  

\#\#\# PORTS:   
3004:3000

\#\#\# PERSISTENCE EVALUATION

The RecipesAndIngredientManagement container requires persistent storage to manage recipes, ingredients, and their associations. It needs to store detailed information about ingredients, such as their unique ingredient ID and name. Additionally, it must persist recipe data, including the recipe ID, name, nutritional information (carbohydrates, fats, proteins), and preparation steps. To establish the relationship between recipes and their ingredients, the system also maintains a join table linking recipe IDs to their associated ingredient IDs. 

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The RecipesAndIngredientManagement container is connected to Spoonacular API that is external services for accessing recipe, ingredient, and nutritional data.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: RecipesAndIngredientManagement  
\- TYPE: backend  
\- DESCRIPTION: Manages recipes and ingredients, allowing users to search recipes, retrieve ingredient details, and plan meals efficiently.  
\- PORTS: 3004  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- postgresql: Provides the PostgreSQL JDBC driver, enabling Java applications to interact with a PostgreSQL database for data storage and retrieval.  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a model directory for defining the entities represented in the db  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- repositories to interact with the database and make queries.  
    \- a service directory for defining the util functions for the controller  
    \- an utility directory for managing the JWT context  
    \- a security directory for managing the request filters and all the security stuffs

\- ENDPOINTS:

| HTTP METHOD | URL                                 | Description                                                     | User Stories |  
| \----------- | \----------------------------------- | \--------------------------------------------------------------- | \------------ |  
| GET         | /recipes-ingredients/ingredients/search-by-name | Searches for ingredients by their name.                         | 12           |  
| GET         | /recipes-ingredients/ingredients/search-by-id/{id} | Retrieves information about a specific ingredient by its ID.    | 12           |  
| GET         | /recipes-ingredients/recipes/search-by-name | Searches for recipes by their name.                             | 10         |  
| GET         | /recipes-ingredients/recipes/search-by-ingredient | Searches for recipes by their ingredients.                             | 14          |  
                  

\- DB STRUCTURE:   
\*\*\_Ingredients\_\*\* : | \*\*\_ingredient\_id\_\*\* | recipeName |  

\*\*\_Recipes\_\*\* : | \*\*\_recipe\_id\_\*\* | recipeName | carbohydrates | fats | proteins | steps |  

\*\*\_recipe\_ingredient\_\*\* : | \*\*\_recipe\_id\_\*\* | \*\*\_ingredient\_id\_\*\* |  

\#\#\#\# MICROSERVICE: postgresql-recipesAndIngredient\_db  
\- TYPE: database  
\- DESCRIPTION: Stores all the ingredients and recipes retrieved from the spoonacular api, when searched by an user.  
\- PORTS: 5432

\#\# CONTAINER\_NAME: ShoppinListManagement

\#\#\# DESCRIPTION: 

The ShoppingListManagement container is responsible for managing user shopping lists. It provides functionalities for users to create, retrieve, and delete shopping lists, as well as add or remove ingredients from them. This container ensures that users can efficiently organize and manage their shopping needs, making it easier to keep track of what they want to buy.

\#\#\# USER STORIES:

12\) As a registered user, I want to add the ingredients to my shopping list so that I can keep track of what I need to buy.   
16\) As a registered user, I want to delete an ingredient from my shopping list so that I can remove it if I already have it.   
20\) As a registered user, I want to create a shopping list, so that I can keep track of what I want to buy.   
21\) As a registered user, I want to delete a shopping list, so that I can keep track of what I want to buy.   
22\) As a registered user, I want to read my shopping lists, so that I know what to buy.  

\#\#\# PORTS:   
3002:3000

\#\#\# PERSISTENCE EVALUATION

The ShoppingListManagement container requires persistent storage to manage user shopping lists and their associated ingredients. It needs to store details such as the username and shopping list name to uniquely identify each shopping list. Additionally, the system must persist data about the ingredients associated with each shopping list, including the ingredient key, username, and shopping list name. 

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The ShoppingListManagement container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: ShoppinListManagement  
\- TYPE: backend  
\- DESCRIPTION:  Manages user shopping lists, enabling users to create, retrieve, delete lists, and add or remove ingredients efficiently.  
\- PORTS: 3002  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- postgresql: Provides the PostgreSQL JDBC driver, enabling Java applications to interact with a PostgreSQL database for data storage and retrieval.  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a model directory for defining the entities represented in the db  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- repositories to interact with the database and make queries.  
    \- a service directory for defining the util functions for the controller  
    \- an utility directory for managing the JWT context  
    \- a security directory for managing the request filters and all the security stuffs

\- ENDPOINTS:

| HTTP METHOD | URL                                    | Description                                                        | User Stories |  
| \----------- | \-------------------------------------- | \------------------------------------------------------------------ | \------------ |  
| GET         | /shopping-lists                       | Retrieves all shopping lists for the authenticated user.           | 22          |shoppingList\_db  
| GET         | /shopping-lists/{name}                | Retrieves a specific shopping list by name for the authenticated user. | 22          |  
| POST        | /shopping-lists                       | Creates a new shopping list for the authenticated user.            | 20          |  
| DELETE      | /shopping-lists/{name}                | Deletes a specific shopping list by name for the authenticated user. | 21          |  
| POST        | /shopping-lists/add-ingredient        | Adds an ingredient to the shopping list.                           | 12        |  
| DELETE       | /shopping-lists/delete-ingredient        | Delete an ingredient from the shopping list.                           | 16       |

\- DB STRUCTURE: 

\*\*\_ShoppingList\_Ingredients\_\*\* : | ingredients | \*\*\_ingredients\_key\_\*\* | \*\*\_shopping\_list\_username\_\*\* | \*\*\_shopping\_list\_shopping\_list\_name\_\*\* |

\*\*\_ShoppingList\_\*\* : | \*\*\_username\_\*\* | \*\*\_shopping\_list\_name\_\*\* |  

\#\#\#\# MICROSERVICE: postgresql-shoppingList\_db  
\- TYPE: database  
\- DESCRIPTION: Stores all the shopping lists, many for each user, each one containing some saved ingredients   
\- PORTS: 5432

\#\# CONTAINER\_NAME: StorageManagement

\#\#\# DESCRIPTION: 

The StorageManagement container is responsible for managing the storage of ingredients for users. It provides functionalities to add, retrieve, update, and delete ingredients in the user's storage. Users can set expiration dates, track ingredient quantities, and move ingredients from their shopping lists to their storage. This container ensures efficient inventory management for users, helping them keep track of their available ingredients.

\#\#\# USER STORIES:

8\) As a registered user, I want to add my ingredients to the storage so that I can keep track of the ingredients I have at home.   
9\) As a registered user, I want to delete an ingredient from my storage so that I can delete an ingredient I used for a recipe.   
15\) As a registered user, I want to move the ingredients from my shopping list to my ingredients storage so that I can keep track of what I bought.   
17\) As a registered user, I want to set the expiration date for the ingredients in my storage so that I can remember when they will expire.   
19\) As a registered user, I want to set the quantity for the ingredient in my storage so that I can know the quantities of each ingredient in the storage.  

\#\#\# PORTS:   
3005:3000

\#\#\# PERSISTENCE EVALUATION

The StorageManagement container requires persistent storage to manage the ingredients stored by users. It needs to store data such as the ingredient ID, username, quantity, and expiration date of each ingredient. This ensures that users can keep track of the ingredients they have at home, monitor their quantities, and be aware of when ingredients are nearing expiration. 

\#\#\# EXTERNAL SERVICES CONNECTIONS  
The StorageManagement container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: StorageManagement  
\- TYPE: backend  
\- DESCRIPTION: Manages ingredient storage, allowing users to add, retrieve, update, delete ingredients, set expiration dates, and track quantities.  
\- PORTS: 3005  
\- TECHNOLOGICAL SPECIFICATION:  
The microservice is developed in Java 21 and uses the Java Spring Boot framework version 3.4.1.  
Spring Boot:  
Several Spring Boot starter dependencies are included:  
\- Tomcat: The microservice uses TomcatWebServer as a web server to serve the Spring Boot application in a production environment.  
   
\- JWT (Jsonwebtoken): The microservice handles JSON Web Tokens (JWT), commonly used for secure token-based authentication.  
   
\- spring-boot-starter-data-jpa: The service interacts with a relational database using JPA (Java Persistence API).  
   
\- postgresql: Provides the PostgreSQL JDBC driver, enabling Java applications to interact with a PostgreSQL database for data storage and retrieval.  
   
\- lombok: A Java library that reduces boilerplate code by generating commonly used methods like getters, setters, toString, equals, and hashCode at compile time through annotations.  
   
\- spring-boot-starter-test: This is included for unit and integration testing purposes.  
   
\- spring-boot-starter-web: This is used for building web applications, including RESTful APIs.  
   
\- spring-boot-starter-security: Provides basic security features for Spring Boot applications, including authentication, authorization, and protection against common vulnerabilities (e.g., CSRF).  
   
\- spring-security-test: A test dependency for Spring Security, offering utilities to test security configurations and integration scenarios in Spring Boot applications.  
   
\- jakarta.validation-api: Defines the standard API for Java Bean Validation, used to validate object properties using annotations. 

\- Maven: The build process is managed by Apache Maven, with plugins such as spring-boot-maven-plugin for packaging the application and maven-compiler-plugin for compiling the code with Java 21\.

\- SERVICE ARCHITECTURE:   
The service is realized with:  
    \- a controller to manage routes, request parameters and responses. It handles the business logic of the microservice.  
    \- a model directory for defining the entities represented in the db  
    \- a dto directory with all the classes related to requests bodies and responses.  
    \- repositories to interact with the database and make queries.  
    \- a service directory for defining the util functions for the controller  
    \- an utility directory for managing the JWT context  
    \- a security directory for managing the request filters and all the security stuffs

\- ENDPOINTS:

| HTTP METHOD | URL                                    | Description                                                         | User Stories |  
| \----------- | \-------------------------------------- | \------------------------------------------------------------------- | \------------ |  
| GET         | /api/storage               | Retrieves the storage list of the specified user.                   | 8            |  
| POST        | /api/storage/add-ingredient           | Adds an ingredient to the user's storage with quantity and expiration date. | 8, 17, 19    |  
| DELETE       | /api/storage/delete-ingredient           | Delete an ingredient from the user's storage with quantity and expiration date. | 9     |  
| POST      | /api/storage/move-ingredients           | Move ingredients from the user's shopping list to the storage. | 15     |

\- DB STRUCTURE: 

\*\*\_Storage\_List\_\*\* : | expiry\_date | quantity | \*\*\_ingredient\_id\_\*\* | \*\*\_username\_\*\* |

\#\#\#\# MICROSERVICE: postgresql-ingredientsStorage\_db  
\- TYPE: database  
\- DESCRIPTION: Stores all the user’s storage, one for each user, each one containing some saved ingredients and their respective quantity and expiration date  
\- PORTS: 5432

\#\# CONTAINER\_NAME: myApp-FE

\#\#\# USER STORIES:

1\) As a not registered user, I want to subscribe with email and password so that being a registered user. 

2\) As a registered user, I want to log in with email and password so that logging in my account. 

3\) As a registered user, I want to access my profile so that I can visualize my personal data.  
   
4\) As a registered user, I want to delete my account so that being no more a registered user. 

5\) As a registered user, I want to modify my email address so that I can update it. 

6\) As a registered user, I want to modify my password so that I can update it. 

7\) As a registered user, I want to modify my gender so that I can update it. 

8\) As a registered user, I want to add my ingredients to the storage so that I can keep track of the ingredients I have at home. 

9\) As a registered user, I want to delete an ingredient from my storage so that I can delete an ingredient I used for a recipe. 

10\) As a registered user, I want to search for recipes so that I can find ideas for meals.   
11\) As a registered user, I want to save recipes so that I can access them easily in the future. 

12\) As a registered user, I want to add the ingredients to my shopping list so that I can keep track of what I need to buy. 

13\) As a registered user, I want to delete a saved recipe so that I can remove it if I don't like it. 

14\) As a registered user, I want to search recipes containing a specific ingredient so that I can find something I can cook with the ingredients I have in storage. 

15\) As a registered user, I want to move the ingredients from my shopping list to my ingredients storage so that I can keep track of what I bought. 

16\) As a registered user, I want to delete an ingredient from my shopping list so that I can remove it if I already have it. 

17\) As a registered user, I want to set the expiration date for the ingredients in my storage so that I can remember when they will expire. 

18\) As a registered user, I want to receive notifications 1 day before my ingredients expire so that I have time to cook them before the expiration date. 

19\) As a registered user, I want to set the quantity for the ingredient in my storage so that I can know the quantities of each ingredient in the storage.

20\) As a registered user, I want to create a shopping list, so that I can keep track of what I want to buy.

21\) As a registered user, I want to delete a shopping list, so that I can keep track of what I want to buy.

22\) As a registered user, I want to read my shopping lists, so that I know what to buy.

\#\#\# PORTS:   
3006:3006

\#\#\# DESCRIPTION:  
Container which exposes html/typescript dynamic pages which displays all the data retrieved from each microservice.

\#\#\# PERSISTANCE EVALUATION  
The Client-FE container does not include a database.

\#\#\# EXTERNAL SERVICES SERVICES CONNECTIONS  
The myApp-FE container does not connect to external services.

\#\#\# MICROSERVICES:

\#\#\#\# MICROSERVICE: myApp-FE  
\- TYPE: frontend  
\- DESCRIPTION: This microservice serves the main user interface for the Customer.  
\- PORTS: 3006  
\- PAGES:

| Name                  | Description                                              | Related Microservice      | User Stories |  
| \--------------------- | \-------------------------------------------------------- | \------------------------- | \------------ |  
| HomePage.tsx              | Displays the homepage.                                   | Frontend                  | N/A          |  
| SearchRecipeResults.tsx   | Displays search results for recipes.                     | recipesingredients-management         | 10, 14      |  
| RecipeInfoPage.tsx        | Displays detailed information for a specific recipe.     | recipesingredients-management         | 11, 12       |  
| ShoppingListPage.tsx      | Displays the shopping list page.                         | shoppinglist-management  | 20, 21, 22          |  
| ShoppingListDetail.tsx    | Displays details for a specific shopping list.           | shoppinglist-management  | 12, 15, 16           |  
| UserProfile.tsx       | Displays the user profile's data with notifications.            | userprofile-management notification-management | 3, 4, 5, 6, 7, 13       |  
| SignUp.tsx                | Displays the signup page.                                | User Profile Management authentication-management  | 1             |  
| Login.tsx                 | Displays the login page.                                 | User Profile Management authentication-management  | 2            |  
| Storage.tsx                 | Displays the storage page.                                 | storage-management   | 8, 9, 17, 18, 19            |  
| Page not found (404)  | Displays a 404 error page if the route is not found.     | Frontend                  | N/A          |

