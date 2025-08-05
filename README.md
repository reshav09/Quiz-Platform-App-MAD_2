```markdown
# Quiz Master - V2 🧠

A multi-user quiz platform designed to simulate an exam preparation portal for multiple courses. The platform supports both administrative and user functionalities.

> ⚠️ **Note:**  
> This project is **not complete**. Some functionalities, particularly related to route handling and data flow between frontend and backend, are pending or partially implemented. It is not production-ready.

---

## 🗂️ Project Structure

```

├── README.md
├── backend/
│   ├── app.py                  # Main Flask application
│   ├── config.py              # Flask and DB configurations
│   ├── celery_config.py       # Celery + Redis settings
│   ├── quiz_master.db         # SQLite database
│   ├── tasks.py               # Celery task definitions
│   ├── auth/                  # Authentication logic (JWT)
│   ├── models/                # SQLAlchemy models
│   ├── routes/                # Route definitions (admin, quiz, etc.)
│   └── utils/                 # Helper functions (caching, etc.)
├── frontend/
│   ├── index.html             # Main HTML file
│   └── static/
│       ├── css/styles.css
│       └── js/
│           ├── app.js
│           ├── charts.js
│           └── debug.js
├── requirements.txt           # Python dependencies

```

---

## ⚙️ Tech Stack

### Backend
- **Flask** – REST APIs
- **SQLite** – Embedded database
- **Redis** – Caching and broker for Celery
- **Celery** – Async jobs and task queue
- **JWT** – Role-based user authentication

### Frontend
- **HTML, CSS, Bootstrap** – UI and layout
- **JavaScript + Chart.js** – Client-side logic and charts

---

## 🧑‍💻 User Roles

### 🔒 Admin (Quiz Master)
- Single admin account (hardcoded in DB)
- Manage subjects, chapters, quizzes, and users
- View quiz performance and user analytics
- Export quiz/user data via CSV (async job)
- Scheduled reminders and monthly activity reports

### 👤 Users
- Register and log in
- Browse subjects and chapters
- Attempt quizzes (timed)
- View quiz history and performance
- Export personal quiz data

---

## 🔁 Async Jobs (Using Celery)

- **Daily Reminders:** Notify inactive users about new quizzes
- **Monthly Report:** Email-based performance summary
- **CSV Export (Triggered by User/Admin):** 
  - Users: Export their quiz history
  - Admin: Export user performance across all quizzes

---

## 💾 Database Models (Simplified)

- **User:** id, email, password, name, DOB, qualification
- **Subject:** id, name, description
- **Chapter:** id, name, subject_id
- **Quiz:** id, chapter_id, date, duration
- **Question:** id, quiz_id, question, options, correct answer
- **Score:** id, quiz_id, user_id, score, timestamp

---

## 🚧 Known Issues / Work in Progress

- Several **route handlers** are incomplete or broken
- Frontend/backend **integration** is partial
- CSV export needs full UI integration
- Admin dashboard UI needs polish
- **Celery jobs** configured but not tested thoroughly

---

## 🏁 Getting Started (Local Setup)

### 1. Clone the Repository
```bash
git clone <repo-url>
cd <project-dir>
````

### 2. Set Up Python Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Redis Server

```bash
redis-server
```

### 4. Run Celery Worker

```bash
celery -A backend.tasks.celery worker --loglevel=info
```

### 5. Run Flask Application

```bash
python backend/app.py
```

### 6. Access the App

Visit: [http://localhost:5000](http://localhost:5000)

---

## ✅ Completed Features

* User authentication via JWT
* Basic admin dashboard routing
* Quiz model, structure, and basic CRUD
* Redis caching utility
* UI mockups using Bootstrap

---

## ❌ Pending / Incomplete

* Full route wiring for quiz operations
* Final admin dashboard views
* Complete testing of Celery task flows
* Production-level validations (both client/server)

---

## 🔐 Admin Credentials (for demo)

```text
Username: admin
Password: admin123
```

> ⚠️ These credentials are preloaded when initializing the database programmatically.

---

## 📜 License

This project is intended for educational purposes only.
---

## 📝 Author Notes

If you wish to complete or fork this project, feel free to raise issues or suggestions.

