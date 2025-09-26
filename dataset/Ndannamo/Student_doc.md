# SYSTEM DESCRIPTION:

The goal of this project is to design and develop a distributed software system that assists individuals in organizing trips. Our solution aims to streamline the process of planning, coordinating, and managing trips, whether they are for leisure or business purposes, by offering a comprehensive suite of tools in a single platform.

Unlike traditional trip planning apps, this system integrates collaborative features like group chat and polls with financial management tools, offering a one-stop solution for trip organization. Its distributed nature ensures reliability and efficiency, catering to both small groups and large-scale travel needs.


# USER STORIES:

1) As a future user, I want to register via email and password, to begin using the application.
2) As a user, I want to login, to access the application's features.
3) As a user, I want to delete my account.
4) As a user, I want to access my profile, to see my information.
5) As a user, I want to modify my username.
6) As a user, I want to modify my password.
7) As a user, I want to see all my trips.
8) As a user, I want to search my trips by title or destination.
9) As a user, I want to see my pending invitations to some trips.
10) As a user, I want to create a Trip, to start planning my trip.
11) As a trip creator, I want to delete a Trip.
12) As a trip creator, I want to invite other users to my trip, to share trip information with them.
13) As a user, I want to accept an invitation to a trip.
14) As a user, I want to refuse an invitation to a trip.
15) As a trip creator, I want to revoke an invitation that has been sent.
16) As a trip participant, I want to leave the trip.
17) As a trip creator, I want to remove a participant from my trip.
18) As a trip participant, I want to modify the trip's title.
19) As a trip participant, I want to modify the trip's dates.
20) As a trip participant, I want to modify the trip's destinations.
21) As a trip participant, I want to see the trip's schedule.
22) As a trip participant, I want to filter my schedule by a specific day.
23) As a trip participant, I want to see the weather prediction for every day of the trip, to better plan my activities.
24) As a trip participant, I want to add an activity to a trip's schedule.
25) As a trip participant, I want to delete an activity from a trip's schedule.
26) As a trip participant, I want to see the details of an activity from the schedule.
27) As a trip participant, I want to modify an activity's name, time, place, date, address and additional information.
28) As a trip participant, I want to add an attachment to an activity.
29) As a trip participant, I want to see a map with a marker on the activity's address.
30) As a trip participant, I want to see an activity's attachments.
31) As a trip participant, I want to be able to download the attachments of an activity.
32) As a trip participant, I want to add a travel to a trip's schedule.
33) As a trip participant, I want to delete a travel from a trip's schedule.
34) As a trip participant, I want to see the details of a travel from the schedule.
35) As a trip participant, I want to modify a travel's name, departure time, arrival time, departure place, arrival place, date, and additional information.
36) As a trip participant, I want to add an attachment to a travel.
37) As a trip participant, I want to see a map with a marker on the travel's departure address.
38) As a trip participant, I want to see a travel's attachments.
39) As a trip participant, I want to be able to download the attachments of a travel.
40) As a trip participant, I want to change the main location of a night.
41) As a trip participant, I want to create an accommodation spanning several nights, to save information about it.
42) As a trip participant, I want to delete an accommodation.
43) As a trip participant, I want to see the details of a night's accommodation.
44) As a trip participant, I want to modify an accommodation's name, check-in and check-out time, dates, contacts, address and additional information.
45) As a trip participant, I want to add an attachment to an accommodation.
46) As a trip participant, I want to see an accommodation's attachments.
47) As a trip participant, I want to be able to download the attachments of an accommodation.
48) As a trip participant, I want to create a new expense, to settle up at the end of the trip.
49) As a trip participant, I want to change the title of an expense.
50) As a trip participant, I want to change the mount of an expense.
51) As a trip participant, I want to change the split of an expense.
52) As a trip participant, I want to change the date of an expense.
53) As a trip participant, I want to delete an expense.
54) As a trip participant, I want to see how much I spent during the trip.
55) As a trip participant, I want to know who I have to pay back.
56) As a trip participant, I want to know who have to pay me back.
57) As a trip participant, I want to settle my debts.
58) As a trip participant, I want to remind other users to settle their debts with me.
59) As a trip participant, I want to send a message to the others participants in a group chat.
60) As a trip participant, I want to see the message sent in the group chat in real time.
61) As the user who sent a message, I want to delete that message.
62) As the user who sent a message, I wan to to modify that message.
63) As the user who sent a message, I want to see if other participants receive and/or read the message.
64) As a trip participant, I want to see the photos of a trip uploaded by me and the other participants.
65) As a trip participant, I want to upload a photo of a trip.
66) As a trip participant, I want to delete a photo of a trip.
67) As a user who's creating or updating a trip, I want to see be suggested names of cities.
68)	As a user , I want to check if a user is online, so that I know if they are available to chat in real time

