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
   flask seed         # (optional) populate with sample data
   ```
4. Get an API Key from Together AI (www.together.ai) and store it under .env as TOGETHER_API_KEY.
5. **Run the web application:**
   ```bash
   python app.py
   ```

## Planned features / TODO

- Core AI chat
  - Feedback prompt after each AI session (rating + optional comment)
- Homework & content uploads
  - PDF upload for lecture notes / resources
- Content management
  - Simple CMS for teachers to organize/view PDFs and lecture notes by class
  - Search/filter by title, class, teacher, date
  - Versioning / replace file workflow
- Student / teacher UX
  - Show only student’s own interactions and teachers’ view of all interactions
  - Session restore: resume unfinished chats
- Processing & rendering
  - Strip LaTeX preamble / extract a MathJax-safe file from the homework
  - Consider the possibility of using markdown for math instead of MathJax 
  - Extract data from the pdfs to include within the context (using VLMs)
- Security & data
  - Access control for uploads and interactions
  - Sanitize inputs and uploaded files
  - Rate limiting and abuse protections
  - Secure secret/API handling (no keys in repo)
- Ops & quality
  - Unit tests for routes and file I/O
  - Logging and error reporting
  - Backup/export interactions/homeworks (JSON/CSV)
  - UX polish and accessibility
- Future enhancements
  - Teacher review tools / analytics on common student questions
  - Per-teacher prompt templates
  - Exportable lesson packs from lecture notes + homework
- Style
  - Mitigate inline styling in index.html and use css classes
