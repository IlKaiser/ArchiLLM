# SYSTEM DESCRIPTION:

Our distributed application concerns energy (electricity) management, both on the user’s side and on the energy grid level. 
The energy grid is the system that allows the distribution of electricity from the power stations to the final consumers. An important role in this process is done by the grid control center (we call it the central node). This structure manages the distribution of energy, in order to always ensure the stability and availability of energy. Each central node covers a certain area with the users residing in it. It is also linked to other adjacent central nodes, and (possibly) to a power station.
A crucial element in the energy grid system are the energy storages, since they allow storage of energy for later use; this improves the stability of the system. Usually they are batteries or some other similar method of storing energy. 

*Objectives*

optimize energy distribution: our application has to be able to manage correctly and efficiently the energy used and produced by each of its users, control the limits of consumption and send energy to the users.
enhance user control and awareness : our aim is to improve the user's ability to manage and effectively understand their energy usage. We want to implement features that allow users to actively monitor their energy consumption, providing detailed insights and controls. By enhancing user control and awareness, the goal is to enable individuals to make informed decisions about their energy usage, promoting efficiency and sustainability.
promote energy sharing and collaboration between users: one of the purposes of this application is to encourage the sharing of energy resources and to foster collaboration among users: this will be possible by creating a system where they can seamlessly buy and sell energy between themselves. In this way we are allowing users to efficiently meet their energy needs through mutual cooperation by shaping a more interconnected and sustainable energy ecosystem.
encourage sustainability: we want to educate and suggest sustainability and economical advice in order to encourage the transition to a greener economy, without wasting energy, so the application will have a personalized section concerning this topic.

*What our system should do*

Energy monitoring: Each user will have a detailed view on her/his own energy balance, regarding both consumption and production, they can access a dashboard containing statistics and charts showing energy consumption of the user from various sources (if more than one) through time. The user will receive notifications in case she/he is consuming above the limit, in fact each user will have a capacity limit that can be set or can have a default value. This is done to avoid wasting energy or overloading the network.
Energy bill: The user is able to choose the most preferred between different energy providers which serve his/her central node, by consulting and comparing them in a list. The application will send energy bills to the user according to their energy consumption and their provider fees. This is done only for the energy coming from the central node without considering exchanges with other users, which will be paid directly at the moment of transaction. 
Energy trading: The users will be able to easily trade energy between themselves (through the central node) or directly to the central node. The users can sell their produced energy to the central node whenever they want, if the central node capacity is not already full. They can buy extra-energy (other than the one they are already being provided with) directly from the central node without specifying the source seller. 
Energy storage and saving: In order to avoid any waste of energy, the user can monitor the amount of energy in her/his own deposit/storage if present. 
Energy management: Our application allows the central node (grid control center) to efficiently manage the distribution of energy among all users in the grid, in such a way that each user can satisfy her/his request.  The application will provide a dashboard with the current status of all the users that are served by the central node, and also the application will monitor and manage the central storage capacity which contains energy to be sold to users. Also the central node should monitor its storage capacity and energy production.
Sustainability: The user can choose whether to receive personalized advice for energy saving (and sustainability), this allows the user to reduce her/his spending and also to be environmentally friendly. In fact the user can choose what will be her/his sources of energy since they often are not specified in the contracts (renewable or traditional). 


# USER STORIES:

1) As a user, I want to register an account with my personal information, so that I can be a registered user.
2) As a central node manager, I want to register a new central node and link it to providers and users, so that I can ensure proper energy distribution.
3) As a user, I want to log in with username and password so that I can access all the website functionalities.
4) As a user, I want to have a home page, so that I can quickly access all the areas of the website.
5) As a user, I want to be able to access my personal information, so that I can change my password
6) As a user, I want to be able to register my devices, so that I can monitor their consumption.
7) As a user, I want to have a page where I can see all the notifications that are sent me so that I can be aware of the changes that are happening.
8) As a user, I want to monitor my energy consumption and production through a dashboard, so that I can track my energy usage and make informed decisions. 
9) As a user, I want to receive personalized energy-saving tips and sustainability recommendations, so that I can reduce my costs and environmental impact. 
10) As a central node manager, I want to monitor the real-time energy usage of all users in my grid, so that I can efficiently distribute energy and maintain grid stability.
11) As a renewable energy producer, I want to sell my surplus energy to the central node, so that I can earn revenue from my production.
12) As a user, I want to receive energy bills sent by the central node based on my provider’s rates and my consumption, so that I can track my expenses.
13) As a central node manager, I want to be able to see the energy storage levels within my grid, so that I can ensure energy availability during peak demand.
14) As a user I want to be able to access my energy storage in order to see my stored energy level.
15) As a user, I want to compare different energy providers within my central node, so that I can choose the most convenient and sustainable option.
16) As a user, I want to insert/update my current provider contract, so that I can adjust my account to fit my changing energy needs.
17) As a user, I want to access a history of my past energy bills, so that I can review my previous payments and budget accordingly.
18) As a user, I want to receive notification when a new bill is produced by the central node, so that I can know when to pay it.
19) As a user, I want to select my energy source (renewable or traditional) when signing up with a provider, so that I can align my consumption with my sustainability goals.
20) As a user, I want to buy additional energy from the central node when my energy needs exceed my provider’s supply, so that I can avoid power shortages.
21) As a user, I want to be able to pay through an integrated payment gateway (Stripe), so that I can manage transactions efficiently.
22) As a user, I want to insert and change my payment method, so that I can pay bills or energy.
23) As a user, I want to receive real-time transaction confirmations when buying or selling energy, so that I have a clear record of my energy trades.

# CONTAINERS:

## CONTAINER_NAME: user_service

### DESCRIPTION: 
This container handles users login/logout procedure as well as their registration to the platform. 

### USER STORIES:
1) As a user, I want to register an account with my personal information, so that I can be a registered user.
3) As a user, I want to log in with username and password so that I can access all the website functionalities.
4) As a user I want to have a home page, so that I can quickly access all the areas of the website.
5) As a user I want to be able to access my personal information, so that I can change my password.

### PORTS: 
4003:4003

### PERSISTENCE EVALUATION
The user_service requires persistent storage to manage user-related data across sessions and system restarts. It stores essential data such as personal information (name, surname, CF, email), login credentials (username, hashed password), and residency details (address, city, province, region, nation). This data is persisted in a PostgreSQL database and is used to authenticate users, retrieve and display their profile information, and associate them with specific properties like flats or villas. Storing this data ensures that users can securely log in, update their information, and maintain an accurate representation of their residential status within the system.

### EXTERNAL SERVICES CONNECTIONS
This container does not connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: user_service
- TYPE: frontend/backend

- DESCRIPTION: Handles frontend and backend operations regarding user's information.

- PORTS: 4003

- TECHNOLOGICAL SPECIFICATION:
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- a set of HTML pages representing the user interface for registration, login, profile, and property setup. These pages interact with the backend through form submissions and asynchronous JavaScript fetch calls.
	- JavaScript modules handling dynamic behaviors: form_validation.js manages client-side validation and form submission ajax.js populates form fields with address-related data; navigation.js manages route redirection and cookie parsing;profile.js and home.js provide logic for personalized content rendering.
	- a Node.js server (server.js) using Express to define all routes and API endpoints. It serves static files, handles session management, and communicates with a PostgreSQL database.
	- SQL queries embedded in the server code for all insertions, selections, and data validations, covering entities like Person, Property, Flat, Region, City, etc.
	- a PostgreSQL database accessed via the pg module, structured with normalized geographic and user-related tables.
	- authentication logic that uses sessions and bcrypt-hashed passwords, setting a logged cookie for identifying users across requests.
	- a profile page that retrieves and displays user and residence information, allowing for password change via a secure backend call.