| \#  | Title                              | User story                                                       |
| -- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3*  | Account deletion                          | As a user, I want to delete my account.                                                                                                                  |
| 28* | Adding an attachment to an activity       | As a trip participant, I want to add an attachment to an activity, to save tickets/reservations/etc                                                      |
| 30* | Seeing an activity's attachments          | As a trip participant, I want to see an activity's attachments, to check the tickets/reservations/etc                                                    |
| 31* | Downloading an activity's attachments     | As a trip participant, I want to be able to download the attachments of an activity                                                                      |
| 36* | Adding an attachment to a travel          | As a trip participant, I want to add an attachment to a travel, to save tickets/reservations/etc                                                         |
| 38* | Seeing a travel's attachments             | As a trip participant, I want to see a travel's attachments, to check the tickets/reservations/etc                                                       |
| 39* | Downloading a travel's attachments        | As a trip participant, I want to be able to download the attachments of a travel                                                                         |
| 43* | Seeing an accomodation's details          | As a trip participant, I want to see the details of a night's accomodation                                                                               |
| 45* | Adding an attachment to an accomodation   | As a trip participant, I want to add an attachment to an accomodation, to save tickets/reservations/etc                                                  |
| 61* | Delete message                            | As the user who sent a message, I want to delete that message                                                                                            |
| 62* | Modify message                            | As the user who sent a message, I wanto to modify that message                                                                                           |
| 63* | Check message                             | As the user who sent a message, I want to see if other participants receive and/or read the message                                                      |
\* Not implemented

# CONTAINERS:

## CONTAINER_NAME: authentication

### DESCRIPTION: 
This container runs the microservice of the authentication (registration and login) of users.

### USER STORIES:
1) As a future user, I want to register via email and password, to begin using the application.
2) As a user, I want to login, to access the application's features.

### PORTS: 
- 8081

### PERSISTENCE EVALUATION
To ensure the persistence of data, we used the Spring Data JPA interface, that allowed us to implement JPA-based (Java Persistence API) repositories.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:
- Registration and authentication

#### MICROSERVICE: Registration and authentication
- TYPE: backend
- DESCRIPTION: Allows a user to register and to login. This microservice is in charge of creating new users, and producing the JWT tokens that the users need to access the functionalities of the other microservices.
- PORTS: 8081
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Java using the SpringBoot framework. It connects to a PostgreSQL database hosted by the Postgres_main container, and exposes a REST interface on port 8081.
- SERVICE ARCHITECTURE:  
<img src="booklets/images/Ndannamo_Microservice_Authentication.png" alt="System architecture" width="80%"/>

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | POST | /api/auth/login | Logs the user in, returning a JWT token | 2 |
    | POST | /api/auth/register | Registers a user, returning a JWT token | 1 |


- DB STRUCTURE:

	**_users_** :	| **_id_** | email | nickname | password | role |




## CONTAINER_NAME: backend

### DESCRIPTION: 
This container runs the microservices related to the main functionalities of the application.

