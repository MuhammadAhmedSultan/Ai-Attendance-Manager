import os
import random  # Only this, do NOT do 'from random import random'
import secrets
import string
import threading
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os


from flask import (
    Flask, render_template, request, session, url_for, redirect,
    flash
)
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message


################################
# Flask App + Config
################################
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tahaansari2017'

# MongoDB connection
app.config["MONGO_URI"] = (
    "mongodb+srv://tahaansari2017:123@cluster1.ls8b7.mongodb.net/"
    "Student?retryWrites=true&w=majority&appName=Cluster1"
)
mongo = PyMongo(app)

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'attendancemanager37@gmail.com'
app.config['MAIL_PASSWORD'] = 'jbar arwf cxch goxl'
app.config['MAIL_DEFAULT_SENDER'] = 'attendancemanager37@gmail.com'
mail = Mail(app)

# File uploads
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Folder to store uploaded images
UPLOAD_FOLDER = "static/uploads/courses"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

################################
# Generate Enrollment ID
################################
def generate_enrollment_id():
    """Generate an 8-digit numeric Enrollment ID"""
    return ''.join(secrets.choice(string.digits) for _ in range(8))

################################
# Register Student
################################
@app.route("/register", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        # Save uploaded image
        image = request.files["image"]
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
        image.save(image_path)

        # Generate a random password (8 chars: letters + digits)
        alphabet = string.ascii_letters + string.digits
        plain_password = ''.join(secrets.choice(alphabet) for _ in range(8))

        # Generate unique enrollment ID
        enrollment_id = generate_enrollment_id()

        # Collect student details
        student = {
            "enrollment_id": enrollment_id,
            "full_name": request.form.get("full_name"),
            "father_name": request.form.get("father_name"),
            "mother_name": request.form.get("mother_name"),
            "date_of_birth": request.form.get("date_of_birth"),
            "gender": request.form.get("gender"),
            "nationality": request.form.get("nationality"),
            "religion": request.form.get("religion"),
            "address": request.form.get("address"),
            "contact_number": request.form.get("contact_number"),
            "email": request.form.get("email"),
            "b_form_number": request.form.get("b_form_number"),
            "previous_school": request.form.get("previous_school"),
            "class_applying_for": request.form.get("class_applying_for"),
            "emergency_contact": request.form.get("emergency_contact"),
            "medical_info": request.form.get("medical_info"),
            "languages_spoken": request.form.get("languages_spoken"),
            "image": image_filename,  # store filename
            "password": plain_password,  # store in plain text (⚠️ not secure)
            "created_at": datetime.datetime.utcnow(),
        }

        # Insert into MongoDB
        mongo.db.students.insert_one(student)

        # Send credentials email
        student_email = request.form.get("email")
        student_name = request.form.get("full_name")

        if student_email:
            subject = "Welcome to Our School - Your Login Credentials"
            body = f"""
Dear {student_name},

Welcome to our school! 🎉

Your account has been successfully created.

👉 Enrollment ID: {enrollment_id}
👉 Login Email: {student_email}
👉 Temporary Password: {plain_password}

Please log in and change your password as soon as possible for security.

Best regards,
School Administration
            """

            # Function for threaded email sending
            def send_async_email(app, msg):
                with app.app_context():
                    try:
                        mail.send(msg)
                    except Exception as e:
                        print("Email sending failed:", e)

            msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[student_email])
            msg.body = body

            threading.Thread(target=send_async_email, args=(app, msg)).start()

        # Notify admin with success message
        flash(f"Student registered successfully! Credentials sent to {student_email}", "success")
        return redirect(url_for("list_students"))

    return render_template("/student/register.html")


################################
# Students List Page
################################
@app.route("/students")
def list_students():
    students = list(mongo.db.students.find())
    return render_template("/student/students.html", students=students)

from bson.objectid import ObjectId

