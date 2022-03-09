from dataclasses import dataclass
from click import edit
from flask import Flask, render_template, request, url_for, redirect, flash, abort, jsonify, json, session
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date, datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, create_engine, text
from sqlalchemy.orm import relationship, sessionmaker 
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, ReviewForm, CurriculumForm, CreateArticleForm, QuizForm, SaveCurrForm, SubscribeForm
from flask_gravatar import Gravatar
import stripe
import os

domain_url = "http://127.0.0.1:5000/"
stripe.api_key = "pk_test_51IIGWqLGjgKtQE5XbFTv7fAtwgJPUhdzx6fhgSk0mywBTSHx5r251bbsv0Kth9uvdTPEpRTTPAJ2e2Mf0R95AQr700VAxecDYD"
STRIPE_SECRET_API = os.environ.get('STRIPE_SECRET_API')


#initial config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'H@McQfTjWnZr4u7x!A%D*G-JaNdRgUkX'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


#connect to DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///findmycurriculum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

engine = create_engine('sqlite:///findmycurriculum.db')
Session = sessionmaker(engine)
session = Session()



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONFIGURE TABLE

saved_curriculum = db.Table('saved_curriculum',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculum.id', primary_key=True))
)

curriculum_grades = db.Table('curriculum_grades', 
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculum.id', primary_key=True)),
    db.Column('grades_id', db.Integer, db.ForeignKey('grades.id', primary_key=True))
)

learningStyle = db.Table('style', 
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculum.id', primary_key=True)),
    db.Column('learning_style_id', db.Integer, db.ForeignKey('learning_style.id', primary_key=True))
)

curriculumType = db.Table('type', 
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculum.id', primary_key=True)),
    db.Column('curriculum_type_id', db.Integer, db.ForeignKey('curriculum_type.id', primary_key=True))
)

recommendedSubjects = db.Table('subject', 
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curriculum.id', primary_key=True)),
    db.Column('recommended_subjects_id', db.Integer, db.ForeignKey('recommended_subjects.id', primary_key=True))
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    articles = relationship("Article", back_populates="author")
    reviews = relationship("Reviews", back_populates="review_author")
    customerId = db.Column(db.String(50))
    saved_curr = db.relationship("Curriculum", secondary=saved_curriculum, lazy='subquery', backref=db.backref('users', lazy=True))
  

class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="articles")
    title = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class Curriculum(db.Model):
    __tablename__ = "curriculum"
    id = db.Column(db.Integer, primary_key=True)
    curriculum_name = db.Column(db.String(250), unique=True, nullable=False)
    link = db.Column(db.String(250), nullable=False)
    cdreview = db.Column(db.String(250))
    grades = db.relationship('Grades', secondary=curriculum_grades, lazy='subquery', backref=db.backref('curriculum', lazy=True))
    number_of_reviews = db.Column(db.Integer, nullable=False)
    stars = db.Column(db.Float, nullable=False)
    accredited = db.Column(db.String(5), nullable=False)
    cost = db.Column(db.String(), nullable=False)
    worldview = db.Column(db.String(120), nullable=False)
    disability_friendly = db.Column(db.String(4), nullable=False)
    teacher_involvement = db.Column(db.String(5), nullable=False)
    learning_style = db.relationship('Learning_Style', secondary=learningStyle, lazy='subquery', backref=db.backref('curriculum', lazy=True))
    curriculum_type = db.relationship('Curriculum_Type', secondary=curriculumType, lazy='subquery', backref=db.backref('curriculum', lazy=True))
    subjects = db.relationship('Subjects', secondary=recommendedSubjects, lazy='subquery', backref=db.backref('curriculum', lazy=True))
    reviews = db.relationship("Reviews", back_populates="parent_curriculum")


class Grades(db.Model):
    __tablename__ = "grades"
    id = db.Column(db.Integer, primary_key=True)


class Subjects(db.Model):
    __tablename__ = "recommended_subjects"
    id = db.Column(db.Integer, primary_key=True)

class Learning_Style(db.Model):
    __tablename__ = "learning_style"
    id = db.Column(db.Integer, primary_key=True)

