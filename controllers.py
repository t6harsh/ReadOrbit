from flask import Flask, render_template, redirect, request, url_for, flash , jsonify
from flask import current_app as app
from sqlalchemy import join
from models import *
from datetime import datetime, timedelta
#from apscheduler.schedulers.background import BackgroundScheduler

# scheduler = BackgroundScheduler()
# scheduler.start()

logged_admin = False 

logged_user = False

@app.route("/")
def home():
    return render_template("/index.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    global logged_admin
    if not logged_admin:
        if request.method == "POST":
            admin_email = request.form.get("admin_email")

            admin_password = request.form.get("admin_password")
            admin = Admin.query.filter(Admin.admin_email == admin_email).first()
            if admin:
                if admin.admin_password == admin_password:
                    logged_admin = admin_email
                    return redirect(url_for("admin_dashboard"))
                

                error = "Password Missmatched"
                return render_template("/admin_login.html", error=error)
            error = "Wrong email"
        return render_template("/admin_login.html", error=error)
    return redirect(url_for("admin_dashboard"))



@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    error = None




    global logged_user
    if request.method == "POST":
        user_email = request.form.get("user_email")
        user_password = request.form.get("user_password")
        user = User.query.filter(User.user_email == user_email).first()
        if user:
            if user_password == user.user_password:
                logged_user = user_email
                return redirect(url_for("user_dashboard"))
            

            error = "Password Missmatched"

            return render_template("/user_login.html", error=error)
        error = "Wrong email"
        return render_template("/user_register.html", error=error)
    return render_template("/user_login.html", error=error)

@app.route("/user_register", methods=["GET", "POST"])

def user_register():
    if request.method == "POST":
        user_email = request.form.get("user_email")
        user = User.query.filter(User.user_email == user_email).first()


        if user:
            return render_template("/user_register.html", error="User eamil already exist....")
        user_password = request.form.get("user_password")
        user_name = request.form.get("user_name")


        user = User(user_email=user_email, user_name=user_name, user_password=user_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("user_login"))
    
    return render_template("/user_register.html")

MAX_BOOK_REQUESTS = 5

@app.route("/user_dashboard", methods=["GET"])
def user_dashboard():
    global logged_user

    if not logged_user:
        return redirect(url_for("user_login"))
    user_email = logged_user
    user = User.query.filter_by(user_email=user_email).first()
    feedback = Feedback.query.get(user_email)

    if user:
        sections = Section.query.all()
        for section in sections:
            section.books = section.section_books
        user_requests = Request_book.query.filter_by(user_email=user_email).filter(Request_book.status.in_(['pending', 'accepted'])).all()
        requested_book_ids = [request.book_id for request in user_requests]


        user_requests_count = Request_book.query.filter_by(user_email=user_email).filter(Request_book.status.in_(['pending', 'accepted'])).count()

        completed_books = Request_book.query.filter_by(user_email=user_email).filter(Request_book.status.in_(['returned', 'revoked'])).all()
        feedback_given = {feedback.book_id: True for feedback in Feedback.query.filter_by(user_email=user_email)}
        for section in sections:
            section.books = [book for book in section.books if book.book_id not in requested_book_ids]
        return render_template("user_dashboard.html", sections=sections, feedback_given=feedback_given, feedback=feedback, user_requests=user_requests, completed_books=completed_books, Book=Book, MAX_BOOK_REQUESTS=MAX_BOOK_REQUESTS, user_requests_count=user_requests_count, user=user)
    else:

        flash("User not found")
        return redirect(url_for("user_login"))

def has_been_requested(book, user_email):
    for request in book.book_requests:
        if request.user_email == user_email:
            return True
        
    return False

@app.route("/book_request", methods=["POST"])
def book_request():
    global logged_user
    if logged_user:

        if request.method == "POST":
        
            user_email = logged_user
            user_requests_count = Request_book.query.filter_by(user_email=user_email).filter(Request_book.status.in_(['pending', 'accepted'])).count()
        
            if user_requests_count >= MAX_BOOK_REQUESTS:
                flash("You have reached the maximum limit of book requests.")
                return redirect(url_for("user_dashboard"))
        
            book_id = request.form.get('book_id')
            section_id = request.form.get('section_id')
            days_required = int(request.form.get('days_required'))
        
        
            new_request = Request_book(book_id=book_id, section_id=section_id, user_email=user_email, request=1, days_required=days_required)
            db.session.add(new_request)
            db.session.commit()
        
            return redirect(url_for("user_dashboard"))
    return redirect(url_for("user_login"))

@app.route("/cancel_request/<int:request_id>", methods=["POST"])
def cancel_request(request_id):
    global logged_user
    if logged_user:
        
        request_book = Request_book.query.get(request_id)
        if request_book and request_book.user_email == logged_user:
        
            db.session.delete(request_book)
        
            db.session.commit()
            return redirect(url_for("user_dashboard"))
    return redirect(url_for("user_login"))

@app.route("/return_book/<int:request_id>", methods=["POST"])
def return_book(request_id):
    global logged_user
    if logged_user:
        
        request_book = Request_book.query.get(request_id)
        if request_book and request_book.user_email == logged_user and request_book.status == 'accepted':
            request_book.status = 'returned'
        
            db.session.commit()
            user = User.query.filter_by(user_email=logged_user).first()
            if user:
                user.user_books_count -= 1
        
                db.session.commit()
            return redirect(url_for("user_dashboard"))
    return redirect(url_for("user_login"))

@app.route("/section_create", methods=["GET", "POST"])
def section_create():
    global logged_admin
    if logged_admin:
        if request.method == "POST":
            section_name = request.form.get("section_name")
        
            section = Section.query.filter(Section.section_name == section_name).first()
        
            section_date_created = request.form.get("section_date_created")
            section_description = request.form.get("section_description")
        
            section_max_books = request.form.get("section_max_books")
            section = Section(section_name=section_name, section_date_created=section_date_created, section_description=section_description, section_max_books=section_max_books)
        
            db.session.add(section)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        return render_template("/section_create.html")
    return redirect(url_for("admin_login"))

@app.route("/admin_dashboard")
def admin_dashboard():
    global logged_admin
    if logged_admin:
        sections = Section.query.all()
        
        pending_requests = Request_book.query.filter_by(status='pending').all()
        return render_template("admin_dashboard.html", sections=sections, pending_requests=pending_requests)
    return redirect(url_for("admin_login"))


@app.route("/section_delete", methods=["GET", "POST"])
def section_delete():
    global logged_admin
    if logged_admin:

        if request.method == "POST":
            section_id = int(request.form.get("section_id"))
            section = Section.query.filter(Section.section_id == section_id).first()

            db.session.delete(section)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        sections = Section.query.all()

        return render_template("section_delete.html", sections=sections)
    return redirect(url_for("admin_login"))

@app.route("/book_create", methods=["GET", "POST"])
def book_create():
    global logged_admin

    if logged_admin:
        if request.method == "POST":
            book_name = request.form.get("book_name")
            book_content = request.form.get("book_content")

            book_author_name = request.form.get("book_author_name")
            section_ids = request.form.getlist("section_ids")
            book = Book(book_name=book_name, book_content=book_content, book_author_name=book_author_name)
            for id in section_ids:

                section = Section.query.get(id)
                if section:
                    section.section_no_of_books_added += 1
                    book.book_sections.append(section)

            db.session.add(book)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        sections_from_db = Section.query.all()
        sections = [section for section in sections_from_db if section.section_no_of_books_added < section.section_max_books]

        return render_template("book_create.html", sections=sections)
    return redirect(url_for("admin_login"))

@app.route("/book_edit", methods=["GET", "POST"])
def book_edit():
    global logged_admin
    if logged_admin:
        if request.method == "POST":
            book_id = request.form.get("book_id")
            book = Book.query.get(book_id)
            book_name = request.form.get("book_name")
            book_content = request.form.get("book_content")
            book_author_name = request.form.get("book_author_name")

            section_ids = request.form.getlist("section_ids")
            held_sections = []
            for id in section_ids:

                section = Section.query.get(id)
                held_sections.append(section)
            for section in book.book_sections:
                if section not in held_sections:
                    section.section_no_of_books_added -= 1
                    book.book_sections.remove(section)
            new_section_ids = request.form.getlist("new_sections")
            new_sections = []
            for i in new_section_ids:

                new_sections.append(Section.query.get(i))
            for i in new_sections:
                book.book_sections.append(i)
                i.section_no_of_books_added += 1
            book.book_name = book_name
            book.book_content = book_content
            book.book_author_name = book_author_name
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        books = Book.query.all()

        sections = Section.query.all()
        sections_available = []
        for section in sections:
            if section.section_max_books > section.section_no_of_books_added:
                sections_available.append(section)
                db.session.commit()
        return render_template("book_edit.html", books=books, sections_available=sections_available)
    return redirect(url_for("admin_login"))

@app.route("/section_edit", methods=["GET", "POST"])
def section_edit():
    global logged_admin
    if logged_admin:
        if request.method == "POST":
            section_id = request.form.get("section_id")
            section_name = request.form.get("section_name")
            section_date_created = request.form.get("section_date_created")
            section_description = request.form.get("section_description")

            section_max_books = request.form.get("section_max_books")
            section = Section.query.get(section_id)
            if int(section_max_books) < section.section_no_of_books_added:
                error = "Max books added"

                sections = Section.query.all()

                return render_template("section_edit.html", error=error, sections=sections)
            section.section_name = section_name
            section.section_date_created = section_date_created
            section.section_description = section_description
            section.section_max_books = section_max_books
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        sections = Section.query.all()
        return render_template("section_edit.html", sections=sections, error=None)
    return redirect(url_for("admin_login"))

@app.route("/book_delete", methods=["GET", "POST"])

def book_delete():
    global logged_admin
    if logged_admin:
        if request.method == "POST":
            book_id = int(request.form.get("book_id"))
            book = Book.query.filter(Book.book_id == book_id).first()
            db.session.delete(book)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        books = Book.query.all()
        return render_template("book_delete.html", books=books)
    return redirect(url_for("admin_login"))


@app.route("/admin_requests")
def admin_requests():
    requests = Request_book.query.filter_by(status='pending').all()
    for request in requests:
        request.book = Book.query.filter_by(book_id=request.book_id).first()
    approved_books = Request_book.query.filter_by(status='accepted').all()
    for approved_book in approved_books:
        approved_book.book = Book.query.filter_by(book_id=approved_book.book_id).first()
    return render_template("admin_requests.html", requests=requests, approved_books=approved_books)


@app.route("/accept_request/<int:request_id>", methods=["POST"])

def accept_request(request_id):
    request = Request_book.query.get(request_id)
    if request:
        days_required = request.days_required
        request.status = 'accepted'
        return_date = datetime.now() + timedelta(days=days_required)
        request.return_date = return_date
        db.session.commit()
    return redirect(url_for("admin_requests"))

@app.route("/reject_request/<int:request_id>", methods=["POST"])

def reject_request(request_id):
    request = Request_book.query.get(request_id)
    if request:

        request.status = 'rejected'

        db.session.commit()
    return redirect(url_for("admin_requests"))

@app.route("/revoke_access/<int:request_id>", methods=["POST"])
def revoke_access(request_id):
    request = Request_book.query.get(request_id)
    if request:
        request.status = 'revoked'
        db.session.commit()
    return redirect(url_for("admin_requests"))

@app.route("/feedback/<int:book_id>", methods=["POST"])
def feedback(book_id):
    feedback_text = request.form.get('feedback_text')
    new_feedback = Feedback(user_email=logged_user, book_id=book_id, feedback_text=feedback_text)
    db.session.add(new_feedback)
    db.session.commit()

    return redirect(url_for("user_dashboard"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    global logged_admin
    global logged_user
    logged_user = False
    logged_admin = False

    return redirect(url_for("home"))


@app.route("/view_book/<int:book_id>")
def view_book(book_id):
    book = Book.query.get(book_id)

    if book:
        return render_template("book_details.html", book_name=book.book_name, book_content=book.book_content)
    return "Book not found", 404

@app.route("/available_books")
def available_books():
    issued_books_count = db.session.query(Request_book.book_id, db.func.count()).filter(Request_book.status.in_(['accepted', 'revoked', 'returned'])).group_by(Request_book.book_id).all()

    students_issued_count = db.session.query(Request_book.book_id, db.func.count()).filter(Request_book.status == 'accepted').group_by(Request_book.book_id).all()
    issued_books_dict = {book_id: count for book_id, count in issued_books_count}
    students_issued_dict = {book_id: count for book_id, count in students_issued_count}
    books = Book.query.all()
    book_data = []
    for book in books:
        times_issued = issued_books_dict.get(book.book_id, 0)
        students_issued = students_issued_dict.get(book.book_id, 0)

        book_data.append({
            'name': book.book_name,
            'times_issued': times_issued,
            'students_issued': students_issued
        })
    return render_template("available_books.html", book_data=book_data)

@app.route("/feedback_list")
def feedback_list():
    feedback_entries = Feedback.query.all()
    feedback_data = []

    for feedback_entry in feedback_entries:

        feedback_data.append({
            'user_email': feedback_entry.user_email,

            'user_name': feedback_entry.user.user_name,
            'book_name': feedback_entry.book.book_name,
            'feedback_text': feedback_entry.feedback_text

        })
    return render_template("feedback_list.html", feedback_data=feedback_data)




@app.route("/admin_search", methods=["GET","POST"])
def admin_search():
    global logged_admin
    if logged_admin:
        sections, books = [],[]
        if request.method=="POST":
            checkbox = request.form.get("flexRadioDefault")
            if checkbox =="section":
                section_name = request.form.get("section_name")
                sections = Section.query.filter(Section.section_name.ilike(f"%{section_name}%")).all()  
            elif checkbox =="book": 
                book_name = request.form.get("book_name")
                books = Book.query.filter(Book.book_name.ilike(f"%{book_name}%")).all() 

        admin = Admin.query.get(logged_admin)
        return render_template("admin_search.html", admin_name = admin.admin_name, sections = sections , books = books)
    return redirect(url_for("admin_login"))

@app.route("/user_search", methods=["GET","POST"])
def user_search():
    global logged_user
    if logged_user:
        sections, books = [],[]
        if request.method=="POST":
            checkbox = request.form.get("flexRadioDefault")
            if checkbox =="section":
                section_name = request.form.get("section_name")
                sections = Section.query.filter(Section.section_name.ilike(f"%{section_name}%")).all() 
            elif checkbox =="book": 
                book_name = request.form.get("book_name")
                books = Book.query.filter(Book.book_name.ilike(f"%{book_name}%")).all()  

        user = User.query.get(logged_user)
        return render_template("user_search.html", user_name = user.user_name, sections = sections , books = books)
    return redirect(url_for("user_login"))