################################
# Edit Student
################################
@app.route("/students/edit/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    student = mongo.db.students.find_one({"_id": ObjectId(student_id)})

    if request.method == "POST":
        update_data = {
            "full_name": request.form.get("full_name"),
            "email": request.form.get("email"),
            "class_applying_for": request.form.get("class_applying_for"),
            "contact_number": request.form.get("contact_number"),
        }
        mongo.db.students.update_one({"_id": ObjectId(student_id)}, {"$set": update_data})
        flash("Student updated successfully!", "success")
        return redirect(url_for("list_students"))

    return render_template("/student/edit_student.html", student=student)

################################
# Send Email from Modal
################################
@app.route("/students/send_email/<student_id>", methods=["POST"])
def send_email_modal(student_id):
    student = mongo.db.students.find_one({"_id": ObjectId(student_id)})

    if not student:
        flash("Student not found ❌", "danger")
        return redirect(url_for("list_students"))

    # Get email from modal form
    email_to = request.form.get("email")
    if not email_to:
        flash("Email cannot be empty ❌", "danger")
        return redirect(url_for("list_students"))

    subject = "Your School Login Credentials"
    body = f"""
Dear {student['full_name']},

This is a reminder of your login credentials:

👉 Enrollment ID: {student['enrollment_id']}
👉 Login Email: {email_to}
👉 Password: {student['password']}

Please log in and change your password as soon as possible for security.

Best regards,
School Administration
    """

    # Send email in thread
    def send_async_email(app, msg):
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                print("Email sending failed:", e)

    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[email_to])
    msg.body = body
    threading.Thread(target=send_async_email, args=(app, msg)).start()

    flash(f"Credentials sent to {email_to} ✅", "success")
    return redirect(url_for("list_students"))

################################
# Delete Student
################################
@app.route("/students/delete/<student_id>")
def delete_student(student_id):
    mongo.db.students.delete_one({"_id": ObjectId(student_id)})
    flash("Student deleted successfully!", "danger")
    return redirect(url_for("list_students"))

################################
# Student Login
################################
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        enrollment_id = request.form.get("enrollment_id")
        password = request.form.get("password")

        # Find student by enrollment_id
        student = mongo.db.students.find_one({"enrollment_id": enrollment_id})

        if student and student["password"] == password:  # ⚠ plain password check
            # Save student info in session
            from flask import session
            session["student_id"] = str(student["_id"])
            session["student_name"] = student["full_name"]
            flash("Login successful! 🎉", "success")
            return redirect(url_for("student_panel"))
        else:
            flash("Invalid Enrollment ID or Password ❌", "danger")

    return render_template("/student/login.html")
@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("login"))

    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    return render_template("/student/student_dashboard.html", student=student)

# Courses Page
@app.route("/student/courses")
def student_courses():
    if "student_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    # Ensure 'courses' field exists
    if "courses" not in student:
        student["courses"] = []
    return render_template("/student/student_courses.html", student=student)


# Attendance Page
@app.route("/student/attendance")
def student_attendance():
    if "student_id" not in session:
        return redirect(url_for("login"))
    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    return render_template("/student/student_attendance.html", student=student)

# Messages Page
@app.route("/student/messages")
def student_messages():
    if "student_id" not in session:
        return redirect(url_for("login"))
    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    return render_template("/student/student_messages.html", student=student)

################################
# Student Panel
################################
@app.route("/student/panel")
def student_panel():
    from flask import session
    if "student_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    return render_template("/student/student_panel.html", student=student)
################################
# Student PRofile
################################
@app.route("/student/profile")
def student_profile():
    from flask import session
    if "student_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    student = mongo.db.students.find_one({"_id": ObjectId(session["student_id"])})
    return render_template("/student/student_profile.html", student=student)


################################
# Logout
################################
@app.route("/logout")
def logout():
    from flask import session
    session.clear()
    flash("Logged out successfully ✅", "info")
    return redirect(url_for("login"))




@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("admin_register"))

        # Check if email already exists
        existing_admin = mongo.db.admins.find_one({"email": email})
        if existing_admin:
            flash("Email already registered!", "danger")
            return redirect(url_for("admin_register"))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Save to database
        mongo.db.admins.insert_one({
            "email": email,
            "password": hashed_password
        })

        flash("Admin registered successfully!", "success")
        return redirect(url_for("admin_register"))

    return render_template("/admin/admin_register.html")


from flask import session

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if admin exists
        admin = mongo.db.admins.find_one({"email": email})
        if admin and check_password_hash(admin["password"], password):
            # Successful login
            session["admin_id"] = str(admin["_id"])
            session["admin_email"] = admin["email"]
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for("admin_login"))

    return render_template("/admin/admin_login.html")



@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    # Total registered faculty
    total_faculty = mongo.db.faculty.count_documents({})

    # Top 5 recently registered faculty
    top_faculty = list(mongo.db.faculty.find().sort("_id", -1).limit(5))

    return render_template(
        "/admin/admin_dashboard.html",
        email=session["admin_email"],
        total_faculty=total_faculty,
        top_faculty=top_faculty
    )