### USER STORIES:
4) As a user, I want to access my profile, to see my information.
5) As a user, I want to modify my username.
7) As a user, I want to see all my trips.
8) As a user, I want to search my trips by title or destination.
9) As a user, I want to see my pending invitations to some trips.
10) As a user, I want to create a Trip, to start planning my trip.
11) As a trip creator, I want to delete a Trip.
12) As a trip creator, I want to invite other users to my trip, to share trip information with them.
13) As a user, I want to accept an invitation to a trip.
14) As a user, I want to refuse an invitation to a trip.
15) As a trip creator, I want to revoke an invitation that has been sent.
16) As a trip participant, I want to leave the trip.
17) As a trip creator, I want to remove a participant from my trip.
18) As a trip participant, I want to modify the trip's title.
19) As a trip participant, I want to modify the trip's dates.
20) As a trip participant, I want to modify the trip's destinations.
21) As a trip participant, I want to see the trip's schedule.
22) As a trip participant, I want to filter my schedule by a specific day.
24) As a trip participant, I want to add an activity to a trip's schedule.
25) As a trip participant, I want to delete an activity from a trip's schedule.
26) As a trip participant, I want to see the details of an activity from the schedule.
32) As a trip participant, I want to add a travel to a trip's schedule.
33) As a trip participant, I want to delete a travel from a trip's schedule.
34) As a trip participant, I want to see the details of a travel from the schedule.
35) As a trip participant, I want to modify a travel's name, departure time, arrival time, departure place, arrival place, date, and additional information.
40) As a trip participant, I want to change the main location of a night.
41) As a trip participant, I want to create an accommodation spanning several nights, to save information about it.
43) As a trip participant, I want to see the details of a night's accommodation.
44) As a trip participant, I want to modify an accommodation's name, check-in and check-out time, dates, contacts, address and additional information.
48) As a trip participant, I want to create a new expense, to settle up at the end of the trip.
49) As a trip participant, I want to change the title of an expense.
50) As a trip participant, I want to change the mount of an expense.
51) As a trip participant, I want to change the split of an expense.
52) As a trip participant, I want to change the date of an expense.
53) As a trip participant, I want to delete an expense.
54) As a trip participant, I want to see how much I spent during the trip.
55) As a trip participant, I want to know who I have to pay back.
56) As a trip participant, I want to know who have to pay me back.
64) As a trip participant, I want to see the photos of a trip uploaded by me and the other participants.
65) As a trip participant, I want to upload a photo of a trip.
66) As a trip participant, I want to delete a photo of a trip.


### PORTS: 
- 8080

### PERSISTENCE EVALUATION
To ensure the persistence of data, we used the Spring Data JPA interface, that allowed us to implement JPA-based (Java Persistence API) repositories.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:  

#### MICROSERVICE: Profile managing
- TYPE: backend
- DESCRIPTION: Allows a user to see and modify their personal data, and to accept or refuse invitations sent by other users.
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Java using the SpringBoot framework. It connects to a PostgreSQL database hosted by the Postgres_main container, and exposes a REST interface on port 8080.
- SERVICE ARCHITECTURE: 
<img src="booklets/images/Ndannamo_Microservice_Profile_Managing.png" alt="System architecture" width="80%"/>

- ENDPOINTS:
		
	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | GET | /profile | Returns the personal data of the logged user | 4, 9 |
    | PUT | /profile/nickname | Changes the user's nickname | 5 |
    | PUT | /profile/password | Changes the user's password | 5 |
    | POST | /profile/invitations/{id} | Allows the user to accept or refuse an invitation to trip {id} |  13, 14 |


- DB STRUCTURE:

  - Main table:
 
    **_users_** :	| **_id_** | email | nickname | password | role |

  - Join table:

    **_trips\_invitations_** : | trip\_id | user\_id |


#### MICROSERVICE: Trips managing
- TYPE: backend
- DESCRIPTION: Allows to create and manage a trip: delete it, edit it, invite people to it, etc. It also allows to manage the schedule of a trip: create and manage events (activities or travels) and multi-nights accomodations.
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Java using the SpringBoot framework. It connects to a PostgreSQL database hosted by the Postgres_main container, and exposes a REST interface on port 8080.
- SERVICE ARCHITECTURE: 
<img src="booklets/images/Ndannamo_Microservice_Trip_Managing.png" alt="System architecture" width="100%"/>

