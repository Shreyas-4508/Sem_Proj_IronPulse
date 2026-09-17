# IronPulse: Smart Physical Training System

IronPulse is a semester project focused on developing a smart, user-friendly web-based Physical Training System. The platform is designed to help users organize, track, and improve their physical training through structured workouts, exercise guidance, progress monitoring, and fitness-related resources.

The project aims to combine a clean and responsive web interface with practical training features, creating a centralized platform for users to manage their fitness journey.

### Key Features

* Structured workout and exercise plans
* Exercise information and guidance
* Training and progress tracking
* User-friendly and responsive interface
* Fitness-related resources and recommendations
* Organized training dashboard
* Future scope for smart/personalized training recommendations

IronPulse is being developed as an academic semester project while applying concepts of web development, UI/UX design, database management, and software engineering.

**Project:** IronPulse – Smart Physical Training System
**Type:** Semester Project
**Platform:** Web Application
**Status:** In Development

## Local and Vercel setup

Create a local `.env` file from `.env.example`, or add the same variables in the Vercel project settings:

```text
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key
```

Only the Supabase anon/publishable key belongs in frontend environment variables. Do not add a service-role key. Run `supabase-schema.sql` in the Supabase SQL editor before using profile synchronization.
