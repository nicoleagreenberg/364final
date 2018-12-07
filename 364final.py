###############################
####### SETUP (OVERALL) #######
###############################

# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
import requests
import json
from wtforms.validators import Required, Length, Email, Regexp, EqualTo

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask_migrate import Migrate, MigrateCommand
from threading import Thread
from werkzeug import secure_filename

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['HEROKU_ON'] = os.environ.get('HEROKU')

## Statements for db setup (and manager setup if using Manager)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://nicoleackermangreenberg@localhost:5432/364final" 

manager = Manager(app)
db = SQLAlchemy(app) # For database use
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand) # Add migrate command to manager

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

## Set up shell
def make_shell_context():
	return dict( app=app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))

######################################
######## HELPER FXNS (If any) ########
######################################

def get_or_create_recipes(ingred):
	baseurl = "https://api.edamam.com/search"
	params = {}
	params["q"] = ingred.ingred
	params["app_id"] = 'e4e80ba4'
	params["app_key"] = '648e3b6268fc14c9889a4013d4aaff9b'
	resp = requests.get(baseurl,params=params)
	
	hits = json.loads(resp.text)['hits']
	recipes = []
	for item in hits:
		title = item['recipe']['label']
		recipe_url = item['recipe']['url']
		recipe = Recipe(title=title,recipe_url=recipe_url, ingred_id=ingred.id)
		recipes.append(recipe)
		db.session.add(recipe)
	db.session.commit()
	return recipes

def get_recipe_by_id(id):
	"""returns recipe or None"""
	recipe_obj = Recipe.query.filter_by(id=id).first()
	return recipe_obj

def get_or_create_recipe_collection(db_session, name, recipe_list, current_user):
	#RecipeCollection here = the association table one
	recipeCollection = db_session.query(RecipeCollection).filter_by(name=name,user_id=current_user.id).first()
	if recipeCollection:
		return recipeCollection
	else:
		recipeCollection = RecipeCollection(name=name,user_id=current_user.id,recipes=[])
		for a in recipe_list:
			recipeCollection.recipes.append(a)
		db_session.add(recipeCollection)
		db_session.commit()
		return recipeCollection

# Set up association Table between Recipes and RecipeCollections
recipe_collection = db.Table('recipe_collection',db.Column('recipe_id', db.Integer, db.ForeignKey('recipes.id')),db.Column('collection_id',db.Integer, db.ForeignKey('RecipeCollections.id')))

##################
##### MODELS #####
##################

# Special model for users to log in
class User(UserMixin, db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(255), unique=True, index=True)
	email = db.Column(db.String(64), unique=True, index=True)
	collection = db.relationship('RecipeCollection', backref='User')
	password_hash = db.Column(db.String(128))

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True


class Recipe(db.Model):
	__tablename__ = "recipes"
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String())
	recipe_url = db.Column(db.String())
	ingred_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'))

	def __repr__(self):
		return "{} (ID: {})".format(self.title, self.id)


class Ingredient(db.Model):
	__tablename__ = "ingredients"
	id = db.Column(db.Integer,primary_key=True)
	ingred = db.Column(db.String())
	recipes = db.relationship("Recipe", backref="Ingredient")

	def __repr__(self):
		return "{} (ID: {})".format(self.ingred, self.id)

class RecipeCollection(db.Model):
	__tablename__ = "RecipeCollections"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
	recipes = db.relationship('Recipe',secondary=recipe_collection,backref=db.backref('RecipeCollections',lazy='dynamic'),lazy='dynamic')

class DeleteButtonForm(FlaskForm):
	submit= SubmitField('Delete')

## DB load functions
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id)) # returns User object or None

###################
###### FORMS ######
###################

