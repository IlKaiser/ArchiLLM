# ChoronoPic Documentation

## 🧠 SYSTEM DESCRIPTION

ChronoPic is a photo management platform where users can upload images and automatically tag them based on age detection and optionally known persons. The system provides asynchronous processing using computer vision (face & age detection), and supports secure user authentication. Users can view, filter, and manage their personal image collections based on metadata and detection results.

---

## ✅ USER STORIES

| #   | Description                                                                                            |
| --- | ------------------------------------------------------------------------------------------------------ |
| 1   | As a User, I want to sign up so that I can access the application.                                     |
| 2   | As a User, I want to verify my account using an OTP so that I can activate my account securely.        |
| 3   | As a User, I want to log in to the platform so that I can use its features.                            |
| 4   | As a User, I want to remain logged in so I don’t need to re-enter credentials repeatedly.              |
| 5   | As a User, I want to reset my password so that I can recover access when I forget it.                  |
| 6   | As a User, I want to upload a photo with optional metadata so that it can be processed and stored.     |
| 7   | As a User, I want the system to run face detection automatically so the image can be cropped properly. |
| 8   | As a User, I want age detection to run in the background so I get a result without waiting.            |
| 9   | As a User, I want to retrieve the detected age for a specific photo.                                   |
| 10  | As a User, I want to retrieve detected ages for multiple photos to avoid many separate API calls.      |
| 11  | As a User, I want to delete one or more photos and their associated age records if desired.            |
| 12  | As a User, I want to view all my uploaded photos and tags by email.                                    |
| 13  | As a User, I want to retrieve photo content by ID so I can display it on the frontend.                 |
| 14  | As a User, I want to filter photos by email and tag to categorize and query them easily.               |

---

## 📦 CONTAINERS

---

### 🔐 CONTAINER: Authentication

- **Port:** 8082
- **Technology:** Java Spring Boot + JWT

#### 🧾 User Stories

1, 2, 3, 4, 5

#### 🧰 Description

Handles registration, OTP verification, login, password recovery, and token validation for all users.

#### 💾 Persistence Evaluation

- Store user account data (Story 1, 3, 5)
- Track OTPs and verification status (Story 2)
- Maintain refresh/session tokens (Story 4)

> Requires relational DB for persistence.

#### 🔌 External Services

- None

#### 🧩 Microservice: `auth-service`

- **Type:** backend
- **Ports:** 8082
- **Technology:** Java Spring Boot, JWT
- **Architecture:** Stateless REST API

#### 📡 Endpoints

| Method | URL                             | Description            | Stories |
| ------ | ------------------------------- | ---------------------- | ------- |
| POST   | `/api/accounts/signup`          | Register new user      | 1       |
| POST   | `/api/accounts/verify-otp`      | OTP verification       | 2       |
| POST   | `/api/accounts/login`           | Login with credentials | 3       |
| POST   | `/api/accounts/forgot-password` | Request password reset | 5       |
| POST   | `/api/accounts/reset-password`  | Set new password       | 5       |

---

### 🖼️ CONTAINER: Photo-Service

- **Port:** 8080
- **Technology:** Java Spring Boot + MongoDB

#### 🧾 User Stories

6, 11, 12, 13, 14

#### 🧰 Description

Manages photo uploads, retrieval, filtering, deletion, and metadata storage.

#### 💾 Persistence Evaluation

- Store uploaded photos (Story 6)
- Metadata: email, tag, timestamps (Stories 6, 12, 14)
- Retrieve/delete content (Stories 11, 13)

> Suitable DB: MongoDB or other NoSQL.

#### 🔌 External Services

- Calls Age Detection container

#### 🧩 Microservice: `photo-service`

- **Type:** backend
- **Ports:** 8080
- **Architecture:** RESTful service with DB

#### 📡 Endpoints

| Method | URL                      | Description                   | Stories |
| ------ | ------------------------ | ----------------------------- | ------- |
| POST   | `/api/photos/upload`     | Upload photo with metadata    | 6       |
| GET    | `/api/photos/mine`       | View all user’s photos        | 12      |
| GET    | `/api/photos/image/{id}` | Retrieve photo by ID (base64) | 13      |
| GET    | `/api/photos/filter`     | Filter by email and tag       | 14      |
| DELETE | `/api/photos/{id}`       | Delete single photo           | 11      |
| DELETE | `/api/photos/batch`      | Delete multiple photos        | 11      |

---

### 🧠 CONTAINER: Age-Detection-Service

- **Port:** 8081
- **Technology:** Java Spring Boot + OpenCV + Docker

#### 🧾 User Stories

7, 8, 9, 10, 11

#### 🧰 Description

Handles face detection and age estimation asynchronously.

#### 💾 Persistence Evaluation

- Store age for each photo (Stories 8–10)
- Store cropped face images (Story 7)
- Allow deletion of age data (Story 11)

#### 🔌 External Services

- Receives photo IDs from Photo-Service

#### 🧩 Microservice: `age-detection`

- **Type:** backend
- **Ports:** 8081
- **Architecture:** Event-driven REST API

#### 📡 Endpoints

| Method | URL                  | Description                  | Stories |
| ------ | -------------------- | ---------------------------- | ------- |
| POST   | `/api/face-detect`   | Crop face from image         | 7       |
| POST   | `/api/age/upload`    | Trigger age detection        | 8       |
| POST   | `/api/age-detect`    | Process and store age data   | 8       |
| GET    | `/api/age/{photoId}` | Get age for a photo          | 9       |
| POST   | `/api/age/batch`     | Get ages for multiple photos | 10      |
| DELETE | `/api/age/{photoId}` | Delete age metadata          | 11      |
| DELETE | `/api/age/batch`     | Delete multiple age records  | 11      |
