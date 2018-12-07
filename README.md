#TODO
 

My final project will be an extension of my midterm, where users can search an ingredient and get recipe results back using the Edamam API. If they’re logged in, they can create a recipe collection using the past recipe results, and also update (rename) and delete these. 

Models:
	Recipes
	Ingredients
	Users
	RecipeCollection

Routes: 
	/login 
	/register

	Can see before login -
		/ = index route will have the search form on it
		/recipe_results = get a list of recipes back 
		/all_recipes = see past recipe results 
	
	Can see after login -
		/recipe_collections = create personal collection of recipes from any past recipe results
		/see_your_collections = see ones you’ve created 
		/edit_collection = delete or update a recipe collection

Forms:
	Ingredient search 
	Collection creation 
	Collection update/delete

Templates:
	404.html
	500.html
	base.html
	login.html
	register.html
	search_form.html = ingredient search form
	recipe_results.html = displays current recipe results from one search
	all_ingred.html = displays past searches
	all_recipes.html = displays past recipe results
	createcollection.html 
	see_your_collections.html 
	updatecollection.html

Relationships:
	one -> many: Ingredient to Recipes
	many -> many: RecipeCollection to Recipes
