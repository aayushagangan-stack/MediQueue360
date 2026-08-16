# MediQueue360
MediQueue360 – A digital clinic appointment and queue management system built with Flask, MySQL, HTML, CSS, JavaScript, and Bootstrap.

# MediQueue360

MediQueue360 is a web-based digital clinic appointment and queue management system developed as part of my web development internship.

The system helps manage patients, doctors, receptionists, administrators, appointments, digital queues, consultations, prescriptions, and medical reports through separate role-based dashboards.

## Features

### Patient
- Register and log in securely
- View and edit profile
- Book doctor appointments
- View booked appointments
- Manage appointments
- View medical reports
- View consultation and prescription details

### Doctor
- Log in through a dedicated dashboard
- View appointments
- Manage appointment status
- Conduct patient consultations
- Add diagnosis and doctor notes
- Add prescriptions
- Manage patient reports
- View doctor schedule

### Receptionist
- View and manage appointments
- Manage the digital patient queue
- Assign queue numbers
- Track patient visits
- Manage appointment-related activities

### Administrator
- Secure admin login
- Manage users
- Add patients, doctors, and receptionists
- Manage departments
- View and manage appointments
- View system records
- Manage overall clinic information

## Technologies Used

- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **Backend:** Python, Flask
- **Database:** MySQL
- **Authentication:** Flask-Login, Flask-Bcrypt
- **Database Connectivity:** MySQL Connector/Python
- **Development Environment:** Visual Studio Code

## Project Structure

MediQueue360/
│
├── database/
│   ├── db.py
│   └── schema.sql
│
├── models/
│   └── user_model.py
│
├── routes/
│   ├── admin_routes.py
│   ├── auth_routes.py
│   ├── doctor_routes.py
│   ├── patient_routes.py
│   └── receptionist_routes.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   └── js/
│       └── script.js
│
├── templates/
│   ├── admin/
│   ├── doctor/
│   ├── patient/
│   ├── receptionist/
│   └── ...
│
├── uploads/
├── app.py
├── requirements.txt
└── README.md
