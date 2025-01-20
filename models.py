from main import get_db
db = get_db()

class Admin(db.Model):
    __tablename__ = "admin"
    admin_name = db.Column(db.String() , nullable = False)
    admin_email = db.Column(db.String() , primary_key = True, nullable = False)
    admin_password = db.Column(db.String() , nullable = False)


class User(db.Model):
    __tablename__ = "user"
    user_name = db.Column(db.String() , nullable = False)
    user_email = db.Column(db.String() , primary_key = True, nullable = False)
    user_password = db.Column(db.String() , nullable = False)
    user_books_count = db.Column(db.Integer(), default =0)

class Section(db.Model):
    __tablename__ = "section"
    section_id = db.Column(db.Integer() , primary_key = True, autoincrement =True)
    section_name = db.Column(db.String() , nullable = False)
    section_description = db.Column(db.String() , nullable = False)
    section_date_created = db.Column(db.String() , nullable = False)
    section_max_copies_of_book = db.Column(db.Integer())
    section_max_books = db.Column(db.Integer())
    section_no_of_books_added = db.Column(db.Integer(), default =0)

class Book_in_section(db.Model):
    __tablename__ = "book_in_section"
    book_id = db.Column(db.Integer() , db.ForeignKey("book.book_id") , nullable = False)
    section_id = db.Column(db.Integer() , db.ForeignKey("section.section_id"), nullable = False)
    no_of_books = db.Column(db.Integer() , nullable = False)
    id = db.Column(db.Integer() , primary_key = True, autoincrement =True)

class Book(db.Model):
    __tablename__ = "book"
    book_id = db.Column(db.Integer() , primary_key = True, autoincrement =True)
    book_name = db.Column(db.String() , nullable = False)
    book_content = db.Column(db.String() , nullable = False)
    book_author_name = db.Column(db.String() , nullable = False)
    book_rating = db.Column(db.Integer())
    book_date_issued = db.Column(db.Integer())
    feedback = db.Column(db.String())
    book_return_date = db.Column(db.Integer(), default =0)
    book_sections = db.relationship("Section", secondary="book_in_section", backref="section_books")
    book_requests = db.relationship("Request_book")
    
class Request_book(db.Model):
    __tablename__ = "request_book"
    id = db.Column(db.Integer() , primary_key = True, autoincrement =True)
    book_id = db.Column(db.Integer() , db.ForeignKey("book.book_id") , nullable = False)
    section_id = db.Column(db.Integer() , db.ForeignKey("section.section_id"), nullable = False)
    user_email = db.Column(db.String() , db.ForeignKey("user.user_email"), nullable = False)
    request = db.Column(db.Integer())
    days_required = db.Column(db.Integer() , nullable = False)
    request_date = db.Column(db.DateTime(), nullable=False, default=db.func.current_timestamp())
    return_date = db.Column(db.DateTime())
    status = db.Column(db.String(), default='pending')

class Feedback(db.Model):
    __tablename__ = "feedback"
    feedback_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(), db.ForeignKey("user.user_email"), nullable=False)
    book_id = db.Column(db.Integer(), db.ForeignKey("book.book_id"), nullable=False)
    feedback_text = db.Column(db.String(), nullable=False)
    feedback_date = db.Column(db.DateTime(), nullable=False, default=db.func.current_timestamp())
    user = db.relationship("User", backref=db.backref("user_feedbacks", cascade="all, delete-orphan"))
    book = db.relationship("Book", backref=db.backref("book_feedbacks", cascade="all, delete-orphan"))

    