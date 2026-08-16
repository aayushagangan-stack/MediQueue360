from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db_connection
from flask import send_from_directory
from flask_bcrypt import Bcrypt

admin = Blueprint("admin", __name__, url_prefix="/admin")

bcrypt = Bcrypt()

@admin.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "admin":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for("home"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("SELECT COUNT(*) AS total FROM receptionists")
        total_receptionists = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM doctors")
        total_doctors = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        total_patients = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM departments")
        total_departments = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT
                a.appointment_date,
                a.appointment_time,
                a.status,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name

            FROM appointments a

            JOIN patients p
                ON a.patient_id = p.patient_id

            JOIN users patient_user
                ON p.user_id = patient_user.user_id

            JOIN doctors d
                ON a.doctor_id = d.doctor_id

            JOIN users doctor_user
                ON d.user_id = doctor_user.user_id

            ORDER BY
                a.appointment_date DESC,
                a.appointment_time DESC

            LIMIT 5
        """)

        recent_appointments = cursor.fetchall()

        return render_template(
            "admin/dashboard.html",

            total_receptionists=total_receptionists,
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_departments=total_departments,

            recent_appointments=recent_appointments
        )

    finally:
        cursor.close()
        connection.close()


@admin.route("/users")
@login_required
def users():

    if current_user.role != "admin":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return redirect(url_for("home"))


    search = request.args.get("search", "").strip()
    role = request.args.get("role", "").strip()
    status = request.args.get("status", "").strip()


    connection = get_db_connection()

    if connection is None:

        flash(
            "Unable to connect to the database.",
            "danger"
        )

        return redirect(url_for("admin.dashboard"))


    cursor = connection.cursor(dictionary=True)


    try:

        query = """
            SELECT
                user_id,
                full_name,
                email,
                phone,
                role,
                status,
                created_at
            FROM users
            WHERE 1=1
        """

        params = []


        if search:

            query += """
                AND (
                    full_name LIKE %s
                    OR email LIKE %s
                    OR phone LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        if role:

            query += """
                AND role = %s
            """

            params.append(role)


        if status:

            query += """
                AND status = %s
            """

            params.append(status)


        query += """
            ORDER BY created_at DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        users_data = cursor.fetchall()


        return render_template(
            "admin/users.html",
            users=users_data,
            search=search,
            selected_role=role,
            selected_status=status
        )


    finally:

        cursor.close()
        connection.close()

@admin.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    if current_user.role != "admin":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "danger")
        return redirect(url_for("admin.users"))

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()
        status = request.form.get("status", "active").strip()
        department_id = request.form.get("department_id", "").strip()
        qualification = request.form.get("qualification", "").strip()
        experience_years = request.form.get("experience_years", "0").strip()
        consultation_fee = request.form.get("consultation_fee", "0").strip()
        about = request.form.get("about", "").strip()
        employee_id = request.form.get("employee_id", "").strip()

        if not full_name or not email or not password or not role:
            cursor.close()
            connection.close()
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for("admin.add_user"))

        if len(password) < 6:
            cursor.close()
            connection.close()
            flash("Password must contain at least 6 characters.", "warning")
            return redirect(url_for("admin.add_user"))

        if role not in ["patient", "doctor", "receptionist"]:
            cursor.close()
            connection.close()
            flash("Invalid user role selected.", "warning")
            return redirect(url_for("admin.add_user"))

        if role == "doctor":
            if not department_id or not qualification:
                cursor.close()
                connection.close()
                flash("Please select a department and enter the doctor's qualification.", "warning")
                return redirect(url_for("admin.add_user"))

            try:
                department_id = int(department_id)
                experience_years = int(experience_years or 0)
                consultation_fee = float(consultation_fee or 0)
            except ValueError:
                cursor.close()
                connection.close()
                flash("Please enter valid doctor professional details.", "warning")
                return redirect(url_for("admin.add_user"))

            if experience_years < 0 or consultation_fee < 0:
                cursor.close()
                connection.close()
                flash("Experience and consultation fee cannot be negative.", "warning")
                return redirect(url_for("admin.add_user"))

        if role == "receptionist" and not employee_id:
            cursor.close()
            connection.close()
            flash("Please enter the receptionist employee ID.", "warning")
            return redirect(url_for("admin.add_user"))

        try:
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s LIMIT 1",
                (email,)
            )

            if cursor.fetchone():
                flash("An account with this email already exists.", "warning")
                return redirect(url_for("admin.add_user"))

            if role == "doctor":
                cursor.execute(
                    """
                    SELECT department_id
                    FROM departments
                    WHERE department_id = %s AND status = 'active'
                    LIMIT 1
                    """,
                    (department_id,)
                )

                if cursor.fetchone() is None:
                    flash("The selected department is not available.", "warning")
                    return redirect(url_for("admin.add_user"))

            if role == "receptionist":
                cursor.execute(
                    "SELECT receptionist_id FROM receptionists WHERE employee_id = %s LIMIT 1",
                    (employee_id,)
                )

                if cursor.fetchone():
                    flash("This employee ID is already in use.", "warning")
                    return redirect(url_for("admin.add_user"))

            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

            cursor.execute(
                """
                INSERT INTO users
                (full_name, email, password, phone, role, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (full_name, email, hashed_password, phone, role, status)
            )

            user_id = cursor.lastrowid

            if role == "patient":

                date_of_birth = request.form.get("date_of_birth") or None
                gender = request.form.get("gender") or None
                address = request.form.get("address") or None
                emergency_contact = request.form.get("emergency_contact") or None

                cursor.execute(
                    """
                    INSERT INTO patients
                    (
                        user_id,
                        date_of_birth,
                        gender,
                        address,
                        emergency_contact
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        date_of_birth,
                        gender,
                        address,
                        emergency_contact
                    )
                )
                
            elif role == "doctor":
                cursor.execute(
                    """
                    INSERT INTO doctors
                    (user_id, department_id, qualification, experience_years, consultation_fee, about)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        department_id,
                        qualification,
                        experience_years,
                        consultation_fee,
                        about
                    )
                )

            elif role == "receptionist":
                cursor.execute(
                    """
                    INSERT INTO receptionists (user_id, employee_id)
                    VALUES (%s, %s)
                    """,
                    (user_id, employee_id)
                )

            connection.commit()
            flash("User created successfully.", "success")
            return redirect(url_for("admin.users"))

        except Exception as e:
            connection.rollback()
            print("ADD USER ERROR:", e)
            flash("Unable to create user. Please check the details and try again.", "danger")
            return redirect(url_for("admin.add_user"))

        finally:
            cursor.close()
            connection.close()

    try:
        cursor.execute(
            """
            SELECT department_id, department_name
            FROM departments
            WHERE status = 'active'
            ORDER BY department_name ASC
            """
        )

        departments = cursor.fetchall()
        return render_template("admin/add_user.html", departments=departments)

    except Exception as e:
        print("LOAD DEPARTMENTS ERROR:", e)
        flash("Unable to load departments.", "danger")
        return redirect(url_for("admin.users"))

    finally:
        cursor.close()
        connection.close()
    
@admin.route("/users/<int:user_id>")
@login_required
def manage_user(user_id):

    if current_user.role != "admin":

        flash("You do not have permission to access this page.", "danger")

        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:

        flash("Unable to connect to the database.", "danger")

        return redirect(url_for("admin.users"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
    """
    SELECT
        u.user_id,
        u.full_name,
        u.email,
        u.phone,
        u.role,
        u.status,
        u.created_at,

        p.date_of_birth,
        p.gender,
        p.address,
        p.emergency_contact,

        d.department_id,
        dep.department_name,
        d.qualification,
        d.experience_years,
        d.consultation_fee,
        d.about,

        r.employee_id

    FROM users u

    LEFT JOIN patients p
        ON u.user_id = p.user_id

    LEFT JOIN doctors d
        ON u.user_id = d.user_id

    LEFT JOIN departments dep
        ON d.department_id = dep.department_id

    LEFT JOIN receptionists r
        ON u.user_id = r.user_id

    WHERE u.user_id = %s

    LIMIT 1
    """,
    (user_id,),
)

        user = cursor.fetchone()

        if user is None:

            flash("User not found.", "warning")

            return redirect(url_for("admin.users"))

        return render_template("admin/manage_user.html", user=user)

    finally:

        cursor.close()
        connection.close()

@admin.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):

    if current_user.role != "admin":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "danger")
        return redirect(url_for("admin.users"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.phone,
                u.role,
                u.status,
                d.department_id,
                d.qualification,
                d.experience_years,
                d.consultation_fee,
                d.about,
                r.employee_id,
                p.date_of_birth,
                p.gender,
                p.address,
                p.emergency_contact
            FROM users u
            LEFT JOIN doctors d ON u.user_id=d.user_id
            LEFT JOIN patients p ON u.user_id=p.user_id
            LEFT JOIN receptionists r ON u.user_id=r.user_id
            WHERE u.user_id=%s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        if user is None:
            flash("User not found.", "warning")
            return redirect(url_for("admin.users"))

        cursor.execute("""
            SELECT department_id, department_name
            FROM departments
            WHERE status='active'
            ORDER BY department_name
        """)

        departments = cursor.fetchall()

        if request.method == "POST":

            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            role = request.form.get("role")
            status = request.form.get("status")

            department_id = request.form.get("department_id")
            qualification = request.form.get("qualification", "").strip()
            experience_years = request.form.get("experience_years")
            consultation_fee = request.form.get("consultation_fee")
            about = request.form.get("about", "").strip()

            employee_id = request.form.get("employee_id", "").strip()

            date_of_birth = request.form.get("date_of_birth") or None
            gender = request.form.get("gender") or None
            address = request.form.get("address", "").strip()
            emergency_contact = request.form.get("emergency_contact", "").strip()

            if not full_name or not email:
                flash("Name and email are required.", "warning")
                return redirect(url_for("admin.edit_user", user_id=user_id))
            cursor.execute("""
                UPDATE users
                SET
                    full_name=%s,
                    email=%s,
                    phone=%s,
                    role=%s,
                    status=%s
                WHERE user_id=%s
            """, (
                full_name,
                email,
                phone,
                role,
                status,
                user_id
            ))

            if role == "doctor":

                cursor.execute("""
                    UPDATE doctors
                    SET
                        department_id=%s,
                        qualification=%s,
                        experience_years=%s,
                        consultation_fee=%s,
                        about=%s
                    WHERE user_id=%s
                """, (
                    department_id,
                    qualification,
                    experience_years,
                    consultation_fee,
                    about,
                    user_id
                ))

            elif role == "patient":

                cursor.execute("""
                    UPDATE patients
                    SET
                        date_of_birth=%s,
                        gender=%s,
                        address=%s,
                        emergency_contact=%s
                    WHERE user_id=%s
                """, (
                    date_of_birth,
                    gender,
                    address,
                    emergency_contact,
                    user_id
                ))

            elif role == "receptionist":

                cursor.execute("""
                    UPDATE receptionists
                    SET
                        employee_id=%s
                    WHERE user_id=%s
                """, (
                    employee_id,
                    user_id
                ))

            connection.commit()

            flash("User updated successfully.", "success")

            return redirect(url_for("admin.manage_user", user_id=user_id))
        return render_template(
            "admin/edit_user.html",
            user=user,
            departments=departments
        )

    except Exception as e:

        connection.rollback()

        print("EDIT USER ERROR:", e)

        flash("Unable to update user details.", "danger")

        return redirect(
            url_for("admin.manage_user", user_id=user_id)
        )

    finally:

        cursor.close()

        connection.close()


@admin.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):

    if current_user.role != "admin":

        flash("You do not have permission to perform this action.", "danger")

        return redirect(url_for("home"))

    if user_id == current_user.id:

        flash("You cannot delete your own admin account.", "warning")

        return redirect(url_for("admin.manage_user", user_id=user_id))

    connection = get_db_connection()

    if connection is None:

        flash("Unable to connect to the database.", "danger")

        return redirect(url_for("admin.users"))

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )

        if cursor.rowcount == 0:

            flash("User not found.", "warning")

        else:

            connection.commit()

            flash("User deleted successfully.", "success")

        return redirect(url_for("admin.users"))

    except Exception:

        connection.rollback()

        flash(
            "Unable to delete the user. This user may have related records.", "danger"
        )

        return redirect(url_for("admin.manage_user", user_id=user_id))

    finally:

        cursor.close()
        connection.close()