- ENDPOINTS:
		
    | HTTP METHOD | URL | Description | User Stories |
    | ----------- | --- | ----------- | ------------ |
    | POST | /trips | Creates a new trip | 10 |
    | GET | /trips | Returns all trips of the logged user | 7, 8 |
    | GET | /trips/{id} | Returns trip {id} | 7, 8 |
    | DELETE | /trips/{id} | Deletes trip {id} | 11 |
    | POST | /trips/{id}/invite | Invites users to trip {id} | 12 |
    | DELETE | /trips/{id}/invite | Uninvites users to trip {id} | 15 |
    | DELETE | /trips/{id}/participants | Removes users from trip {id} | 17 |
    | GET | /trips/{id}/leave | Leaves trip {id} | 16 |
    | PUT | /trips/{id}/title | Changes title of trip {id} | 18 |
    | PUT | /trips/{id}/dates | Changes dates of trip {id} | 19 |
    | PUT | /trips/{id}/locations | Changes destinations of trip {id} | 20 |
    | GET | /trips/{id}/schedule | Returns the schedule of trip {id} | 21, 22, 26, 34, 43 |
    | POST | /trips/{id}/schedule/activity | Creates an activity for trip {id} | 24 |
    | DELETE | /trips/{id}/schedule/activity/{activity_id} | Deletes activity {activity_id} from trip {id} | 25 |
    | POST | /trips/{id}/schedule/travel | Creates a travel for trip {id} | 32 |
    | DELETE | /trips/{id}/schedule/travel/{travel_id} | Deletes travel {travel_id} from trip {id} | 33 |
    | POST | /trips/{id}/schedule/overnightstay | Creates an accomodation for trip {id} | 41 |
    | PUT | /trips/{id}/schedule/overnightstay | Edits an accomodation for trip {id} | 44 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/place | Edits the place of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/date | Edits the date of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/name | Edits the name of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/address | Edits the address of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/time | Edits the time of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/activity/{activity_id}/info | Edits the additional info of activity {activity_id} of trip {id} | 27 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/place | Edits the starting place of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/destination | Edits the destination of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/date | Edits the date of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/arrivaldate | Edits the arrival date of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/address | Edits the departure address of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/time | Edits the departure and arrival times of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/travel/{travel_id}/info | Edits the additional info of travel {travel_id} of trip {id} | 35 |
    | PUT | /trips/{id}/schedule/night/{night_id}/place | Edits the place of night {night_id} of trip {id} | 40 |
    | GET | /trips/{id}/photos | Returns a list of IDs of all the photos of trip {id} | 64 |
    | POST | /trips/{id}/photos | Uploads a photo to trip {id} | 65 |
    | GET | /trips/{id}/photos/{photo_id} | Returns the binary data of photo {photo_id} of trip {id} | 64 |
    | GET | /trips/{id}/photos/{photo_id}/info | Returns the info of photo {photo_id} of trip {id} | 64 |
    | DELETE | /trips/{id}/photos/{photo_id} | Deletes photo {photo_id} from trip {id} | 66 |
    | GET | /trips/{id}/expenses | Returns all expenses of trip {id} | 54, 55, 56 |
    | POST | /trips/{id}/expenses | Creates a new expense for trip {id} | 48 |
    | DELETE | /trips/{id}/expenses/{expense_id} | Deletes expense {expense_id} from trip {id} | 53 |
    | PUT | /trips/{id}/expenses/{expense_id} | Modifies expense {expense_id} of trip {id} | 49, 50, 51, 52 |


- DB STRUCTURE:

  - Main tables:

    **_trip_** : | **_id_** | creation_date | start_date | end_date | created_by | title | locations | invitations |

    **_activities_** : | **_id_** | trip_id | place | date | type | start_time | end_time | address | name | info |

    **_travels_** : | **_id_** | trip_id | place | date | type | departure_date | arrival_date | departure_time | arrival_time | address | destination | info |

    **_nights_** : | **_id_** | trip_id | place | date | type | overnight_stay_id | 

    **_overnight\_stay_** : | **_id_** | trip_id | start_date | end_date | start_check_in_time | end_check_in_time | start_check_out_time | end_check_out_time | name | address | contact |

    **_expenses_** : | **_id_** | trip_id | amount | date | paid_by | split_even | refund | paid_by_nickname | title | 

    **_image\_data_** : | **_id_** | trip_id | uploaded_by_id | upload_date | name | type | description | imagedata | 

  - Join tables:

    **_trips\_invitations_** : | trip\_id | user\_id |

    **_trips\_participation_** : | trip\_id | user\_id |

    **_amount\_per\_user_** : | expense_id | amount_per_user |






## CONTAINER_NAME: chat
This container provides a communication service via socket. It also manages the store of masseges sent for each trips.

### USER STORIES:
59) As a trip participant, I want to send a message to the others participants in a group chat.
60) As a trip participant, I want to see the message sent in the group chat in real time.
68)	As a user , I want to check if a user is online, so that I know if they are available to chat in real time

### PORTS:
- 8082

### PERSISTENCE EVALUATION
This service persists all chat messages exchanged between users during a trip. Messages are stored in a PostgreSQL database.

### EXTERNAL SERVICE CONNECTIONS
- The container communicates with the Authentication container through the /api/users/ endpoint to syncrhonize its users with those in the Authentication container
- The container communicates witj the Backedn container throush the /api/channels/ endpoint to ensure that each Trip corresponds to a messaging channel

### MICROSERVICES:
- Chat

