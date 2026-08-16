from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from database.db import get_db_connection
from flask_login import login_required, current_user


receptionist = Blueprint(
    "receptionist",
    __name__,
    url_prefix="/receptionist"
)


@receptionist.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "receptionist":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    return render_template(
        "receptionist/dashboard.html"
    )


@receptionist.route("/appointments")
@login_required
def appointments():

    if current_user.role != "receptionist":

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
            url_for("receptionist.dashboard")
        )


    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""

            SELECT

                appointments.appointment_id,

                appointments.appointment_date,

                appointments.appointment_time,

                appointments.reason_for_visit,

                appointments.status,

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

            WHERE appointments.status = 'Pending'

            ORDER BY appointments.appointment_date ASC

        """)

        appointments = cursor.fetchall()

        return render_template(
            "receptionist/appointments.html",
            appointments=appointments
        )

    finally:

        cursor.close()

        connection.close()

@receptionist.route(
    "/assign-time/<int:appointment_id>",
    methods=["GET", "POST"]
)
@login_required
def assign_time(appointment_id):

    if current_user.role != "receptionist":

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
            url_for("receptionist.appointments")
        )


    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                appointments.*,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name,

                departments.department_name

            FROM appointments

            JOIN patients
                ON appointments.patient_id = patients.patient_id

            JOIN users AS patient_user
                ON patients.user_id = patient_user.user_id

            JOIN doctors
                ON appointments.doctor_id = doctors.doctor_id

            JOIN users AS doctor_user
                ON doctors.user_id = doctor_user.user_id

            LEFT JOIN departments
                ON doctors.department_id = departments.department_id

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
                url_for("receptionist.appointments")
            )


        if request.method == "POST":

            appointment_time = request.form.get(
                "appointment_time"
            )

            if not appointment_time:

                flash(
                    "Please select an appointment time.",
                    "warning"
                )

                return redirect(
                    url_for(
                        "receptionist.assign_time",
                        appointment_id=appointment_id
                    )
                )

            # Confirm appointment

            cursor.execute(
                """
                UPDATE appointments
                SET
                    appointment_time = %s,
                    status = 'Confirmed'
                WHERE appointment_id = %s
                """,
                (
                    appointment_time,
                    appointment_id
                )
            )


            # Check whether queue entry already exists

            cursor.execute(
                """
                SELECT queue_id
                FROM queue_entries
                WHERE appointment_id = %s
                """,
                (appointment_id,)
            )

            existing_queue = cursor.fetchone()


            if existing_queue is None:

                # Generate Queue Number

                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM queue_entries
                    WHERE doctor_id = %s
                    AND queue_date = %s
                    """,
                    (
                        appointment["doctor_id"],
                        appointment["appointment_date"]
                    )
                )

                queue_count = cursor.fetchone()["total"]

                queue_number = queue_count + 1


                # Insert Queue Entry

                cursor.execute(
                    """
                    INSERT INTO queue_entries
                    (
                        appointment_id,
                        patient_id,
                        doctor_id,
                        queue_date,
                        queue_number,
                        queue_status
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'Waiting'
                    )
                    """,
                    (
                        appointment_id,
                        appointment["patient_id"],
                        appointment["doctor_id"],
                        appointment["appointment_date"],
                        queue_number
                    )
                )

            connection.commit()

            flash(
                "Appointment confirmed successfully.",
                "success"
            )

            return redirect(
                url_for("receptionist.appointments")
            )

        return render_template(
            "receptionist/assign_time.html",
            appointment=appointment
        )

    finally:

        cursor.close()
        connection.close()

