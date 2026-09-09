# IronPulse Backend API 🏋️‍♂️

Production-ready Node.js / Express & PostgreSQL backend service for the **IronPulse Smart Physical Training System**.

---

## 📁 Project Architecture

```
ironpulse-backend/
├── server.js              # Express app entry point & route registration
├── db.js                  # PostgreSQL Pool connection manager
├── schema.sql             # SQL schema (users, athlete_profiles, feedback, workout_sessions)
├── init-db.js             # Automated database schema initializer
├── package.json           # NPM scripts & dependencies
├── .env.example           # Environment template
├── .env                   # Local environment configuration
├── middleware/
│   └── auth.js            # JWT verification & route protection middleware
└── routes/
    ├── auth.js            # Signup, login & token verification (/api/auth)
    ├── profile.js         # Athlete profile save/load, progress updates & reset (/api/profile)
    ├── feedback.js        # Star rating & comment submission (/api/feedback)
    └── workouts.js        # Workout session history & stats (/api/workouts)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js** (v16+)
- **PostgreSQL** (v12+) installed and running

### 2. Configure Environment
Create or edit `.env` in the `ironpulse-backend` directory:
```env
PORT=5000
NODE_ENV=development

# PostgreSQL settings
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=ironpulse_db
DB_SSL=false

# Or use full connection URL:
# DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ironpulse_db

JWT_SECRET=your_strong_secret_key_here
JWT_EXPIRES_IN=7d
CORS_ORIGIN=*
```

### 3. Install Dependencies
```bash
cd ironpulse-backend
npm install
```

### 4. Create Database & Initialize Schema
Create the database in PostgreSQL if it doesn't already exist:
```sql
CREATE DATABASE ironpulse_db;
```
Then run the automated schema initializer:
```bash
npm run init-db
```

### 5. Start the Server
```bash
# Production mode
npm start

# Development mode (with auto-reload)
npm run dev
```

The API server will run at `http://localhost:5000`.

---

## 📡 API Reference & Endpoints

### 🔐 1. Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/signup` | Register new user + create default profile | No |
| `POST` | `/api/auth/login` | Log in and receive JWT token | No |
| `GET` | `/api/auth/me` | Fetch authenticated user details | Yes (`Bearer <token>`) |

#### Signup Payload Example:
```json
{
  "email": "athlete@example.com",
  "password": "securepassword123",
  "full_name": "Alex Mercer"
}
```

---

### 👤 2. Athlete Profile (`/api/profile`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/profile` | Get current athlete profile | Yes |
| `PUT` | `/api/profile` | Upsert / update assessment & body metrics | Yes |
| `PATCH` | `/api/profile/progress` | Update streak, workouts, consistency | Yes |
| `POST` | `/api/profile/reset` | Reset profile metrics back to default | Yes |

#### Profile Update Payload Example:
```json
{
  "gender": "Male",
  "focusArea": ["Chest", "Arms"],
  "goals": ["Build Muscle"],
  "motivation": ["Improve Health"],
  "pushupLevel": "Beginner",
  "activityLevel": "Moderately Active",
  "weeklyTrainingDays": 4,
  "firstDay": "Monday",
  "weight": 72.5,
  "weightUnit": "KG",
  "height": 178,
  "heightUnit": "CM",
  "avatarUrl": "assets/male.png"
}
```

---

### ⭐ 3. Feedback (`/api/feedback`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/feedback` | Submit star rating (1-5), suitability & comment | Yes |
| `GET` | `/api/feedback` | Retrieve user feedback history | Yes |

#### Feedback Submission Example:
```json
{
  "rating": 5,
  "isSuitable": true,
  "comment": "Incredible routine! The audio pacing kept me focused."
}
```

---

### 🏃‍♂️ 4. Workout Sessions (`/api/workouts`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/workouts` | Record completed workout session | Yes |
| `GET` | `/api/workouts` | Get workout history & aggregated stats | Yes |

#### Workout Session Log Example:
```json
{
  "routineName": "Chest & Arms Hypertrophy Blast",
  "durationSeconds": 1320,
  "exercisesCompleted": 4,
  "totalExercises": 4,
  "notes": "Completed full reps with great form."
}
```