@admin.route("/departments", methods=["GET", "POST"])
@login_required
def departments():

    if current_user.role != "admin":

        flash("You do not have permission to access this page.", "danger")

        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:

        flash("Unable to connect to the database.", "danger")

        return redirect(url_for("admin.dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:

        if request.method == "POST":

            department_name = request.form.get("department_name", "").strip()

            description = request.form.get("description", "").strip()

            if not department_name:

                flash("Department name is required.", "warning")

                return redirect(url_for("admin.departments"))

            cursor.execute(
                """
                SELECT department_id
                FROM departments
                WHERE department_name = %s
                LIMIT 1
                """,
                (department_name,),
            )

            existing_department = cursor.fetchone()

            if existing_department:

                flash("This department already exists.", "warning")

                return redirect(url_for("admin.departments"))

            cursor.execute(
                """
                INSERT INTO departments
                (
                    department_name,
                    description
                )
                VALUES
                (
                    %s,
                    %s
                )
                """,
                (department_name, description),
            )

            connection.commit()

            flash("Department added successfully.", "success")

            return redirect(url_for("admin.departments"))

        cursor.execute("""
            SELECT
                department_id,
                department_name,
                description,
                status,
                created_at
            FROM departments
            ORDER BY department_name ASC
            """)

        departments_data = cursor.fetchall()

        return render_template("admin/departments.html", departments=departments_data)

    except Exception as e:

        connection.rollback()

        print("DEPARTMENT ERROR:", e)

        flash("Unable to process the department request.", "danger")

        return redirect(url_for("admin.departments"))

    finally:

        cursor.close()
        connection.close()


@admin.route("/departments/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
def edit_department(department_id):

    if current_user.role != "admin":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "danger")
        return redirect(url_for("admin.departments"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                department_id,
                department_name,
                description
            FROM departments
            WHERE department_id = %s
            LIMIT 1
            """,
            (department_id,),
        )

        department = cursor.fetchone()

        if department is None:
            flash("Department not found.", "warning")
            return redirect(url_for("admin.departments"))

        if request.method == "POST":

            department_name = request.form.get("department_name", "").strip()

            description = request.form.get("description", "").strip()

            if not department_name:
                flash("Department name is required.", "warning")
                return redirect(
                    url_for("admin.edit_department", department_id=department_id)
                )

            cursor.execute(
                """
                UPDATE departments
                SET
                    department_name = %s,
                    description = %s
                WHERE department_id = %s
                """,
                (department_name, description, department_id),
            )

            connection.commit()

            flash("Department updated successfully.", "success")

            return redirect(url_for("admin.departments"))

        return render_template("admin/edit_department.html", department=department)

    except Exception as e:

        connection.rollback()

        print("EDIT DEPARTMENT ERROR:", e)

        return f"Edit Department Error: {e}", 500

    finally:

        cursor.close()
        connection.close()


@admin.route("/departments/<int:department_id>/delete", methods=["POST"])
@login_required
def delete_department(department_id):

    if current_user.role != "admin":

        flash("You do not have permission to access this page.", "danger")

        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:

        flash("Unable to connect to the database.", "danger")

        return redirect(url_for("admin.departments"))

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM departments
            WHERE department_id = %s
            """,
            (department_id,),
        )

        connection.commit()

        flash("Department deleted successfully.", "success")

        return redirect(url_for("admin.departments"))

    except Exception as e:

        connection.rollback()

        print("DELETE DEPARTMENT ERROR:", e)

        flash("Unable to delete department.", "danger")

        return redirect(url_for("admin.departments"))

    finally:

        cursor.close()
        connection.close()

@admin.route("/appointments")
@login_required
def manage_appointments():

    if current_user.role != "admin":
        flash(
            "You do not have permission to access this page.",
            "danger"
        )
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash(
            "Database connection failed.",
            "danger"
        )
        return redirect(url_for("admin.dashboard"))

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

            JOIN departments
                ON doctors.department_id = departments.department_id    

            ORDER BY
                appointments.appointment_date DESC

        """)

        appointments = cursor.fetchall()

        return render_template(
            "admin/manage_appointments.html",
            appointments=appointments
        )

    except Exception as e:

        print("MANAGE APPOINTMENTS ERROR:", e)

        flash(
            "Unable to load appointments.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )

    finally:

        cursor.close()
        connection.close()

@admin.route("/reports")
@login_required
def view_reports():

    if current_user.role != "admin":
        flash(
            "You do not have permission to access this page.",
            "danger"
        )
        return redirect(url_for("home"))

    connection = get_db_connection()

    if connection is None:
        flash(
            "Unable to connect to the database.",
            "danger"
        )
        return redirect(url_for("admin.dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                medical_reports.report_id,

                patient_user.full_name AS patient_name,

                doctor_user.full_name AS doctor_name,

                appointments.appointment_date,

                appointments.status AS visit_status,

                medical_reports.file_path

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

            LEFT JOIN visit_records
                ON medical_reports.visit_id =
                   visit_records.visit_id

            LEFT JOIN appointments
                ON visit_records.appointment_id =
                   appointments.appointment_id

            ORDER BY
                medical_reports.report_date DESC
        """)

        reports = cursor.fetchall()

        return render_template(
            "admin/view_reports.html",
            reports=reports
        )

    except Exception as e:

        print("VIEW REPORTS ERROR:", repr(e))

        flash(
            "Unable to load reports.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )

    finally:

        cursor.close()
        connection.close()

@admin.route("/reports/file/<path:filename>")
@login_required
def view_report_file(filename):

    if current_user.role != "admin":
        flash(
            "You do not have permission to access this file.",
            "danger"
        )
        return redirect(url_for("home"))

    return send_from_directory(
        "uploads",
        filename
    )        