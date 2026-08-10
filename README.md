---
title: "Math-Mate"
emoji: "👀"
colorFrom: "pink"
colorTo: "indigo"
sdk: "docker"
pinned: false
license: "apache-2.0"
---

# Math-Mate

Math-Mate is a comprehensive web-based platform that serves as both a content management system and an AI-powered tutoring assistant for homework assignments. Designed for teachers, professors, and students, Math-Mate streamlines the homework process and enhances learning through intelligent support.

## Features

- **Accounts & Roles:** Teachers and students sign up for their own accounts, with role-aware dashboards and access control throughout the app.
- **Classes & Enrollment:** Teachers create classes that come with a unique invite code. Students join a class with that code, and teachers can also invite an existing student directly by email. Assignments and resources are organized per class.
- **Homework Upload & Management:** Educators can easily upload, organize, and manage homework assignments within their classes.
- **Student Homework Portal:** Students can view and access assigned homework through a user-friendly dashboard.
- **AI Tutor Assistance:** An integrated AI tutor helps students with their homework, offering explanations, hints, and step-by-step guidance.
- **Teacher Review Tools:** Teachers can review student interactions with the AI tutor, gaining insights into student progress and common challenges.
- **Student Feedback System:** After receiving AI assistance, students are prompted to provide feedback on the help they received.
- **RLHF-lite Improvement:** The platform uses Reinforcement Learning from Human Feedback (RLHF-lite) to continuously improve AI responses based on student feedback.

## Technology

- **Backend:** Python with Flask framework
- **Database:** SQLAlchemy models with Flask-Migrate (Alembic) migrations

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd math-mate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up the database:**
   ```bash
   flask db upgrade   # create the tables from the migrations
   python seed.py         # (optional) populate with sample data
   ```
4. Get an API Key from Together AI (www.together.ai) and store it under .env as TOGETHER_API_KEY.
5. **Run the web application:**
   ```bash
   python app.py
   ```
