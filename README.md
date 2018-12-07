Hosted on heroku at: https://final364nicole.herokuapp.com
 

My final project will be an extension of my midterm, where users can search an ingredient and get recipe results back using the Edamam API. If they’re logged in, they can create a recipe collection using the past recipe results, and also update (rename) and delete these. 

Models:
	Recipes
	Ingredients
	Users
	RecipeCollection

Routes: 
	/login 
	/logout
	/register
	/secret

	Can see before login -
		/ = index route will have the search form on it
		/recipe_results = get a list of recipes back from a search with hyperlinks to the recipes
		/all_recipes = see past recipe results
		/all_ingred = see past ingredient searches
	
	Can see after login -
		/create_recipe_collection = create personal collection of recipes from any past recipe results, you can only name it something with alpha characters (whitespaces count as not alpha!!! so including whitespaces will not pass validation)
		/all_collections = see collections you've created. click on collection name to update the name. you can also delete from here 

		/delete/<name> = delete recipe collection
		/update/<name> = update recipe collection

Forms:
	RegistrationForm
	LoginForm
	IngredForm = search an ingredient and get results
	CollectionCreateForm
	UpdateRecipeForm = update collection name

Templates:
	404.html
	all_collections.html
	all_ingred.html
	all_recipes.html
	base.html
	login.html
	form.html
	register.html
	create_recipe_collection.html
	recipe_results.html = displays current recipe results from one search
	update_info.html
	

Relationships:
	one -> many: Ingredient to Recipes
	many -> many: RecipeCollection to Recipes