- ENDPOINTS: 
		
    | HTTP METHOD | URL                   | Description                                       | User Stories |
    |-------------|-----------------------|---------------------------------------------------|--------------|
    | GET         | /                     | Home page (guest)                                 |      4       |
    | GET         | /login                | Login form page                                   |      3       |
    | GET         | /registration/user    | Registration form for user                        |      1       |
    | GET         | /registration/flat    | Registration form for flat residence              |      1       |
    | GET         | /registration/house   | Registration form for house residence             |      1       |
    | GET         | /home                 | Home page after login                             |      4       |
    | GET         | /profile              | User profile page                                 |      5       |
    | GET         | /home_reg             | Home redirection for invalid login                |      3       |
    | GET         | /logout               | Destroys session and logs out                     |      3       |
    | POST        | /login                | Login request processing and session creation     |      3       |
    | POST        | /change-password      | Changes the user password                         |      5       |
    | POST        | /insert_user          | Registers a new user                              |      1       |
    | POST        | /insert_house         | Saves house (villa) details for user              |      1       |
    | POST        | /insert_flat          | Saves flat details for user                       |      1       |

- PAGES: 

	|     Name     |         Description         | Related Microservice | User Stories |
	|--------------|-----------------------------|----------------------|--------------|
	| flat_reg     | flat registration page      | user_service         |  1	       |
	| login		   | login page					 | user_service         |  3	   	   |
	| home		   | home page					 | user_service			|  4		   |
	| home_catch   | home page redirection after | user_service			|  3		   |
					 attempted login, if that
					 user is missing
	| house_reg    | house registration page	 | user_service	   		|  1		   |
	| profile	   | profile page				 | user_service		    |  5		   |
	| user_reg	   | user registration page		 | user_service 		|  1		   |

- DB STRUCTURE: it is the same for each microservice, hence it is reported once only.

	**_nation_** :  | **_nation\_name_** |  

	**_region_** :  | **_id_** | **_reg\_name_** | **_nation\_name_** |  

	**_province_** :  | **_id_** | **_prov\_name_** | **_reg\_name_** |  

	**_city_** :  | **_id_** | **_city\_name_** | **_prov\_id_** |  

	**_person_** :  | **_id_** | **_p\_name_** | **_cf_** | **_surname_** | **_username_** | **_passcode_** | **_email_** | **_birthplace_** | **_birthprov_** | **_city\_id_** | **_birthdate_** | **_user\_role_** |  

	**_property_** :  | **_id_** | **_p\_address_** | **_city\_name_** | **_city\_id_** | **_inhabitant_** |  

	**_flat_** :  | **_id_** | **_prop\_id_** | **_floor_** | **_int\_number_** | **_inhabitant_** |  

	**_device_** :  | **_id_** | **_user\_id_** | **_property\_id_** | **_dev\_name_** | **_avg\_consuming_** |  

	**_consumption_** :  | **_id_** | **_device\_id_** | **_consumed_** | **_month\_date_** | **_exceeded_** |  

	**_has\_storage_** :  | **_id_** | **_property\_id_** | **_energy\_storage\_id_** |  

	**_energy\_storage_** :  | **_id_** | **_storage\_capacity_** | **_current\_energy_** | **_last\_recharge_** |  

	**_central\_node_** :  | **_id_** | **_energy\_storage\_id_** | **_province\_id_** | **_user\_admin_** |  

	**_has\_provider_** :  | **_id_** | **_central\_node\_id_** | **_provider\_id_** |  

	**_central\_node\_status_** :  | **_id_** | **_central\_node\_id_** | **_total\_energy\_distributed_** | **_total\_energy\_stored_** | **_status\_timestamp_** |  

	**_energy\_provider_** :  | **_id_** | **_ep\_name_** | **_energy\_type_** | **_cost_** |  

	**_bill_** :  | **_id_** | **_user\_id_** | **_trimester_** | **_amount_** | **_consumption_** | **_provider\_id_** | **_provider\_name_** | **_payed_** | **_deduction_** |  

	**_selected\_provider_** :  | **_id_** | **_user\_id_** | **_provider\_id_** | **_property\_id_** | **_consumption_** | **_ep\_description_** |  

	**_transaction\_pay_** :  | **_id_** | **_user\_id_** | **_other\_entity_** | **_central\_node\_id_** | **_transaction\_date_** | **_amount_** | **_price_** | **_transaction\_type_** | **_cardid_** | **_cardnumber_** |  

	**_user\_card\_info_** :  | **_id_** | **_user\_id_** | **_cardholderid_** |  

	**_cards_** :  | **_id_** | **_user\_id_** | **_cardholderid_** | **_cardid_** |  

	**_product_** :  | **_id_** | **_user\_id_** | **_central\_node\_id_** | **_to\_sale\_date_** | **_amount_** | **_price_** | **_energy\_type_** |  

	**_notifications_** :  | **_id_** | **_user\_id_** | **_notification\_text_** | **_notification\_timestamp_** |  

	**_energy\_usage_** :  | **_id_** | **_timestamp_** | **_energy\_value_** |  

	**_house_** :  | **_id_** | **_inhabitant_** | **_average\_production_** |  

	**_device\_flat_** :  | **_id\_flat_** | **_id\_device_** |  

	**_device\_house_** :  | **_id\_prop_** | **_id\_device_** |  

	**_flat\_provided_** :  | **_id_** | **_flat\_id_** | **_ep\_id_** |  

	**_house\_provided_** :  | **_id_** | **_house\_id_** | **_ep\_id_** |  


