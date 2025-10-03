# Math-Mate

Math-Mate is a comprehensive web-based platform that serves as both a content management system and an AI-powered tutoring assistant for homework assignments. Designed for teachers, professors, and students, Math-Mate streamlines the homework process and enhances learning through intelligent support.

## Features

- **Homework Upload & Management:** Educators can easily upload, organize, and manage homework assignments.
- **Student Homework Portal:** Students can view and access assigned homework through a user-friendly dashboard.
- **AI Tutor Assistance:** An integrated AI tutor helps students with their homework, offering explanations, hints, and step-by-step guidance.
- **Teacher Review Tools:** Teachers can review student interactions with the AI tutor, gaining insights into student progress and common challenges.
- **Student Feedback System:** After receiving AI assistance, students are prompted to provide feedback on the help they received.
- **RLHF-lite Improvement:** The platform uses Reinforcement Learning from Human Feedback (RLHF-lite) to continuously improve AI responses based on student feedback.

## Technology

- **Backend:** Python with Flask framework

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
3. **Run the web application:**
   ```bash
   python app.py
   ```

## Planned features / TODO

- Core AI chat
  - Feedback prompt after each AI session (rating + optional comment)
- Homework & content uploads
  - PDF upload for homework submissions
  - PDF upload for lecture notes / resources
  - Server-side PDF storage and metadata (uploader, class, title, upload_time)
  - Render PDFs in-browser (embedded viewer) and allow download
- Content management
  - Simple CMS for teachers to organize/view PDFs and lecture notes by class
  - Search/filter by title, class, teacher, date
  - Versioning / replace file workflow
- Student / teacher UX
  - Show only student’s own interactions and teachers’ view of all interactions
  - Session restore: resume unfinished chats
- Processing & rendering
  - Strip LaTeX preamble and render math via MathJax
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
