from os import link
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField, SelectMultipleField, URLField, FloatField, BooleanField, RadioField, HiddenField, widgets
from wtforms.validators import DataRequired, URL, Email, InputRequired
from flask_ckeditor import CKEditorField


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()



##WTForm
class CreateArticleForm(FlaskForm):
    title = StringField("Article Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Article Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Article Content", validators=[DataRequired()])
    submit = SubmitField("Submit Article")

class ReviewForm(FlaskForm):
    stars = SelectField("How Many Stars", choices=[("0", "0"), ("1", "⭐"), ("2", "⭐"), ("3", "⭐⭐⭐"), ("4", "⭐⭐⭐⭐"), ("5", "⭐⭐⭐⭐⭐")])
    review_text = CKEditorField("Review", validators=[DataRequired()])
    submit = SubmitField("Submit Review")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email(message=(f'That\'s not a valid email address.'))])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message=(f'That\'s not a valid email address.'))])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class CurriculumForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    link = URLField("Curriculum Link", validators=[DataRequired()])
    cdreview = URLField("Cathy Duffy Review Link")
    grades = MultiCheckboxField("What grades are available?", choices=["PreK", "K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
    reviews = FloatField("Number of Reviews")
    stars = FloatField("Number of Stars")
    accredited = RadioField("Is this curriculum accredited?", choices=[("True", "Yes"), ("False", "No")], validators=[DataRequired()])
    cost = SelectField(f"What's the most this curriculum costs?", choices=["$", "$$", "$$$", "$$$$", "Not important"], validators=[DataRequired()])
    worldview = SelectField("Does this curriculum have a particular worldview?", choices=["Christian", "Mennonite", "Secular", "Neutral", "Doesn't matter"], validators=[DataRequired()])
    disability_friendly = RadioField("Is this curriculum learning/developmental disability friendly?", choices=[("True", "Yes"), ("False", "No")], validators=[DataRequired()])
    involvement = MultiCheckboxField("What's the expected Teacher Involvement?", choices=["Low", "Mid", "High"])
    learning_style = MultiCheckboxField("Do their resources favor a learning type?", choices=["No", "Visual", "Audio", "Kinetic"])
    curriculum_type = MultiCheckboxField("What category(ies) does this curriculum fit into?", choices=["Unit based", "All In One", "Project based", "Supplementary"])
    recommended_subjects = MultiCheckboxField("What subject(s) are recommended in particular?", choices=["All", "Language Arts", "Math", "History", "Geography", "Art", "Bible", "Spanish", "French", "Science", "Handwriting"])
    submit = SubmitField("Add Curriculum")

class QuizForm(FlaskForm):
    grades = MultiCheckboxField("What grades are you looking for? Select all that apply.", choices=["PreK", "K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
    accredited = RadioField("Do you need an accredited curriculum?", choices=[("True", "Yes"), ("False", "No")], validators=[DataRequired()])
    cost = SelectField(f"What's the maximum you're willing to spend?", choices=["$", "$$", "$$$", "$$$$", "Not important"], validators=[DataRequired()])
    worldview = SelectField("Do you have a preferred worldview?", choices=["Christian", "Mennonite", "Secular", "Neutral", "Doesn't matter"], validators=[DataRequired()])
    disability_friendly = RadioField("Do you need a curriculum that's learning/developmental disability friendly?", choices=[("True", "Yes"), ("False", "No")], validators=[DataRequired()])
    involvement = RadioField("How much time/involvement do you have/want to put in to planning and implementation?", choices=["Low", "Mid", "High"])
    learning_style = MultiCheckboxField("Are you looking for a particular learning style? Select all that apply.", choices=["No", "Visual", "Audio", "Kinetic"])
    curriculum_type = MultiCheckboxField("What type of curriculum are you looking for? Select all that apply.", choices=["Unit based", "All In One", "Project based", "Supplementary"])
    recommended_subjects = MultiCheckboxField("What subject(s) are you looking for? Select all that apply.", choices=["All", "Language Arts", "Math", "History", "Geography", "Art", "Bible", "Spanish", "French", "Science", "Handwriting"])
    submit = SubmitField("Show Me My Recommended Curriculum")

class SubscribeForm(FlaskForm):
    price_id = HiddenField("prod_LAhZciWJeBSJA8") 
    submit = SubmitField("I'm in!")

class SaveCurrForm(FlaskForm):
    saved = HiddenField('saved')
    