## CONTAINER_NAME: bills_provider_service

### DESCRIPTION: 
Handles bill generation, payment processing, and provider selection.

### USER STORIES:
12) As a user, I want to receive energy bills sent by the central node based on my provider’s rates and my consumption, so that I can track my expenses.
15) As a user, I want to compare different energy providers within my central node, so that I can choose the most convenient and sustainable option.
16) As a user, I want to insert/update my current provider contract, so that I can adjust my account to fit my changing energy needs.
17) As a user, I want to access a history of my past energy bills, so that I can review my previous payments and budget accordingly.
19) As a user, I want to select my energy source (renewable or traditional) when signing up with a provider, so that I can align my consumption with my sustainability goals.

### PORTS: 
4004:4004

### PERSISTENCE EVALUATION
The provider selection and billing service requires persistent storage to support user-specific energy service tracking. It stores details about each user’s selected energy provider, including energy type, cost, consumption plan, and custom description, in the Selected_provider table. All energy bills are persistently recorded with data like trimester, amount, consumption, provider ID and name, and whether the bill has been paid, stored in the Bill table. Additional relational data links users to their properties and central nodes. Notifications about consumption limits are stored and deduplicated to avoid spam. This persistence ensures that provider selections, billing records, and personalized consumption alerts are consistently available across sessions and navigations, enabling reliable comparison, payment, and tracking of energy use.

### EXTERNAL SERVICES CONNECTIONS
This container does not connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: bills_provider_service
- TYPE: backend

- DESCRIPTION: Handles frontend and backend operations for billing and provider management.

- PORTS: 4004

- TECHNOLOGICAL SPECIFICATION:
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- multiple HTML interfaces such as provider.html, search.html, insert_provider.html, bill.html, comparison.html, and my_provider.html, each representing a distinct function in the provider selection and billing workflow.
	- modular JavaScript scripts for page-specific logic:
		- search.js fetches and filters provider data;
		- insert_provider.js handles provider selection/change and form submission;
		- comparison.js displays side-by-side provider comparisons using localStorage;
		- bill.js retrieves, displays, filters, and redirects for payment of user bills;
		- provider.js and my_provider.js verify and render the user’s current provider;
	- a Node.js backend (server.js) built with Express, exposing endpoints for provider retrieval (/get-providers), bill management (/get-bills), contract registration (/select-provider), user and node information, and provider data.
	- persistent data fetched from a PostgreSQL database via pg, where key entities include Bill, Selected_provider, Energy_provider, Notifications, and user-linked tables like Property and Person.
	- integration with a session-based system and cookie parsing (through navigation.js and extractUserId()) to maintain user context across pages and services.
	- logic that conditionally renders interface elements and redirects users (e.g., showing “Insert your provider” if none is found), and supports navigation actions like to_bill() or to_my_provider() programmatically across all pages.

