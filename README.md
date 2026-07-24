# 🏬 Grand Shopping Mall - Smart Parking Slot Booking System

A full-stack, real-time **Smart Parking Management Application** built with **Python Django 5** and **PostgreSQL** database featuring glassmorphic UI design, gatekeeper entrance check-in, exit checkout with automated fee calculator, and role-based access control (Workers vs Admins).

---

## 🌟 Key Features

- **PostgreSQL Database Backend**: Persistent storage for parking locations, multi-floor slots (`G`, `L1`, `L2`, `EV Hub`), vehicle entry/exit logs, and payments.
- **🟢 Worker Entrance Gate (Check-In)**: Gatekeepers register arriving vehicles (plate number, type) and assign a slot. Automatically updates slot status in PostgreSQL to **`OCCUPIED`**.
- **🔴 Admin Exit Gate (Check-Out)**: Gatekeepers check out exiting vehicles. Calculates exact duration (hrs) & total fee, updates exit timestamp, and resets slot status back to **`AVAILABLE` (FREE)**.
- **🏬 Live Slot Board**: Real-time interactive floor map showing all slots color-coded in green (Free) vs red (Occupied).
- **🔒 Role-Based Auth (Workers vs Admins)**:
  - **Workers**: Access Entrance & Exit gates for parking operations. Analytics Dashboard & Admin settings are hidden and restricted.
  - **Admins**: Full access to **Operator Analytics**, revenue counters, and the **User/Admin Manager** to hire new workers or add 2nd Admins.

---

## 🚀 Tech Stack

- **Backend**: Python 3.12, Django 5.x, REST APIs
- **Database**: PostgreSQL (via `psycopg2-binary`)
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), JavaScript (Fetch API)

---

## 🛠️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd smart_parking_booking
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment / PostgreSQL**:
   Make sure PostgreSQL is running on `localhost:5432` with database `smart_parking_db`, or configure environment variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

4. **Run Migrations & Seed Data**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py seed_parking
   ```

5. **Start Development Server**:
   ```bash
   python manage.py runserver 8000
   ```
   Open `http://127.0.0.1:8000/` in your browser!

---

## 👥 Default Demo Credentials

- **Admin Account**:
  - Username: `admin`
  - Password: `adminpassword123`
- **Sample Hired Worker Account**:
  - Username: `worker_john`
  - Password: `johnpass123`