class Curriculum_Type(db.Model):
    __tablename__ = "curriculum_type"
    id = db.Column(db.Integer, primary_key=True)
    



class Reviews(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    curriculum_id = db.Column(db.Integer, db.ForeignKey("curriculum.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_curriculum = relationship("Curriculum", back_populates="reviews")
    review_author = relationship("User", back_populates="reviews")
    stars = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)


db.create_all()


##Decorated Functions

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function




def subscribed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if stripe.Subscription.retrieve(customer_id=User.customerId).status == "active":
            return True



## Begin Routes

@app.route('/')
def home():
    return render_template("index.html")

#TODO Update query to query reflect updated database
@app.route('/quiz', methods=["GET", "POST"])
def quiz():
    form = QuizForm()
    if request.method == "POST":
        if form.validate_on_submit:
            grades = form.grades.data
            accredited = form.accredited.data
            cost = form.cost.data
            worldview = form.worldview.data
            disability_friendly = form.disability_friendly.data
            involvement = form.involvement.data
            learning_style = form.learning_style.data
            curriculum_type = form.curriculum_type.data
            recommended_subjects = form.recommended_subjects.data
            result = Curriculum.query.filter(
                Curriculum.grades.like(grades),
                Curriculum.accredited.like(accredited),
                Curriculum.cost.like(cost),
                Curriculum.worldview.like(worldview),
                Curriculum.disability_friendly.like(disability_friendly),
                Curriculum.teacher_involvement.like(involvement),
                Curriculum.learning_style.like(learning_style),
                Curriculum.curriculum_type.like(curriculum_type),
                Curriculum.recommended_subjects.like(recommended_subjects),
                func.max(Curriculum.reviews),
                func.max(Curriculum.stars)
            )

            return redirect(url_for("result", result=result, current_user=current_user))
    return render_template("quiz.html", form=form, current_user=current_user)

@app.route('/result')
def result():
    return render_template('result.html', current_user=current_user)

@app.route('/articles')
def articles():
    articles = Article.query.all()
    return render_template("articles.html", all_articles=articles, current_user=current_user)

@app.route('/articles/<int:article_id>')
def show_article(article_id):
    requested_article = Article.query.get(article_id)
    return render_template("article.html", post=requested_article, current_user=current_user)

## Create article 
@app.route('/add-article', methods=["GET", "POST"])
def add_new_article():
    form = CreateArticleForm()
    if form.validate_on_submit():
        new_article = Article(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user 
        )
        db.session.add(new_article)
        db.session.commit()
        return redirect(url_for("articles"))

    return render_template("add-article.html", form=form, current_user=current_user)

## Edit Article 

@app.route("/edit-article/<int:article_id>", methods=["GET", "POST"])
def edit_article(article_id):
    article = Article.query.get(article_id)
    edit_form = CreateArticleForm(
        title=article.title,
        subtitle=article.subtitle,
        img_url=article.img_url,
        author=current_user,
        body=article.body 
    )
    if edit_form.validate_on_submit():
        article.title=edit_form.title.data
        article.subtitle=edit_form.subtitle.data
        article.img_url=edit_form.img_url.data
        article.body=edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_article", article_id=article.id))
    
    return render_template("add-article.html", form=edit_form, is_edit=True, current_user=current_user)


## Delete Article
@app.route("/delete/<int:article_id>")
def delete_article(article_id):
    article_to_delete = Article.query.get(article_id)
    db.session.delete(article_to_delete)
    db.session.commit()
    return redirect(url_for('articles'))


## REGISTRATION

@app.route('/register', methods=["GET", "POST"])
def register():
    stripe.api_key = STRIPE_SECRET_API
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=10
        )
        customer = stripe.Customer.create(
            email=form.email.data, 
            name=form.name.data)
        
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
            customerId = customer.id
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('create_subscription', customerId=new_user.customerId))

    return render_template("register.html", form=form, current_user=current_user)