@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("/admin/admin_login"))

####################################
# Admin Courses Page
####################################
@app.route("/admin/courses")
def admin_courses():
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))
    
    courses = list(mongo.db.courses.find())
    return render_template("/admin/admin_courses.html", courses=courses)



####################################
# Add Course with Image Upload
####################################

@app.route("/admin/courses/add", methods=["GET", "POST"])
def add_course():
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        # Basic info
        title = request.form.get("title")
        subtitle = request.form.get("subtitle")
        description = request.form.get("description")

        # Course details
        duration = request.form.get("duration")
        level = request.form.get("level")
        language = request.form.get("language")
        enrolled_students = request.form.get("enrolled")
        certificate = request.form.get("certificate")

        # Curriculum (list of modules/lessons)
        curriculum = request.form.getlist("curriculum")

        # Handle image upload
        image_file = request.files.get("image_file")
        image_url = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            image_url = "/" + image_path.replace("\\", "/")  # Use for HTML src

        # Insert into MongoDB
        mongo.db.courses.insert_one({
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "duration": duration,
            "level": level,
            "language": language,
            "enrolled_students": enrolled_students,
            "certificate": certificate,
            "curriculum": curriculum,
            "image_url": image_url
        })

        flash("Course added successfully!", "success")
        return redirect(url_for("admin_courses"))

    return render_template("/admin/add_course.html")
####################################
# Delete Course
####################################
@app.route("/admin/courses/delete/<course_id>")
def delete_course(course_id):
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    mongo.db.courses.delete_one({"_id": ObjectId(course_id)})
    flash("Course deleted successfully!", "success")
    return redirect(url_for("admin_courses"))


@app.route("/admin/courses/edit/<course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    course = mongo.db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        flash("Course not found!", "danger")
        return redirect(url_for("admin_courses"))

    if request.method == "POST":
        # Basic info
        title = request.form.get("title")
        subtitle = request.form.get("subtitle")
        description = request.form.get("description")

        # Course details
        duration = request.form.get("duration")
        level = request.form.get("level")
        language = request.form.get("language")
        enrolled_students = request.form.get("enrolled")
        certificate = request.form.get("certificate")
        curriculum = request.form.getlist("curriculum")

        # Handle image upload
        image_file = request.files.get("image_file")
        image_url = course.get("image_url")  # Keep old image if no new file uploaded
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            image_url = "/" + image_path.replace("\\", "/")

        # Update MongoDB
        mongo.db.courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": {
                "title": title,
                "subtitle": subtitle,
                "description": description,
                "duration": duration,
                "level": level,
                "language": language,
                "enrolled_students": enrolled_students,
                "certificate": certificate,
                "curriculum": curriculum,
                "image_url": image_url
            }}
        )

        flash("Course updated successfully!", "success")
        return redirect(url_for("admin_courses"))

    return render_template("/admin/edit_course.html", course=course)

@app.route("/admin/courses/view/<course_id>")
def view_course(course_id):
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    course = mongo.db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        flash("Course not found!", "danger")
        return redirect(url_for("admin_courses"))

    return render_template("/admin/view_course.html", course=course)



@app.route("/admin/students")
def admin_students():
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))
    
    students = list(mongo.db.students.find())
    return render_template("/admin/manage_student.html", students=students)

@app.route("/admin/faculty")
def admin_faculty():
    faculty_list = list(mongo.db.faculty.find())
    return render_template("/admin/admin_faculty.html", admin_faculty=faculty_list)

@app.route("/admin/faculty/assign_course/<faculty_id>", methods=["GET", "POST"])
def assign_course(faculty_id):
    if "admin_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("admin_login"))

    # Fetch faculty data
    faculty = mongo.db.faculty.find_one({"_id": ObjectId(faculty_id)})
    if not faculty:
        flash("Faculty not found!", "danger")
        return redirect(url_for("admin_faculty_list"))

    # Fetch all courses
    courses = list(mongo.db.courses.find())

    if request.method == "POST":
        # Get selected courses from form
        selected_courses = request.form.getlist("courses")  # This returns a list of course titles or IDs

        # Update faculty document with selected courses
        mongo.db.faculty.update_one(
            {"_id": ObjectId(faculty_id)},
            {"$set": {"courses": selected_courses}}
        )

        flash(f"Courses assigned successfully to {faculty['first_name']} {faculty['last_name']}", "success")
        return redirect(url_for("admin_faculty_list"))

    return render_template("/admin/course_assign.html", faculty=faculty, courses=courses)

