from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask import send_from_directory
from database.db import get_db_connection


patient = Blueprint("patient", __name__, url_prefix="/patient")


@patient.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "patient":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return redirect(
            url_for("home")
        )


    return render_template(
        "patient/dashboard.html"
    )

@patient.route("/profile")
@login_required
def profile():

    if current_user.role != "patient":

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
            url_for("patient.dashboard")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                date_of_birth,
                gender,
                address,
                emergency_contact
            FROM patients
            WHERE user_id = %s
            LIMIT 1
            """,
            (current_user.id,)
        )

        patient_data = cursor.fetchone()

        if patient_data is None:

            patient_data = {
                "date_of_birth": None,
                "gender": None,
                "address": None,
                "emergency_contact": None
            }

        return render_template(
            "patient/profile.html",
            patient_data=patient_data
        )

    finally:

        cursor.close()
        connection.close()

@patient.route(
    "/edit-profile",
    methods=["GET", "POST"]
)
@login_required
def edit_profile():

    if current_user.role != "patient":

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
            url_for("patient.profile")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        if request.method == "POST":

            full_name = request.form.get(
                "full_name",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            date_of_birth = request.form.get(
                "date_of_birth"
            )

            gender = request.form.get(
                "gender"
            )

            address = request.form.get(
                "address",
                ""
            ).strip()

            emergency_contact = request.form.get(
                "emergency_contact",
                ""
            ).strip()


            if not full_name:

                flash(
                    "Full name is required.",
                    "warning"
                )

                return redirect(
                    url_for("patient.edit_profile")
                )


            # Update basic user information

            cursor.execute(
                """
                UPDATE users
                SET
                    full_name = %s,
                    phone = %s
                WHERE user_id = %s
                """,
                (
                    full_name,
                    phone,
                    current_user.id
                )
            )


            # Update patient information

            cursor.execute(
                """
                UPDATE patients
                SET
                    date_of_birth = %s,
                    gender = %s,
                    address = %s,
                    emergency_contact = %s
                WHERE user_id = %s
                """,
                (
                    date_of_birth if date_of_birth else None,
                    gender if gender else None,
                    address if address else None,
                    emergency_contact if emergency_contact else None,
                    current_user.id
                )
            )


            connection.commit()


            flash(
                "Profile updated successfully.",
                "success"
            )

            return redirect(
                url_for("patient.profile")
            )


        # Load existing patient information

        cursor.execute(
            """
            SELECT
                date_of_birth,
                gender,
                address,
                emergency_contact
            FROM patients
            WHERE user_id = %s
            LIMIT 1
            """,
            (current_user.id,)
        )

        patient_data = cursor.fetchone()


        if patient_data is None:

            patient_data = {
                "date_of_birth": None,
                "gender": None,
                "address": None,
                "emergency_contact": None
            }


        return render_template(
            "patient/edit_profile.html",
            patient_data=patient_data
        )


    except Exception as e:

        connection.rollback()

        print(
            "EDIT PROFILE ERROR:",
            e
        )

        flash(
            "Unable to update your profile.",
            "danger"
        )

        return redirect(
            url_for("patient.edit_profile")
        )


    finally:

        cursor.close()
        connection.close()

@patient.route(
    "/book-appointment",
    methods=["GET", "POST"]
)
@login_required
def book_appointment():

    if current_user.role != "patient":

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
            url_for("patient.dashboard")
        )


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT
                doctors.doctor_id,
                users.full_name,
                doctors.department_id,
                departments.department_name,
                doctors.qualification,
                doctors.experience_years,
                doctors.consultation_fee,
                doctors.about,
                doctors.profile_image
            FROM doctors
            INNER JOIN users
                ON doctors.user_id = users.user_id
            LEFT JOIN departments
                ON doctors.department_id =
                   departments.department_id
            WHERE users.status = 'active'
            ORDER BY users.full_name
            """
        )

        doctors = cursor.fetchall()
        # Get active departments for appointment booking
        cursor.execute(
            """
            SELECT
                department_id,
                department_name
            FROM departments
            WHERE status = 'active'
            ORDER BY department_name
            """
        )

        departments = cursor.fetchall()


        if request.method == "POST":

            doctor_id = request.form.get(
                "doctor_id"
            )

            appointment_date = request.form.get(
                "appointment_date"
            )

            reason_for_visit = request.form.get(
                "reason_for_visit",
                ""
            ).strip()


            if not doctor_id or not appointment_date:

                flash(
                    "Please fill in all required appointment details.",
                    "warning"
                )

                return redirect(
                    url_for("patient.book_appointment")
                )


            cursor.execute(
                """
                SELECT patient_id
                FROM patients
                WHERE user_id = %s
                LIMIT 1
                """,
                (current_user.id,)
            )

            patient_data = cursor.fetchone()


            if patient_data is None:

                flash(
                    "Patient profile not found.",
                    "danger"
                )

                return redirect(
                    url_for("patient.dashboard")
                )


            cursor.execute(
                """
                INSERT INTO appointments
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    reason_for_visit,
                    status,
                    booked_by_user_id
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    'Pending',
                    %s
                )
                """,
                (
                    patient_data["patient_id"],
                    doctor_id,
                    appointment_date,                    
                    reason_for_visit,
                    current_user.id
                )
            )


            connection.commit()


            flash(
                "Appointment request submitted successfully. The clinic will assign your appointment time after reviewing your request. Please check My Appointments for updates.",
                "success"
            )

            return redirect(
                url_for("patient.appointments")
            )


        return render_template(
            "book_appointment.html",
            doctors=doctors,
            departments=departments
        )


    finally:

        cursor.close()
        connection.close()