#TODO Fix Subscription workflow - Currently gets stuck at credit card form/subscription checkout 
@app.route('/create-subscription/<customerId>', methods=['GET','POST'])
def create_subscription(customerId):
    stripe.api_key = STRIPE_SECRET_API
    form = SubscribeForm()
    price_id = 'price_1KUMARLGjgKtQE5XTkqW4QNq'
    customer_id = customerId
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{
                'price': price_id,
                }],
                payment_behavior='default_incomplete',
                   expand=['latest_invoice.payment_intent'],
                )
        return render_template("subscription.html", subscriptionId=subscription.id, clientSecret=subscription.latest_invoice.payment_intent.client_secret)

    except Exception as e:
              return jsonify(error={'message': e.user_message}), 400
    return render_template("subscription.html", current_user=current_user)


@app.route('/subscription')
def subscription(subscriptionId):
    stripe.api_key = STRIPE_SECRET_API
    subscription = stripe.Subscription.retrieve(id=subscriptionId)
    CLIENT_SECRET = subscription.latest_invoice.payment_intent.client_secret
    return render_template('subscription.html', CLIENT_SECRET=CLIENT_SECRET)



#Edit account - tied to profile? 


@app.route('/cancel-subscription', methods=['POST'])
def cancelSubscription(customerId):
    stripe.api_key = STRIPE_SECRET_API
    customerid = User.query.get(customerId).first()
    data = stripe.Subscription.retrieve(customer=customerid)
    try:
         # Cancel the subscription by deleting it
        deletedSubscription = stripe.Subscription.delete(data['subscriptionId'])
        return jsonify(deletedSubscription)
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route('/webhook', methods=['POST'])
def webhook_received():
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']

    data_object = data['object']

    if event_type == 'invoice.paid':
        # Used to provision services after the trial has ended.
        # The status of the invoice will show up as paid. Store the status in your
        # database to reference when a user accesses your service to avoid hitting rate
        # limits.
        print(data)

    if event_type == 'invoice.payment_failed':
        # If the payment fails or the customer does not have a valid payment method,
        # an invoice.payment_failed event is sent, the subscription becomes past_due.
        # Use this webhook to notify your user that their payment has
        # failed and to retrieve new card details.
        print(data)

    if event_type == 'customer.subscription.deleted':
        # handle subscription canceled automatically based
        # upon your subscription settings. Or if the user cancels it.
        print(data)

    if event_type == 'invoice.payment_succeeded':
        if data_object['billing_reason'] == 'subscription_create':
            subscription_id = data_object['subscription']
            payment_intent_id = data_object['payment_intent']

            # Retrieve the payment intent used to pay the subscription
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Set the default payment method
            stripe.Subscription.modify(
            subscription_id,
            default_payment_method=payment_intent.payment_method
            )


    return jsonify({'status': 'success'})