@receptionist.route("/queue")
@login_required
def queue():

    if current_user.role != "receptionist":

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
            url_for("receptionist.dashboard")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
    """
    SELECT
        queue_entries.queue_id,
        queue_entries.queue_number,
        queue_entries.queue_status,
        queue_entries.arrival_time,

        appointments.appointment_date,
        appointments.appointment_time,

        patient_user.full_name AS patient_name,
        doctor_user.full_name AS doctor_name

    FROM queue_entries

    JOIN appointments
        ON queue_entries.appointment_id =
           appointments.appointment_id

    JOIN patients
        ON queue_entries.patient_id =
           patients.patient_id

    JOIN users AS patient_user
        ON patients.user_id =
           patient_user.user_id

    JOIN doctors
        ON queue_entries.doctor_id =
           doctors.doctor_id

    JOIN users AS doctor_user
        ON doctors.user_id =
           doctor_user.user_id

    WHERE
        queue_entries.queue_status IN (
            'Waiting',
            'In Consultation'
        )

        OR queue_entries.queue_id IN (

            SELECT queue_id
            FROM (
                SELECT
                    qe.queue_id

                FROM queue_entries qe

                JOIN appointments a
                    ON qe.appointment_id =
                       a.appointment_id

                WHERE qe.queue_status = 'Completed'

                ORDER BY
                    a.appointment_date DESC,
                    a.appointment_time DESC,
                    qe.queue_id DESC

                LIMIT 3

            ) AS recent_completed
        )

    ORDER BY
        appointments.appointment_date ASC,
        appointments.appointment_time ASC,
        queue_entries.queue_number ASC
    """
)

        queue_entries = cursor.fetchall()

        return render_template(
            "receptionist/queue.html",
            queue_entries=queue_entries
        )

    finally:

        cursor.close()
        connection.close()

@receptionist.route(
    "/update-queue/<int:queue_id>/<status>",
    methods=["POST"]
)
@login_required
def update_queue_status(queue_id, status):

    if current_user.role != "receptionist":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    connection = get_db_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE queue_entries

            SET queue_status = %s

            WHERE queue_id = %s
            """,
            (
                status,
                queue_id
            )
        )

        connection.commit()

        flash(
            "Queue updated successfully.",
            "success"
        )

    finally:

        cursor.close()

        connection.close()

    return redirect(
        url_for("receptionist.queue")
    )        

@receptionist.route("/reports")
@login_required
def reports():

    if current_user.role != "receptionist":
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
            "Unable to connect to the database.",
            "danger"
        )
        return redirect(
            url_for("receptionist.dashboard")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                medical_reports.report_id,
                medical_reports.report_title,
                medical_reports.file_path,
                medical_reports.report_date,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name

            FROM medical_reports

            INNER JOIN patients
                ON medical_reports.patient_id =
                patients.patient_id

            INNER JOIN users AS patient_user
                ON patients.user_id =
                patient_user.user_id

            INNER JOIN doctors
                ON medical_reports.doctor_id =
                doctors.doctor_id

            INNER JOIN users AS doctor_user
                ON doctors.user_id =
                doctor_user.user_id

            ORDER BY medical_reports.report_date DESC
            """
        )

        reports_data = cursor.fetchall()

        return render_template(
            "receptionist/patient_reports.html",
            reports=reports_data
        )

    except Exception as e:

        print(
            "RECEPTIONIST REPORTS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load patient reports.",
            "danger"
        )

        return redirect(
            url_for("receptionist.dashboard")
        )

    finally:

        cursor.close()
        connection.close()