#### MICROSERVICE: Chat
- TYPE: backend
- DESCRIPTION: Users can exchange messages in real-time within the trip channels they are enrolled in
- PORTS: 8082
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Java using the SpringBoot framework. The microservice implements real-time, bidirectional communication using WebSocket as the transport protocol, with STOMP (Simple Text Oriented Messaging Protocol) layered on top for message exchange and routing.
It connects to a PostgreSQL database hosted by chat-postegres container. Expose a REST interface on port 8082 to store and retrieve messages, and to create Channels
- SERVICE ARCHITECTURE:
  <img src="booklets/images/ChatMicroService.png" alt="System architecture" width="80%"/>
- ENDPOINTS (REST):
    | HTTP METHOD | URL | Description | User Stories |
    | ----------- | --- | ----------- | ------------ |
    | POST | /api/channels | Creates a new channel | 59 |
    | DELETE | /api/channels/{id} | Delete a channel | 59 |
    | POST | /api/channels/{id}/participants | Add a participant to channel {id} | 59
    | DELETE | /api/channels/{id}/participants | Remova a participant from channel {id} | 59
    | GET | /api/chat/{id} | Returns messages of channel {id} | 60 |
    | GET | /api/chat/{id}/presence | Returns online user of channel {id} | 68 |
    | POST | /api/users | Create an user | 59 |
- ENDPOINTS (WEBSOCKET):
	| HTTP METHOD |	URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
	| SEND | /chat/{tripId} | Receives messages from users in the specified trip channel | 60 |
	| SEND | /presence/heartbeat | Sends heartbeats to notify server of active users' presence | 68 |
	| SEND | /topic/messages/{tripId} | Sends messages to all users subscribed to the specified trip channel | 59 |
	| SEND | /topic/notice/{encodedEmail}/status | Sends status notifications about a user's online/offline status | 68 |

- DB STRUCTURE:

  - Main tables:

    **_channels_** : | **_id_** | tripId |
    
    **_users_** : | **_id_** | email |

    **_messages_** : | **_id_** | channelId | senderId | senderNickname | body | date |

## CONTAINER_NAME: cities

### DESCRIPTION: 
This container connects to the database run in the container Postgres_cities to offer information (country, coordinates, pictures) of different cities of the world.

### USER STORIES:
67

### PORTS: 
- 8083

### PERSISTENCE EVALUATION
To ensure the persistence of data, we used the Spring Data JPA interface, that allowed us to implement JPA-based (Java Persistence API) repositories.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:
- Cities information

#### MICROSERVICE: Cities information

- TYPE: backend
- DESCRIPTION: Allows to get different information about cities of the world.
- PORTS: 8083
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Java using the SpringBoot framework. It connects to a PostgreSQL database hosted by the Postgres_cities container, and exposes a REST interface on port 8083, only allowing the methods GET and OPTIONS. It doesn't require users to be logged in.
- SERVICE ARCHITECTURE: 
<img src="booklets/images/Ndannamo_Microservice_Cities_Information.png" alt="System architecture" width="80%"/>

- ENDPOINTS:
		
    | HTTP METHOD | URL | Description | User Stories |
    | ----------- | --- | ----------- | ------------ |
    | GET | /cities/{id} | Returns information about the city {id} | 67 |
    | GET | /cities/name/{start} | Returns a list of all the cities whose name starts with the string {start} | 67 |
    | GET | /cities/image?name={name}&country={country} | Returns the URL of an image of city {city} from country {country} | 67 |
    | GET | /cities/coordinates?name={name}&country={country} | Returns the coordinates of city {city} from country {country} | 67 |
  
  
- DB STRUCTURE:
**_cities_** : | **_id_** | name | country | iso | latitude | longitude | image |



## CONTAINER_NAME: frontend

### DESCRIPTION: 
This container contains the frontend of the application.

### USER STORIES:


### PORTS: 
- 3000

### PERSISTENCE EVALUATION
This container doesn't require persistent data.

### EXTERNAL SERVICES CONNECTIONS
- **LocationIQ**: to retrieve the coordinates of the address of an activity/travel/accomodation
- **OpenStreetMap**: to show a map of the address of an activity/travel/accomodation
- **MeteoMatics**: to show the weather forecast for every day of the trip

### MICROSERVICES:
- Frontend

#### MICROSERVICE: Frontend

- TYPE: frontend
- DESCRIPTION: Allows to get different information about cities of the world.
- PORTS: 3000
- TECHNOLOGICAL SPECIFICATION: Microservice realized in Javascript using the React framework. It connects to both external services and to the microservices offered by the other containers of the application. It provides the users with a web interface through with they can access the functionalities of the application.
- SERVICE ARCHITECTURE: 
<img src="booklets/images/Ndannamo_Microservice_Frontend.png" alt="System architecture" width="100%"/>