@app.route('/login', methods=["GET", "POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('profile'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/profile/')
def profile():
    user = User.query.get(current_user.id)
    reviews = session.query(User.reviews)
    return render_template("profile.html", user=user, reviews=reviews, current_user=current_user)

@app.route('/update-profile/')
def update_profile():
    user = User.query.get(current_user.id)
    edit_form = RegisterForm(
        name=user.name,
        email=user.email,
        password=user.password
    )
    if edit_form.validate_on_submit():
        user.name = edit_form.name.data
        user.email = edit_form.email.data
        user.password = edit_form.password.data
        db.session.commit()
        return redirect(url_for("profile", current_user=current_user))

    return render_template("update-profile.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/all-curriculum')
def all_curriculum():
    curriculum = Curriculum.query.all()
    # customerid = current_user.customerId
    # subscription = stripe.Subscription.retrieve(customer=customerid)
    # if subscription.status != "active":
    #     return redirect(url_for('create_subscription'))
    return render_template("all-curriculum.html", all_curriculum=curriculum, current_user=current_user)

@app.route('/curriculum/<int:id>', methods=["GET", "POST"])
def curriculum(id):
    form = ReviewForm()
    save_form = SaveCurrForm()
    requested_curriculum = Curriculum.query.get(id)

    if form.validate_on_submit():
        new_review = Reviews(
            text = form.review_text.data,
            review_author = current_user,
            parent_curriculum = requested_curriculum
        )
        db.session.add(new_review)
        db.session.commit()


    return render_template("curriculum.html", curriculum = requested_curriculum, form = form, save_form=save_form, current_user = current_user)

@app.route('/save-curriculum/<int:id>', methods=["POST"])
def save_curriculum(id):
    if request.methods=="POST":
        user = User.query.get(id=current_user.id)
        saved = Curriculum.query.get(id=id)
        user.saved_curr.append(saved)
        db.session.add(user)
        db.session.commit()
    
    return redirect(url_for('curriculum(id)'))



@app.route('/remove-curriculum/<int:id>', methods=["POST"])
def remove_curriculum(id):
    user = User.query.get(id=current_user.id)
    curriculum_to_remove = User.query.get(saved_curr=id)
    user.saved_curr.split(curriculum_to_remove)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('profile'))
    

#TODO Add insert method for grades, learning style, curriculum type, and subjects > On Add and edit curriculum

@app.route('/add-curriculum', methods=["GET", "POST"])
def add_curriculum():
    form = CurriculumForm()
    if request.method == "POST":
        if form.validate_on_submit():
            new_curriculum = CurriculumForm(
                curriculum_name=form.name.data,
                link=form.link.data,
                cdreview=form.cdreview.data,
                grades=form.grades.data,
                number_of_reviews=form.reviews.data,
                stars=form.stars.data,
                accredited=form.accredited.data,
                cost=form.cost.data,
                worldview=form.worldview.data,
                disability_friendly=form.disability_friendly.data,
                teacher_involvement=form.involvement.data,
                learning_style=form.learning_style.data,
                curriculum_type=form.curriculum_type.data,
                subjects=form.recommended_subjects.data
            )
            db.session.add(new_curriculum)
            db.session.commit()
            return redirect(url_for("all-curriculum"))
    
    return render_template('/add-curriculum.html', form=form, current_user=current_user)

@app.route('/edit-curriculum/<int:id>')
def edit_curriculum(id):
    curriculum = Curriculum.query.get(id)
    edit_form = CurriculumForm(
            curriculum_name = curriculum.curriculum_name,
            link = curriculum.link,
            cdreview = curriculum.cdreview,
            grades = curriculum.grades,
            number_of_reviews = curriculum.reviews,
            stars = curriculum.stars,
            accredited = curriculum.accredited,
            cost = curriculum.cost,
            worldview = curriculum.worldview,
            disability_friendly = curriculum.disability_friendly,
            teacher_involvement = curriculum.involvement,
            learning_style = curriculum.learning_style,
            curriculum_type = curriculum.curriculum_type, 
            subjects = curriculum.recommended_subjects
        )
    if edit_form.validate_on_submit():
            curriculum.curriculum_name = edit_form.name.data,
            curriculum.link = edit_form.link.data,
            curriculum.cdreview = edit_form.cdreview.data,
            curriculum.grades = edit_form.grades.data,
            curriculum.number_of_reviews = edit_form.reviews.data,
            curriculum.stars = edit_form.stars.data,
            curriculum.accredited = edit_form.accredited.data,
            curriculum.cost = edit_form.cost.data,
            curriculum.worldview = edit_form.worldview.data,
            curriculum.disability_friendly = edit_form.disability_friendly.data,
            curriculum.teacher_involvement = edit_form.involvement.data,
            curriculum.learning_style = edit_form.learning_style.data,
            curriculum.curriculum_type = edit_form.curriculum_type.data, 
            curriculum.subjects = edit_form.recommended_subjects.data
            db.session.commit()
            return redirect(url_for("curriculum", id=id))
            
    return render_template("add-curriculum.html", form=edit_form, is_edit=True, current_user=current_user)
        

@app.route("/delete/<id>")
def delete_curriculum(id):
    curriculum_to_delete = Curriculum.query.get(id)
    db.session.delete(curriculum_to_delete)
    db.session.commit
    return redirect(url_for('all_curriculum'))


if __name__ == "__main__":
    app.run(debug=True)