- ENDPOINTS: 

	| HTTP METHOD   | URL                   | Description                        | User Stories   |
	|---------------|-----------------------|------------------------------------|----------------|
	| GET           | /                     | Bill and provider homepage         |   15,16,17     |
	| GET           | /bill                 | Displays bill history page         |   12,17        |
	| GET           | /provider             | Displays provider page             |   16           |
	| GET           | /provider/insert      | Displays provider insertion page   |   16           |
	| GET           | /provider/my_provider | Displays current selected provider |   16           |
	| GET           | /provider/search      | Search available providers         |   15           |
	| GET           | /provider/comparison  | Compare providers                  |   15           |
	| POST          | /get-bills            | Fetch all bills for a user         |   12, 17       |
	| POST          | /get-providers        | Fetch all providers for node       |   16           |
	| POST          | /select-provider      | Insert or change user provider     |   19           |

- PAGES: 

	|     Name    	   |         Description         | Related Microservice   | User Stories |
	|------------------|-----------------------------|------------------------|--------------|
    | bill             | User's bill history view    | bills_provider_service | 12,17		 |
	| provider         | Provider info page          | bills_provider_service | 16 			 |
	| my_provider	   | Selected provider info		 | bills_provider_service | 16			 |
	| search		   | Filter providers			 | bills_provider_service | 15			 |
	| comparison       | Provider comparison page    | bills_provider_service | 15 			 |
	| insert_provider  | Provider selection page     | bills_provider_service | 16,19 		 |


## CONTAINER_NAME: energy_deposit

### DESCRIPTION: 
Allows users to have a view of the current stored energy.

### USER STORIES:
14) As a user I want to be able to access my energy storage in order to see my stored energy level.

### PORTS: 
4001:4001

### PERSISTENCE EVALUATION
The service displays a user's current energy storage status in real time, including capacity, usage, and last recharge.

### EXTERNAL SERVICES CONNECTIONS
This container does not connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: energy_deposit
- TYPE: backend/frontend

- DESCRIPTION: Frontend and backend logic to track and display energy deposits.

- PORTS: 4001

- TECHNOLOGICAL SPECIFICATION: 
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- a single-page HTML interface (deposit.html) that visually represents the user's energy storage using a vertical cylinder graphic and textual indicators for storage capacity, current level, remaining energy, and last recharge.
	- frontend JavaScript (deposit.js) that extracts the logged-in user’s ID from the logged cookie, fetches the latest storage data via /api/energy/:userId, updates the display in real time, and animates the cylinder fill level.
	- a backend server (server.js) built with Node.js and Express, which serves static content and exposes the /api/energy/:userId endpoint to query the energy storage details of the requesting user.
	- PostgreSQL integration using pg to query user-associated storage data by joining Person, Property, Has_Storage, and Energy_Storage tables.
	- cookie-based session logic to support user context, and client-side navigation tools (navigation.js) for routing to related services like profile, login, and notification pages.

- ENDPOINTS: 

	| HTTP METHOD | URL                  | Description               | User Stories |
	|-------------|----------------------|---------------------------|--------------|
	| GET         | /                    | Deposit home page         |    14        |
	| GET         | /api/energy/{userId} | Retrieve user energy data |    14	    |

- PAGES: 

	|     Name     |             Description             | Related Microservice | User Stories |
	|--------------|-------------------------------------|----------------------|--------------|
    | deposit      | Displays user's deposit status page | energy_deposit       | 14 		   |


## CONTAINER_NAME: monitoring_service

### DESCRIPTION: 
Monitors and displays user consumption/production and notification alerts.

### USER STORIES:
6) As a user, I want to be able to register my devices, so that I can monitor their consumption.
7) As a user, I want to have a page where I can see all the notifications that are sent me so that I can be aware of the changes that are happening.
8) As a user, I want to monitor my energy consumption and production through a dashboard, so that I can track my energy usage and make informed decisions. 
9) As a user, I want to receive personalized energy-saving tips and sustainability recommendations, so that I can reduce my costs and environmental impact. 
18) As a user, I want to receive notification when a new bill is produced by the central node, so that I can know when to pay it.