- PAGES: <put this bullet point only in the case of frontend and fill the following table>

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
	| Home | Landing page of the application | - | - |
	| Login | Login page | Registration and authentication | 2 |
	| Signup | Signup page | Registration and authentication | 1 |
	| Profile | Profile page | Profile managing | 4, 5, 9, 13, 14 |
	| Change Password | Page with a form to change your password | Profile managing | 6 |
	| Trips | Page with all your trips where it's possible to create a new trip | Trips managing, Cities information | 7, 8, 10, 67 |
	| Trip Summary | Page with the general details of a trip | Trips managing | 11, 12, 15-20 |
	| Trip Schedule | Page with the schedule and events of a trip | Trips managing | 21-30, 32-38, 40-47 |
	| Trip Expenses | Page with the expenses of a trip | Trips managing | 48-58 |
	| Trip Photos | Page with the photos of a trip | Trips managing | 64-66 |
	| Trip Chat | Page with the chat of a trip | Trips managing | 59, 60, 61 |



## CONTAINER_NAME: Postgres_main

### DESCRIPTION: 
Main database of the application.

### USER STORIES:
[Empty]

### PORTS: 
- 5432

### PERSISTENCE EVALUATION
We ensured the persistence of data by mounting a volume associated to this container.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: Main Database
- TYPE: database
- DESCRIPTION: Implements the main database of the application.
- PORTS: 5432
- TECHNOLOGICAL SPECIFICATION:
This microservice is implemented by running the official PostgreSQL Docker image.
- SERVICE ARCHITECTURE: 
<img src="booklets/images/Ndannamo_PostgresMain_Schema.png" alt="System architecture" width="80%"/>

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

  - Main tables:
 
    **_users_** :	| **_id_** | email | nickname | password | role |

    **_trip_** : | **_id_** | creation_date | start_date | end_date | created_by | title | locations | invitations |

    **_activities_** : | **_id_** | trip_id | place | date | type | start_time | end_time | address | name | info |

    **_travels_** : | **_id_** | trip_id | place | date | type | departure_date | arrival_date | departure_time | arrival_time | address | destination | info |

    **_nights_** : | **_id_** | trip_id | place | date | type | overnight_stay_id | 

    **_overnight\_stay_** : | **_id_** | trip_id | start_date | end_date | start_check_in_time | end_check_in_time | start_check_out_time | end_check_out_time | name | address | contact |

    **_expenses_** : | **_id_** | trip_id | amount | date | paid_by | split_even | refund | paid_by_nickname | title | 

    **_image\_data_** : | **_id_** | trip_id | uploaded_by_id | upload_date | name | type | description | imagedata | 

  - Join tables:

    **_trips\_invitations_** : | trip\_id | user\_id |

    **_trips\_participation_** : | trip\_id | user\_id |

    **_amount\_per\_user_** : | expense_id | amount_per_user |


## CONTAINER_NAME: Postgres_chat
Database to store messages

### USER STORIES:
59, 60, 68

### PORTS:
- 5433

### PERSISTENCE EVALUATION
We ensured the persistence of data by mounting a volume associated to this container.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:
#### MICROSERVICE: Chat Database
- TYPE: database
- DESCRIPTION: Implements a database to store and retrieve messages
- PORTS: 5433
- TECHNOLOGICAL SPECIFICATION:
This microservice is implemented by running the official PostgreSQL Docker image.
- DB STRUCTURE:

  - Main tables:

    **_channels_** : | **_id_** | tripId |
    
    **_users_** : | **_id_** | email |

    **_messages_** : | **_id_** | channelId | senderId | senderNickname | body | date |

## CONTAINER_NAME: Postgres_cities

### DESCRIPTION: 
Database containing information about different cities of the world.

### USER STORIES:
[Empty]

### PORTS: 
- 5434

### PERSISTENCE EVALUATION
We ensured the persistence of data by mounting a volume associated to this container.

### EXTERNAL SERVICES CONNECTIONS
This container doesn't connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: Cities Database
- TYPE: database
- DESCRIPTION: Implements a database with information about cities.
- PORTS: 5434
- TECHNOLOGICAL SPECIFICATION:
This microservice is implemented by running the official PostgreSQL Docker image.
- SERVICE ARCHITECTURE: 

- DB STRUCTURE: <put this bullet point only in the case a DB is used in the microservice and specify the structure of the tables and columns>

  **_cities_** : | **_id_** | name | country | iso | latitude | longitude | image |