@receptionist.route("/reports/<int:report_id>")
@login_required
def view_report(report_id):

    if current_user.role != "receptionist":

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
            "Unable to connect to the database.",
            "danger"
        )

        return redirect(
            url_for("receptionist.reports")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                medical_reports.report_id,
                medical_reports.report_title,
                medical_reports.report_description,
                medical_reports.report_date,
                medical_reports.file_path,

                visit_records.visit_id,
                visit_records.visit_date,
                visit_records.symptoms,
                visit_records.diagnosis,
                visit_records.prescription,
                visit_records.doctor_notes,
                visit_records.follow_up_date,

                patient_user.full_name AS patient_name,
                doctor_user.full_name AS doctor_name

            FROM medical_reports

            INNER JOIN visit_records
                ON medical_reports.visit_id =
                   visit_records.visit_id

            INNER JOIN patients
                ON medical_reports.patient_id =
                   patients.patient_id

            INNER JOIN users AS patient_user
                ON patients.user_id =
                   patient_user.user_id

            INNER JOIN doctors
                ON medical_reports.doctor_id =
                   doctors.doctor_id

            INNER JOIN users AS doctor_user
                ON doctors.user_id =
                   doctor_user.user_id

            WHERE medical_reports.report_id = %s

            LIMIT 1
            """,
            (report_id,)
        )

        report = cursor.fetchone()

        if report is None:

            flash(
                "Report not found.",
                "warning"
            )

            return redirect(
                url_for("receptionist.reports")
            )

        return render_template(
            "receptionist/view_report.html",
            report=report
        )

    except Exception as e:

        print(
            "RECEPTIONIST VIEW REPORT ERROR:",
            repr(e)
        )

        flash(
            "Unable to open the report.",
            "danger"
        )

        return redirect(
            url_for("receptionist.reports")
        )

    finally:

        cursor.close()
        connection.close()
        
@receptionist.route("/reports/file/<path:filename>")
@login_required
def view_report_file(filename):

    if current_user.role != "receptionist":

        flash(
            "You do not have permission to access this file.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    return send_from_directory(
        "uploads",
        filename
    )

@receptionist.route("/patient-records")
@login_required
def patient_records():

    if current_user.role != "receptionist":

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
            "Unable to connect to the database.",
            "danger"
        )

        return redirect(
            url_for("receptionist.dashboard")
        )


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        search = request.args.get(
            "search",
            ""
        ).strip()


        query = """
            SELECT
                patients.patient_id,
                patient_user.full_name AS patient_name,
                patient_user.email AS patient_email

            FROM users AS patient_user

            LEFT JOIN patients
                ON patient_user.user_id = patients.user_id

            WHERE patient_user.role = 'patient'
        """

        params = []


        if search:

            query += """
                AND (
                    CAST(patients.patient_id AS CHAR) LIKE %s
                    OR patient_user.full_name LIKE %s
                    OR patient_user.email LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        query += """
            ORDER BY patient_user.full_name ASC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        patients = cursor.fetchall()


        return render_template(
            "receptionist/patient_records.html",
            patients=patients,
            search=search
        )

    except Exception as e:

        print(
            "PATIENT RECORDS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load patient records.",
            "danger"
        )

        return redirect(
            url_for("receptionist.dashboard")
        )

    finally:

        cursor.close()
        connection.close()


@receptionist.route("/patient-profile/<int:patient_id>")
@login_required
def patient_profile(patient_id):

    if current_user.role != "receptionist":

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
            "Unable to connect to the database.",
            "danger"
        )

        return redirect(
            url_for("receptionist.patient_records")
        )


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT

                patients.patient_id,

                patient_user.full_name,
                patient_user.email,
                patient_user.phone,

                patients.date_of_birth,
                patients.gender,
                patients.emergency_contact,
                patients.address

            FROM patients

            INNER JOIN users AS patient_user
                ON patients.user_id =
                   patient_user.user_id

            WHERE patients.patient_id = %s

            LIMIT 1
            """,
            (patient_id,)
        )


        patient = cursor.fetchone()


        if patient is None:

            flash(
                "Patient record not found.",
                "warning"
            )

            return redirect(
                url_for("receptionist.patient_records")
            )


        return render_template(
            "receptionist/patient_profile.html",
            patient=patient
        )


    except Exception as e:

        print(
            "PATIENT PROFILE ERROR:",
            repr(e)
        )

        flash(
            "Unable to load patient profile.",
            "danger"
        )

        return redirect(
            url_for("receptionist.patient_records")
        )


    finally:

        cursor.close()
        connection.close()