### PORTS: 
4005:4005

### PERSISTENCE EVALUATION
The monitoring service requires persistent storage to track user devices, energy usage, and notifications. It stores device data (name, consumption, linked property), aggregates monthly and per-device consumption for visualization, and records alerts like overconsumption relative to provider-set thresholds. These persisted records enable meaningful user feedback, personalized statistics, and the automated generation of actionable insights through visual and textual outputs.

### EXTERNAL SERVICES CONNECTIONS
This container does not connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: monitoring_service
- TYPE: backend/frontend

- DESCRIPTION: enables users to manage energy providers, compare offers, and pay bills, with persistent tracking of contracts and consumption.

- PORTS: 4005

- TECHNOLOGICAL SPECIFICATION:
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- three primary HTML interfaces: dashboard.html for data visualization and tips, my_devices.html for device management, and notification.html for user alerts.
	- modular JavaScript files:
		- dashboard.js handles energy consumption statistics, visualizations (doughnut/bar charts via Chart.js), and provider info
		- my_devices.js enables insertion and deletion of devices linked to a user's property
		- notification.js fetches and filters alerts (e.g., overconsumption)
		- navigation.js provides global route management and navbar updates
	- a Node.js backend (server.js) using Express, with endpoints to serve static HTML and retrieve data from PostgreSQL via pg.
	- database interaction covering Device, Consumption, Notifications, and Selected_Provider, with real-time aggregation of consumption per device and month.
	- a client-server contract for filtering notifications by date, dynamically updating dashboards with charts, and auto-generating device tables and alerts.
	- contextual rendering tied to the logged-in user via cookie parsing (logged=) to personalize views and data fetches.

- ENDPOINTS: 

	| HTTP METHOD   | URL                                  | Description                   | User Stories   |
	|---------------|--------------------------------------|-------------------------------|----------------|
	| GET           | /                                    | Dashboard homepage            |    8,9         |
	| GET           | /monitoring/notification             | Notification view             |    7,18        |
	| GET           | /monitoring/devices                  | User's device list            |    6           |
	| POST          | /charts                              | Energy chart data             |    8           |
	| POST          | /insert_device                       | Insert a new device           |    6           |
	| DELETE        | /delete_device                       | Delete device                 |    6           |
	| POST          | /get-notifications                   | Retrieve user notifications   |    7           |
	| POST          | /get-devices                         | Retrieve device list          |    6           |
	| GET           | /api/top_devices/:userId             | Top 3 consuming devices       |    8           |
	| GET           | /api/all_devices_consumption/:userId | Consumption per device        |    8           |
	| GET           | /api/monthly_consumption/:userId     | Monthly consumption per user  |    8           |

- PAGES: 

	|     Name     |         Description         | Related Microservice | User Stories |
	|--------------|-----------------------------|----------------------|--------------|
    | dashboard    | Energy usage dashboard      | monitoring_service 	| 8,9 		   |
	| my_devices   | Device list and management  | monitoring_service 	| 6 		   |
	| notification | User notifications page     | monitoring_service 	| 7,18		   |


## CONTAINER_NAME: trading_service

### DESCRIPTION: 
Handles energy buy/sell operations and card-based payments.

### USER STORIES:
11) As a renewable energy producer, I want to sell my surplus energy to the central node, so that I can earn revenue from my production.
20) As a user, I want to buy additional energy from the central node when my energy needs exceed my provider’s supply, so that I can avoid power shortages.
21) As a user, I want to be able to pay through an integrated payment gateway (Stripe), so that I can manage transactions efficiently.
22) As a user, I want to insert and change my payment method, so that I can pay bills or energy.
23) As a user, I want to receive real-time transaction confirmations when buying or selling energy, so that I have a clear record of my energy trades.

### PORTS: 
4002:4002

