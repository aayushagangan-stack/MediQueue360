document.addEventListener(
    "DOMContentLoaded",
    function () {

        const alerts = document.querySelectorAll(
            ".alert"
        );


        alerts.forEach(
            function (alert) {

                setTimeout(
                    function () {

                        const closeButton =
                            alert.querySelector(
                                ".btn-close"
                            );

                        if (closeButton) {
                            closeButton.click();
                        }

                    },
                    5000
                );

            }
        );


        const passwordFields =
            document.querySelectorAll(
                'input[type="password"]'
            );


        passwordFields.forEach(
            function (field) {

                field.addEventListener(
                    "input",
                    function () {

                        if (field.value.length >= 6) {

                            field.classList.remove(
                                "is-invalid"
                            );

                        }

                    }
                );

            }
        );


        const appointmentDate =
            document.querySelector(
                "#appointment_date"
            );


        if (appointmentDate) {

            const today =
                new Date().toISOString().split(
                    "T"
                )[0];

            appointmentDate.setAttribute(
                "min",
                today
            );

        }

    }
);

document.addEventListener("DOMContentLoaded", function () {

    const navLinks = document.querySelectorAll("#mainNavLinks .nav-link");

    navLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            navLinks.forEach(function (item) {

                item.classList.remove("active");

            });

            this.classList.add("active");

        });

    });

});

const roleSelect = document.getElementById("role");

if (roleSelect) {

const doctorFields = document.getElementById("doctorFields");
const receptionistFields = document.getElementById("receptionistFields");
const patientFields = document.getElementById("patientFields");


function updateRoleFields() {

    if (doctorFields) {
        doctorFields.style.display = "none";
    }

    if (receptionistFields) {
        receptionistFields.style.display = "none";
    }

    if (patientFields) {
        patientFields.style.display = "none";
    }


    if (roleSelect.value === "doctor" && doctorFields) {
        doctorFields.style.display = "block";
    }


    if (roleSelect.value === "receptionist" && receptionistFields) {
        receptionistFields.style.display = "block";
    }


    if (roleSelect.value === "patient" && patientFields) {
        patientFields.style.display = "block";
    }
}

roleSelect.addEventListener("change", updateRoleFields);

updateRoleFields();

}

// Filter the doctor list according to the selected department
const departmentSelect = document.getElementById("department_id");
const doctorSelect = document.getElementById("doctor_id");

if (departmentSelect && doctorSelect) {

    const allDoctors = Array.from(
        doctorSelect.options
    ).slice(1);

    departmentSelect.addEventListener("change", function () {

        const selectedDepartment = this.value;

        doctorSelect.innerHTML = `
            <option value="">
                Select a doctor
            </option>
        `;

        allDoctors.forEach(function (doctor) {

            if (
                doctor.dataset.department === selectedDepartment
            ) {

                doctorSelect.appendChild(
                    doctor
                );

            }

        });

    });

}