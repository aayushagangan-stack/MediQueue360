-- ============================================================
-- MediQueue 360
-- Final Database Schema
-- ============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS mediqueue360;

-- Select database
USE mediqueue360;


-- ============================================================
-- 1. USERS TABLE
-- Stores login credentials and common information
-- ============================================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    phone VARCHAR(20),

    role ENUM(
        'patient',
        'doctor',
        'receptionist',
        'admin'
    ) NOT NULL,

    status ENUM(
        'active',
        'inactive'
    ) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. PATIENTS TABLE
-- Stores patient-specific information
-- ============================================================

CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL UNIQUE,

    date_of_birth DATE,

    gender ENUM(
        'Male',
        'Female',
        'Other'
    ),

    address VARCHAR(255),

    emergency_contact VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- ============================================================
-- 3. DEPARTMENTS TABLE
-- Stores clinic/hospital departments
-- ============================================================

CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,

    department_name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    status ENUM(
        'active',
        'inactive'
    ) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. DOCTORS TABLE
-- Stores doctor-specific information
-- ============================================================

CREATE TABLE doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL UNIQUE,

    department_id INT,

    qualification VARCHAR(150),

    experience_years INT DEFAULT 0,

    consultation_fee DECIMAL(10,2) DEFAULT 0.00,

    about TEXT,

    profile_image VARCHAR(255),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON DELETE SET NULL
);


-- ============================================================
-- 5. RECEPTIONISTS TABLE
-- Stores receptionist-specific information
-- ============================================================

CREATE TABLE receptionists (
    receptionist_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL UNIQUE,

    employee_id VARCHAR(50) NOT NULL UNIQUE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- ============================================================
-- 6. DOCTOR SCHEDULES TABLE
-- Stores recurring weekly doctor availability
-- ============================================================

CREATE TABLE doctor_schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,

    doctor_id INT NOT NULL,

    day_of_week ENUM(
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ) NOT NULL,

    start_time TIME NOT NULL,

    end_time TIME NOT NULL,

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id)
        ON DELETE CASCADE,

    UNIQUE (
        doctor_id,
        day_of_week,
        start_time,
        end_time
    )
);


-- ============================================================
-- 7. APPOINTMENTS TABLE
-- Stores patient appointments
-- ============================================================

CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,

    patient_id INT NOT NULL,

    doctor_id INT NOT NULL,

    appointment_date DATE NOT NULL,

    appointment_time TIME DEFAULT NULL,

    reason_for_visit VARCHAR(255),

    status ENUM(
        'Pending',
        'Confirmed',
        'Completed',
        'Cancelled',
        'Rejected'
    ) DEFAULT 'Pending',

    cancellation_reason VARCHAR(255),

    booked_by_user_id INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE,

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id)
        ON DELETE CASCADE,

    FOREIGN KEY (booked_by_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);


-- ============================================================
-- 8. QUEUE ENTRIES TABLE
-- Digital queue/token management
-- Queue number is unique for each doctor on each date
-- ============================================================

CREATE TABLE queue_entries (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,

    appointment_id INT NOT NULL UNIQUE,

    patient_id INT NOT NULL,

    doctor_id INT NOT NULL,

    queue_date DATE NOT NULL,

    queue_number INT NOT NULL,

    queue_status ENUM(
        'Waiting',
        'In Consultation',
        'Completed',
        'Skipped'
    ) DEFAULT 'Waiting',

    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON DELETE CASCADE,

    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE,

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id)
        ON DELETE CASCADE,

    UNIQUE (
        doctor_id,
        queue_date,
        queue_number
    )
);


-- ============================================================
-- 9. VISIT RECORDS TABLE
-- Stores consultation details
-- ============================================================

CREATE TABLE visit_records (
    visit_id INT AUTO_INCREMENT PRIMARY KEY,

    appointment_id INT NOT NULL UNIQUE,

    patient_id INT NOT NULL,

    doctor_id INT NOT NULL,

    symptoms TEXT,

    diagnosis TEXT,

    doctor_notes TEXT,

    prescription TEXT,

    follow_up_date DATE,

    visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON DELETE CASCADE,

    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE,

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id)
        ON DELETE CASCADE
);


-- ============================================================
-- 10. MEDICAL REPORTS TABLE
-- Stores medical reports and uploaded files
-- ============================================================

CREATE TABLE medical_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,

    patient_id INT NOT NULL,

    doctor_id INT NOT NULL,

    visit_id INT,

    report_title VARCHAR(150) NOT NULL,

    report_description TEXT,

    file_path VARCHAR(255),

    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE CASCADE,

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id)
        ON DELETE CASCADE,

    FOREIGN KEY (visit_id)
        REFERENCES visit_records(visit_id)
        ON DELETE SET NULL
);


-- ============================================================
-- 11. CONTACT MESSAGES TABLE
-- Stores messages submitted through Contact Us
-- ============================================================

CREATE TABLE contact_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL,

    subject VARCHAR(150),

    message TEXT NOT NULL,

    status ENUM(
        'New',
        'Read',
        'Replied'
    ) DEFAULT 'New',

    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 12. NOTIFICATIONS TABLE
-- Stores notifications for users
-- ============================================================

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    title VARCHAR(150) NOT NULL,

    message TEXT NOT NULL,

    notification_type ENUM(
        'Appointment',
        'Queue',
        'Report',
        'System'
    ) DEFAULT 'System',

    is_read BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- ============================================================
-- INITIAL ADMIN ACCOUNT
-- ============================================================

INSERT INTO users
(
    full_name,
    email,
    password,
    phone,
    role,
    status
)
VALUES
(
    'MediQueue Admin',
    'admin@mediqueue360.com',
    '$2b$12$NCNhS43V51ncwbZOVVyJA.g2osgrnubi5uLasIGaMUvHfEGQcCDRC',
    '9876543210',
    'admin',
    'active'
);

-- ============================================================
-- DATABASE SETUP COMPLETE
-- ============================================================