### PERSISTENCE EVALUATION
The trading/payment service requires persistent storage to handle user transactions, energy listings, and payment information. It stores product listings with details such as user ID, amount, price, energy type, and listing date. It also tracks transactions by recording the buyer, seller, card used, transaction type, amount, and final energy balances. In addition, it saves users’ preferred and secondary payment cards linked to Stripe customer IDs, enabling secure and consistent payment operations. This persistent data is crucial to ensure transaction integrity, manage available energy for sale, retrieve payment history, and support secure Stripe-based checkout flows.

### EXTERNAL SERVICES CONNECTIONS
This container connects to Stripe API in order to handle the credit card insertion-verification logic.

### MICROSERVICES:

#### MICROSERVICE: trading_service
- TYPE: frontend/backend

- DESCRIPTION: Provides UI and backend logic for trading and transaction flow.

- PORTS: 4002

- TECHNOLOGICAL SPECIFICATION: 
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- a collection of HTML interfaces for trading, buying, selling energy, managing cards, and processing payments. These include buy.html, sell.html, insert_pay.html, and others.
	- a frontend logic layer composed of modular JavaScript files such as buy.js, sell.js, pay.js, card.js, and movement.js, which handle tasks like listing available products, handling form submissions, managing Stripe integration, and displaying transaction history.
	- a Node.js backend (server.js) that exposes RESTful API endpoints for inserting and querying user transactions, products for sale, and saved cards. It integrates with the Stripe API for payment method creation, storage, and charging.
	- a PostgreSQL database that stores all persistent data including transactions, products for sale, preferred payment methods, Stripe customer IDs, and links between users and their energy storage.
	- an external Stripe service used to manage credit card data securely, including card creation, attachment, and payment intent confirmation.
	- a navigation utility (navigation.js) to handle redirections across service pages and update the navbar context based on user login status using a cookie system (logged=...).
	- a session-based system storing Stripe customer IDs in the backend, retrievable via GET /get-session to support smooth card-based transactions.

- ENDPOINTS: 

	| HTTP METHOD   | URL                      | Description                   | User Stories   |
	|---------------|--------------------------|-------------------------------|----------------|
	| GET           | /                        | Trading homepage              |   11,20,21,23  |
	| GET           | /trading/buy             | Buy energy page               |   20           |
	| GET           | /trading/pay             | Pay bill page                 |   21           |
	| GET           | /trading/sell            | Sell energy page              |   11           |
	| GET           | /payment_method          | Payment method page           |   21           |
	| GET           | /trading/movements       | Transaction history page      |   23           |
	| GET           | /trading/checkout        | Checkout page                 |   21           |
	| GET           | /trading/complete        | Payment complete confirmation |   21           |
	| GET           | /payment_method/add_card | Add new card                  |   22           |
	| POST          | /manage-info             | Create/get cardholderId       |   22           |
	| POST          | /add-card                | Add a payment method          |   22           |
	| POST          | /change-card             | Change preferred card         |   22           |
	| POST          | /get-cards               | Retrieve cards via Stripe     |   22           |
	| DELETE        | /delete-cards            | Remove a payment method       |   22           |
	| POST          | /process-payment         | Pay for a product or bill     |   21           |
	| POST          | /get-movements           | Get user’s transaction list   |   23           |
	| POST          | /insert-sale             | Insert product to sell        |   11           |
	| POST          | /get-sales               | Get sales for a node          |   11           |
	| POST          | /get-sales-user          | Get user’s product list       |   11           |
	| POST          | /get-node                | Get user's central node ID    |   11           |
	| DELETE        | /delete_sale             | Delete a sale                 |   11           |

- PAGES: 

	|    Name    |         Description          | Related Microservice | User Stories |
	|------------|------------------------------|----------------------|--------------|
    | buy        | Interface to purchase energy | trading_service 	   | 20 		  |
	| sell       | Interface to sell energy     | trading_service 	   | 11 		  |
	| insert_pay | Add payment method           | trading_service 	   | 22 		  |
	| movements  | View past transactions       | trading_service 	   | 23 		  |
	| add_card	 | Insert card details 			| trading_service	   | 22			  |
	| pay		 | Interface to pay				| trading_service	   | 21			  |
	| trading	 | Trading home page			| trading_service  	   | 11,20,21,23  |


## CONTAINER_NAME: central_node_service

### DESCRIPTION: 
Manages grid-level energy distribution, node registration, and admin functionality.

### USER STORIES:
2) As a central node manager, I want to register a new central node and link it to providers and users, so that I can ensure proper energy distribution.
10) As a central node manager, I want to monitor the real-time energy usage of all users in my grid, so that I can efficiently distribute energy and maintain grid stability.
13) As a central node manager, I want to be able to see the energy storage levels within my grid, so that I can ensure energy availability during peak demand.

### PORTS: 
4000:4000

### PERSISTENCE EVALUATION
The central node service requires persistent storage to manage energy infrastructure data and monitor user consumption. It stores the location, capacity, and current energy levels of each node, the associated energy providers, and real-time deposit information. User consumption data over time is collected and used to compute bills, which are stored alongside relevant provider and pricing details. Alerts for overuse or shortages are generated and saved to notify administrators. This persistent data ensures continuous monitoring of the energy grid, traceability of usage patterns, and automated billing and alerting for provincial users linked to a central node.

### EXTERNAL SERVICES CONNECTIONS
This container does not connect to any external service.

### MICROSERVICES:

#### MICROSERVICE: central_node_service
- TYPE: frontend/backend

- DESCRIPTION: Orchestrates central node configuration and operations for energy flow.

- PORTS: 4000

- TECHNOLOGICAL SPECIFICATION: 
The backend is developed in Node.js with Express module, while the frontend is composed of a set of HTML pages along with some JavaScript files that are used to implement dynamic functionalities.

- SERVICE ARCHITECTURE: 
The service is realized with:
	- a frontend composed of HTML pages such as central_node.html, central_node_registration.html, and select_node_provider.html, each representing a step in setting up and monitoring a central node.
	- client-side JavaScript files like central_node_page.js, deposit.js, central_node_registration.js, and central_node_provider_reg.js which handle energy chart rendering, storage level visualization, dynamic provider selection, and form submission.
	- a Node.js backend (server.js) using Express, which exposes API endpoints for inserting central nodes, assigning providers, retrieving province data, generating user bills based on consumption, and emitting real-time statistics through WebSocket.
	- a PostgreSQL database storing entities such as Central_Node, Energy_Storage, Energy_Provider, Has_Provider, and Consumption.
	- a WebSocket integration (socket.io) that continuously sends updated charts and alerts about energy distribution, storage, user consumption, and deposit levels to the dashboard in real time.
	- real-time and scheduled logic to calculate user consumption summaries, generate bills quarterly based on provider pricing, and insert alerts for overconsumption or low storage levels.
	- dynamic UI updates and data binding via Chart.js and DOM manipulation, keeping the dashboard interactive and up to date.

- ENDPOINTS: 

	| HTTP METHOD | URL                                 | Description                               | User Stories |
	|-------------|-------------------------------------|-------------------------------------------|--------------|
	| GET         | /                                   | Central node dashboard and generate bills |  2           |
	| GET         | /registration/node                  | Central node registration page            |  2           |
	| GET         | /registration/provider              | Provider assignment to node               |  2           |
	| POST        | /api/generate_bills/{centralNodeId} | Generate bills for users in node          |              |
	| POST        | /insert_node                        | Insert a central node and energy storage  |  2           |
	| POST        | /get-node                           | Get node ID for user                      |  2           |

- PAGES: 

	|            Name            |            Description           | Related Microservice | User Stories |
	|----------------------------|----------------------------------|----------------------|--------------|
    | central_node               | Admin dashboard                  | central_node_service | 10			  |
	| central_node_registration  | Page to register a central node  | central_node_service | 2  		  |
	| select_node_provider       | Link providers to central node   | central_node_service | 2			  |