class RegistrationForm(FlaskForm):
	email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
	username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
	password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
	password2 = PasswordField("Confirm Password:",validators=[Required()])
	submit = SubmitField('Register User')

	#Additional checking methods for the form
	def validate_email(self,field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')

	def validate_username(self,field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[Required(), Length(1,64), Email()])
	password = PasswordField('Password', validators=[Required()])
	remember_me = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')

class IngredForm(FlaskForm):
	ingred=StringField("Enter an ingredient to find recipes made with it (ingredient must be one word): ", validators=[Required()])
	submit = SubmitField("Search for recipes")

	def validate_ingred(self, field):
		display_name_input = field.data.split()
		if len(display_name_input)>1:
			raise ValidationError("Your ingredient name can only be one word.")

class CollectionCreateForm(FlaskForm):
	name = StringField('Collection Name',validators=[Required()])
	recipe_picks = SelectMultipleField('Recipes to include', coerce=int)
	submit = SubmitField("Create Collection")

	def validate_name(self, field):
		name_input = field.data
		if not name_input.isalpha():
			raise ValidationError("Your collection name can only be made up of alpha characters, no numbers or symbols.")

class UpdateRecipeForm(FlaskForm):
	newName = StringField("What is the new name of this collection?", validators=[Required()])
	submit = SubmitField('Update')

	def validate_newName(self, field):
		newName_input = field.data
		if len(newName_input)<4:
			raise ValidationError("Your collection name must be greater than 4 characters.")

#######################
###### VIEW FXNS ######
#######################

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
	form = IngredForm()

	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
	form = IngredForm()

	return render_template('500.html'), 500

## Login routes
@app.route('/login',methods=["GET","POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('home'))
		flash('Invalid username or password.')
	return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out')
	return redirect(url_for('home'))

@app.route('/register',methods=["GET","POST"])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You can now log in!')
		return redirect(url_for('login'))
	return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
	return "Only authenticated users can do this! Try to log in or contact the site admin."

## Main routes

@app.route('/', methods=['GET'])
def home():
	form = IngredForm()

	return render_template('form.html',form=form)

@app.route('/recipe_results', methods=['POST'])
def recipe_results():
	form = IngredForm()
	ingred = form.ingred.data
	recipes = []

	if form.validate_on_submit():

		ingred_objects = Ingredient.query.all()

	## Find out if ingred is duplicate
		
		ingred_check = Ingredient.query.filter_by(ingred=ingred).first() #if something is returned, ingred is True, returns None if there isn't anything in the database

		if ingred_check:
			flash("This ingredient has already been searched for.")
			return redirect(url_for('home'))

	## Get the data from the form
	## If this isn't a duplicate, add it
		if not ingred_check:
			db_ingred = Ingredient(ingred=ingred)
			db.session.add(db_ingred)
			db.session.commit()

			recipes = get_or_create_recipes(ingred=db_ingred)
			if not recipes:
				flash("There are no recipes for this ingredient. Search another one.")
	flash(form.errors)			
	return render_template('recipe_results.html',ingred=ingred,recipes=recipes, form=form)			

@app.route('/all_recipes')
def all_recipes():
	form = IngredForm()

	recipes = Recipe.query.all()
	return render_template('all_recipes.html',recipes=recipes, form=form)

@app.route('/all_ingred')
def all_ingred():
	form = IngredForm()

	ingred = Ingredient.query.all()
	return render_template('all_ingred.html', ingred=ingred, form=form)

@app.route('/create_recipe_collection',methods=["GET","POST"])
@login_required
def create_recipe_collection():
	form = CollectionCreateForm()
	choices = []
	#populating your multi select picklist 
	for r in Recipe.query.all():
		choices.append((r.id, r.title))
	form.recipe_picks.choices = choices
	
	if request.method == 'POST' and form.validate_on_submit():
		recipes_selected = form.recipe_picks.data # list?
		recipe_objects = [get_recipe_by_id(int(id)) for id in recipes_selected]
		get_or_create_recipe_collection(db.session,current_user=current_user,name=form.name.data,recipe_list=recipe_objects) 
		return redirect(url_for('all_collections'))
	flash(form.errors)
	return render_template('create_recipe_collection.html',form=form)
	

@app.route('/all_collections',methods=["GET","POST"])
@login_required
def all_collections():
	collections = RecipeCollection.query.filter_by(user_id = current_user.id).all()
	form = DeleteButtonForm()
	return render_template('all_collections.html', collections = collections, form=form)


@app.route('/delete/<name>',methods=["GET","POST"])
@login_required
def delete(name):
	this_collection = RecipeCollection.query.filter_by(id =name).first()
	db.session.delete(this_collection)
	db.session.commit()
	flash("The collection " + " ' " + this_collection.name + " '" + " has been successfully deleted")
	return redirect(url_for("all_collections"))

@app.route('/update/<name>', methods = ['GET'])
@login_required
def updateRecipe(name):
	form = UpdateRecipeForm(request.args)
	if request.method == 'GET' and form.validate():
		new_name = form.newName.data
		r = RecipeCollection.query.filter_by(name = name).first()
		r.name = new_name
		db.session.commit()
		flash("Updated name of " + name + " to " + new_name)
		return redirect(url_for('all_collections'))
	elif len(request.args):
		flash(form.errors)
	return render_template('update_info.html', name = name, form=form)

## Code to run the application...

if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	app.run(use_reloader=True,debug=True) 

# The usual
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