@app.route("/faculty/assign_courses")
def assign_courses():
   
    return render_template("/admin/course_assign.html")

# UPDATE: Edit faculty
@app.route("/faculty/edit/<id>", methods=["GET", "POST"])
def edit_faculty(id):
    faculty = mongo.db.faculty.find_one({"_id": ObjectId(id)})
    if not faculty:
        flash("Faculty not found!", "danger")
        return redirect(url_for("admin_faculty"))

    if request.method == "POST":
        update_data = {
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "dob": request.form.get("dob"),
            "gender": request.form.get("gender"),
            "contact": request.form.get("contact"),
            "email": request.form.get("email"),
            "address": request.form.get("address"),
            "department": request.form.get("department"),
            "designation": request.form.get("designation"),
            "qualification": request.form.get("qualification"),
            "specialization": request.form.get("specialization"),
            "experience": request.form.get("experience"),
            "courses": request.form.get("courses")
        }

        # Update profile picture if new file uploaded
        file = request.files.get("profile_pic")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            update_data["profile_pic"] = filename

        mongo.db.faculty.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        flash("Faculty updated successfully!", "success")
        return redirect(url_for("admin_faculty"))

    return render_template("/admin/edit_faculty.html", faculty=faculty)

# DELETE: Remove faculty
@app.route("/faculty/delete/<id>", methods=["POST"])
def delete_faculty(id):
    mongo.db.faculty.delete_one({"_id": ObjectId(id)})
    flash("Faculty deleted successfully!", "success")
    return redirect(url_for("admin_faculty"))

# Auto-generate Faculty ID
def generate_faculty_id():
    last_faculty = mongo.db.faculty.find_one(sort=[("faculty_id", -1)])
    if last_faculty and last_faculty.get("faculty_id"):
        last_id = int(last_faculty["faculty_id"][3:])  # remove 'FAC' prefix
        return "FAC" + str(last_id + 1)
    else:
        return "FAC1000"

def generate_username(first_name, last_name):
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(10,99)}"


@app.route("/faculty/register", methods=["GET", "POST"])
def faculty_register():
    if request.method == "POST":
        # Personal Information
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        dob = request.form.get("dob")
        gender = request.form.get("gender")
        contact = request.form.get("contact")
        email = request.form.get("email")
        address = request.form.get("address")

        # Auto-generate Faculty ID and Username
        faculty_id = generate_faculty_id()
        username = generate_username(first_name, last_name)

        # Professional / Academic
        department = request.form.get("department")
        designation = request.form.get("designation")
        qualification = request.form.get("qualification")
        specialization = request.form.get("specialization")
        experience = request.form.get("experience")
        courses = request.form.get("courses")

        # Login / Account
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        # Profile picture
        file = request.files.get("profile_pic")
        profile_pic = ""
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            profile_pic = filename

        # Save to MongoDB
        mongo.db.faculty.insert_one({
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "contact": contact,
            "email": email,
            "address": address,
            "faculty_id": faculty_id,
            "department": department,
            "designation": designation,
            "qualification": qualification,
            "specialization": specialization,
            "experience": experience,
            "courses": courses,
            "username": username,
            "password": password,  # In production, hash passwords!
            "profile_pic": profile_pic
        })

        flash(f"Faculty registered successfully! Faculty ID: {faculty_id}, Username: {username}", "success")
        return redirect(url_for("faculty_register"))

    return render_template("/teacher/register.html")

@app.route("/faculty/login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check in MongoDB
        faculty = mongo.db.faculty.find_one({"username": username})

        if faculty and faculty["password"] == password:  # In production, use hashed password check!
            # Set session
            session["faculty_id"] = faculty["faculty_id"]
            session["faculty_name"] = faculty["first_name"] + " " + faculty["last_name"]
            flash(f"Welcome {faculty['first_name']}!", "success")
            return redirect(url_for("faculty_dashboard"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("faculty_login"))

    return render_template("/teacher/login.html")

@app.route("/faculty/dashboard")
def faculty_dashboard():
    if "faculty_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("faculty_login"))
    return render_template("/teacher/dashboard.html", faculty_name=session["faculty_name"])

@app.route("/faculty/logout")
def faculty_logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("faculty_login"))

################################
# Run App
################################

if __name__ == "__main__":
    app.run(debug=True)