@patient.route("/appointments")
@login_required
def appointments():

    if current_user.role != "patient":

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
            url_for("patient.dashboard")
        )


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT
                appointments.appointment_id,
                appointments.appointment_date,
                appointments.appointment_time,
                appointments.reason_for_visit,
                appointments.status,
                users.full_name AS doctor_name,
                departments.department_name
            FROM appointments

            INNER JOIN patients
                ON appointments.patient_id =
                   patients.patient_id

            INNER JOIN doctors
                ON appointments.doctor_id =
                   doctors.doctor_id

            INNER JOIN users
                ON doctors.user_id =
                   users.user_id

            LEFT JOIN departments
                ON doctors.department_id =
                   departments.department_id

            WHERE patients.user_id = %s

            ORDER BY
                appointments.appointment_date DESC,
                appointments.appointment_time DESC
            """,
            (current_user.id,)
        )

        appointments_data = cursor.fetchall()


        return render_template(
            "patient/appointments.html",
            appointments=appointments_data
        )


    finally:

        cursor.close()
        connection.close()


@patient.route(
    "/appointments/<int:appointment_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_appointment(
    appointment_id
):

    if current_user.role != "patient":

        flash(
            "You do not have permission to perform this action.",
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
            url_for("patient.appointments")
        )


    cursor = connection.cursor()


    try:

        cursor.execute(
            """
            UPDATE appointments

            INNER JOIN patients
                ON appointments.patient_id =
                   patients.patient_id

            SET appointments.status = 'Cancelled'

            WHERE appointments.appointment_id = %s

            AND patients.user_id = %s

            AND appointments.status
                IN ('Pending', 'Confirmed')
            """,
            (
                appointment_id,
                current_user.id
            )
        )


        if cursor.rowcount == 0:

            flash(
                "Appointment could not be cancelled.",
                "warning"
            )

        else:

            connection.commit()

            flash(
                "Appointment cancelled successfully.",
                "success"
            )


        return redirect(
            url_for("patient.appointments")
        )


    finally:

        cursor.close()
        connection.close()

# ============================================================
# MEDICAL REPORTS
# ============================================================

@patient.route("/medical-reports")
@login_required
def medical_reports():

    if current_user.role != "patient":

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
            url_for("patient.dashboard")
        )

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                medical_reports.report_id,
                medical_reports.report_title,
                medical_reports.file_path,
                medical_reports.report_date,
                

                doctor_user.full_name AS doctor_name

            FROM medical_reports

            INNER JOIN patients
                ON medical_reports.patient_id =
                   patients.patient_id

            INNER JOIN doctors
                ON medical_reports.doctor_id =
                   doctors.doctor_id

            INNER JOIN users AS doctor_user
                ON doctors.user_id =
                   doctor_user.user_id

            WHERE patients.user_id = %s

            ORDER BY
                medical_reports.report_date DESC
            """,
            (current_user.id,)
        )

        reports = cursor.fetchall()

        return render_template(
            "patient/medical_reports.html",
            reports=reports
        )

    except Exception as e:

        print(
            "MEDICAL REPORTS ERROR:",
            repr(e)
        )

        flash(
            "Unable to load medical reports.",
            "danger"
        )

        return redirect(
            url_for("patient.dashboard")
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# VIEW MEDICAL REPORT FILE
# ============================================================

@patient.route("/medical-reports/<int:report_id>")
@login_required
def view_report(report_id):

    if current_user.role != "patient":

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
            url_for("patient.medical_reports")
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

                medical_reports.visit_id,

                visit_records.visit_date,
                visit_records.symptoms,
                visit_records.diagnosis,
                visit_records.prescription,
                visit_records.doctor_notes,
                visit_records.follow_up_date,

                doctor_user.full_name AS doctor_name

            FROM medical_reports

            INNER JOIN patients
                ON medical_reports.patient_id =
                   patients.patient_id

            INNER JOIN visit_records
                ON medical_reports.visit_id =
                   visit_records.visit_id

            INNER JOIN doctors
                ON medical_reports.doctor_id =
                   doctors.doctor_id

            INNER JOIN users AS doctor_user
                ON doctors.user_id =
                   doctor_user.user_id

            WHERE medical_reports.report_id = %s

            AND patients.user_id = %s

            LIMIT 1
            """,
            (
                report_id,
                current_user.id
            )
        )

        report = cursor.fetchone()

        if report is None:

            flash(
                "Report not found.",
                "warning"
            )

            return redirect(
                url_for("patient.medical_reports")
            )

        return render_template(
            "patient/view_report.html",
            report=report
        )

    except Exception as e:

        print(
            "VIEW REPORT ERROR:",
            repr(e)
        )

        flash(
            "Unable to open the report.",
            "danger"
        )

        return redirect(
            url_for("patient.medical_reports")
        )

    finally:

        cursor.close()
        connection.close()

@patient.route("/medical-report-file/<filename>")
@login_required
def medical_report_file(filename):

    if current_user.role != "patient":

        flash(
            "You do not have permission to access this file.",
            "danger"
        )

        return redirect(
            url_for("patient.medical_reports")
        )

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )        