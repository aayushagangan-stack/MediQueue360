import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from database.db import get_db_connection
from flask import send_from_directory


doctor = Blueprint(
    "doctor",
    __name__,
    url_prefix="/doctor"
)


@doctor.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "doctor":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    return render_template(
        "doctor/dashboard.html"
    )


@doctor.route("/appointments")
@login_required
def appointments():

    if current_user.role != "doctor":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.dashboard")
        )


    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                doctor_id
            FROM doctors
            WHERE user_id = %s
            LIMIT 1
            """,
            (current_user.id,)
        )

        doctor = cursor.fetchone()

        if doctor is None:

            flash(
                "Doctor profile not found.",
                "danger"
            )

            return redirect(
                url_for("doctor.dashboard")
            )


        cursor.execute(
            """
            SELECT

                appointments.appointment_id,

                appointments.appointment_date,

                appointments.appointment_time,

                appointments.reason_for_visit,

                appointments.status,

                patient_user.full_name AS patient_name

            FROM appointments

            JOIN patients
                ON appointments.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            WHERE appointments.doctor_id = %s
            AND appointments.status = 'Confirmed'

            ORDER BY
                appointments.appointment_date,
                appointments.appointment_time
            """,
            (doctor["doctor_id"],)
        )

        appointments = cursor.fetchall()

        return render_template(
            "doctor/appointments.html",
            appointments=appointments
        )

    finally:

        cursor.close()

        connection.close()


@doctor.route(
    "/consult/<int:appointment_id>",
    methods=["GET", "POST"]
)
@login_required
def consult_patient(appointment_id):

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.appointments")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                appointments.*,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name

            FROM appointments

            JOIN patients
                ON appointments.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            JOIN doctors
                ON appointments.doctor_id = doctors.doctor_id

            JOIN users AS doctor_user
                ON doctors.user_id = doctor_user.user_id

            WHERE appointments.appointment_id = %s

            LIMIT 1
            """,
            (appointment_id,)
        )

        appointment = cursor.fetchone()

        if appointment is None:

            flash(
                "Appointment not found.",
                "danger"
            )

            return redirect(
                url_for("doctor.appointments")
            )

        if request.method == "POST":

            symptoms = request.form.get("symptoms")
            diagnosis = request.form.get("diagnosis")
            prescription = request.form.get("prescription")
            doctor_notes = request.form.get("doctor_notes")
            follow_up_date = request.form.get("follow_up_date")

            cursor.execute(
                """
                INSERT INTO visit_records
                (
                    appointment_id,
                    patient_id,
                    doctor_id,
                    symptoms,
                    diagnosis,
                    doctor_notes,
                    prescription,
                    follow_up_date
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    appointment_id,
                    appointment["patient_id"],
                    appointment["doctor_id"],
                    symptoms,
                    diagnosis,
                    doctor_notes,
                    prescription,
                    follow_up_date if follow_up_date else None
                )
            )

            cursor.execute(
                """
                UPDATE appointments
                SET status = 'Completed'
                WHERE appointment_id = %s
                """,
                (appointment_id,)
            )

            cursor.execute(
                """
                UPDATE queue_entries
                SET queue_status = 'Completed'
                WHERE appointment_id = %s
                """,
                (appointment_id,)
            )

            connection.commit()

            flash(
                "Consultation saved successfully.",
                "success"
            )

            return redirect(
                url_for("doctor.appointments")
            )

        return render_template(
            "doctor/consult_patient.html",
            appointment=appointment
        )

    finally:

        cursor.close()
        connection.close()

@doctor.route("/patients")
@login_required
def patients():

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.dashboard")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT DISTINCT

                patients.patient_id,

                patient_user.full_name AS patient_name,

                patient_user.email,

                patient_user.phone,

                patients.gender,

                patients.date_of_birth

            FROM visit_records

            JOIN patients
                ON visit_records.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            JOIN doctors
                ON visit_records.doctor_id = doctors.doctor_id

            WHERE doctors.user_id = %s

            ORDER BY patient_user.full_name ASC
            """,
            (current_user.id,)
        )

        patients = cursor.fetchall()

        return render_template(
            "doctor/patients.html",
            patients=patients
        )

    finally:

        cursor.close()
        connection.close()


@doctor.route("/records")
@login_required
def records():

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.dashboard")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                visit_records.visit_id,

                visit_records.patient_id,

                visit_records.diagnosis,

                appointments.appointment_date,

                appointments.appointment_time,

                patient_user.full_name AS patient_name

            FROM visit_records

            JOIN appointments
                ON visit_records.appointment_id = appointments.appointment_id

            JOIN patients
                ON visit_records.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            JOIN doctors
                ON visit_records.doctor_id = doctors.doctor_id

            JOIN users AS doctor_user
                ON doctors.user_id = doctor_user.user_id

            WHERE doctor_user.user_id = %s

            ORDER BY appointments.appointment_date DESC,
                     appointments.appointment_time DESC
            """,
            (current_user.id,)
        )

        records = cursor.fetchall()

        return render_template(
            "doctor/records.html",
            records=records
        )

    finally:

        cursor.close()
        connection.close()

@doctor.route("/reports")
@login_required
def reports():

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT

            medical_reports.*,

            users.full_name AS patient_name

        FROM medical_reports

        JOIN patients
            ON medical_reports.patient_id = patients.patient_id

        JOIN users
            ON patients.user_id = users.user_id

        ORDER BY report_date DESC
        """
    )

    reports = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "doctor/reports.html",
        reports=reports
    )

@doctor.route(
    "/upload-report/<int:visit_id>",
    methods=["GET", "POST"]
)
@login_required
def upload_report(visit_id):
    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.records")
        )


    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                visit_records.*,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name

            FROM visit_records

            JOIN patients
                ON visit_records.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            JOIN doctors
                ON visit_records.doctor_id = doctors.doctor_id

            JOIN users AS doctor_user
                ON doctors.user_id = doctor_user.user_id

            WHERE visit_records.visit_id = %s

            LIMIT 1
            """,
            (visit_id,)
        )

        visit = cursor.fetchone()

        if visit is None:

            flash(
                "Visit record not found.",
                "danger"
            )

            return redirect(
                url_for("doctor.records")
            )


        if request.method == "POST":

            report_title = request.form.get(
                "report_title"
            )

            report_description = request.form.get(
                "report_description"
            )

            uploaded_file = request.files.get(
                "report_file"
            )

            if uploaded_file is None or uploaded_file.filename == "":

                flash(
                    "Please select a file.",
                    "warning"
                )

                return redirect(
                    url_for(
                        "doctor.upload_report",
                        visit_id=visit_id
                    )
                )


            filename = secure_filename(
                uploaded_file.filename
            )


            save_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
            )


            uploaded_file.save(
                save_path
            )

            file_path = filename

            cursor.execute(
                """
                INSERT INTO medical_reports
                (
                    patient_id,
                    doctor_id,
                    visit_id,
                    report_title,
                    report_description,
                    file_path
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    visit["patient_id"],
                    visit["doctor_id"],
                    visit_id,
                    report_title,
                    report_description,
                    file_path
                )
            )


            connection.commit()


            flash(
                "Medical report uploaded successfully.",
                "success"
            )


            return redirect(
                url_for("doctor.reports")
            )

        return render_template(
            "doctor/upload_report.html",
            visit=visit
        )

    except Exception as e:

        connection.rollback()

        flash(
            str(e),
            "danger"
        )

        return redirect(
            url_for("doctor.records")
        )

    finally:

        cursor.close()
        connection.close()

@doctor.route("/report-file/<path:filename>")
@login_required
def report_file(filename):

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )      

@doctor.route("/patient/<int:patient_id>")
@login_required
def patient_profile(patient_id):

    if current_user.role != "doctor":

        flash(
            "You do not have permission.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    if connection is None:

        flash(
            "Database connection failed.",
            "danger"
        )

        return redirect(
            url_for("doctor.patients")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                patients.patient_id,
                patient_user.full_name AS patient_name,
                patient_user.email,
                patient_user.phone,
                patients.gender,
                patients.date_of_birth,
                patients.address,
                patients.emergency_contact

            FROM patients

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            WHERE patients.patient_id = %s

            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if patient is None:

            flash(
                "Patient not found.",
                "danger"
            )

            return redirect(
                url_for("doctor.patients")
            )

        return render_template(
            "doctor/patient_profile.html",
            patient=patient
        )

    finally:

        cursor.close()
        connection.close() 