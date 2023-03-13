import unicodedata

from bs4 import BeautifulSoup  # webscraper
import requests  # html request maker
import spacy
import re
import random

""" From Lecture 12:
- Parse this well enough to support useful navigation.
- This means breaking “steps” as listed into individual actions or closely connected sets of actions.
- Start by assuming imperative sentences are steps.
- You need a data structure to support navigation forward and backward.
- An array would be a good choice.
- Each element in the array will be an (annotated) step object.
- You need to be able to get from the step object, first: What is the text of that step?
- To support question-answering, you need to annotate each step object with the following information:
    - The cooking action(s) of that step, which will be the verb(s).
    - The ingredient(s) of that step, which will be the direct object.
    - The tools, utensils, and other parameters (time, temperature), which will be indirect objects (objects of propositional phrases).
- You will need these annotations to parameterize question-answering methods associated with queries.
- It will probably make sense to have a simple type system — a semantic model — encompassing: cooking actions, ingredients, utensils, tools, parameters.
- You will need a lexicon of words used in recipes corresponding to this simple semantic model.
"""

ingredients_dict = {}  # just using as a global variable since a lot of the helper functions may use it
all_steps = []  # "You need a data structure to support navigation forward and backward."
chatbot_Qs = ["show me the ingredients list", "go back one step", "go to the next step", "repeat please",
              "take me to the",
              "how do i do that", "how do i", "what is a", "how much of", "what temperature", "how long do i"
                                                                                              "when is it done",
              "what can i substitute for",
              "transform this recipe to"]  # All question prompts from assignment description


# "To support question-answering, you need to annotate each step object with the following information:"
class Step:
    def __init__(self, text, actions=[], ingredients=[], misc={}):
        self.text = text  # full sentence for a given step
        self.actions = actions  # verbs
        self.ingredients = ingredients  # direct objects
        self.misc = misc  # indirect objects (tools, utensils, time, temperature, etc)

    def __str__(self):
        output = f'STEP text:\n   {self.text}\n' \
                 f'ACTIONS: {self.actions}\n' \
                 f'INGREDIENTS: {self.ingredients}\n' \
                 f'MISCELLANEOUS: {self.misc}\n\n'
        return output


# "You will need a lexicon of words used in recipes corresponding to this simple semantic model."
lexicon = {
    "actions": ["add", "adding", "bake", "baking", "beat", "beating", "blend", "blending", "boil", "boiling", "broil",
                "broiling", "brush", "brushing", "chill", "chilling", "coat", "coating", "combine", "combining", "cook",
                "cooking", "cover", "covering", "cream", "creaming", "crush", "crushing", "cut", "cutting", "dice",
                "dicing", "drain", "draining", "drizzle", "drizzling", "dust", "dusting", "fold", "folding", "fry",
                "frying", "garnish", "garnishing", "glaze", "glazing", "grill", "grilling", "heat", "heating", "knead",
                "kneading", "marinate", "marinating", "mash", "mashing", "melt", "melting", "microwave", "microwaving",
                "mix", "mixing", "oven-roast", "oven-roasting", "pan-fry", "pan-frying", "peel", "peeling", "poach",
                "poaching", "pour", "pouring", "preheat", "preheating", "puree", "pureeing", "reduce", "reducing",
                "roast", "roasting", "saute", "sauteing", "season", "seasoning", "shred", "shredding", "simmer",
                "simmering", "squeeze", "squeezing", "stir", "stirring", "strain", "straining", "stuff", "stuffing",
                "thicken", "thickening", "toast", "toasting", "toss", "tossing", "whip", "whipping", "whisk",
                "whisking", "prepare", "preparing", "allow", "allowing", "set", "setting"],
    "ingredients": ['salt', 'sugar', 'flour', 'egg', 'eggs', 'butter', 'oil', 'milk', 'cheese', 'garlic', 'onion',
                    'tomato', 'pepper', 'chicken', 'beef', 'pork', 'fish', 'shrimp', 'rice', 'pasta', 'bean', 'beans',
                    'potato', 'potatoes', 'carrot', 'carrots', 'celery', 'bell pepper', 'bell peppers', 'broccoli',
                    'cauliflower', 'spinach', 'lettuce', 'cucumber', 'avocado', 'lemon', 'lime', 'orange', 'apple',
                    'banana', 'strawberry', 'strawberries', 'blueberry', 'blueberries', 'raspberry', 'raspberries',
                    'almond', 'almonds', 'walnut', 'walnuts', 'cashew', 'cashews', 'sunflower seed', 'sunflower seeds',
                    'pumpkin seed', 'pumpkin seeds', 'sesame seed', 'sesame seeds', 'basil', 'parsley', 'cilantro',
                    'cumin', 'paprika', 'cinnamon', 'vinegar', 'soy sauce', 'mustard', 'ketchup', 'mayonnaise', 'honey',
                    'maple syrup', 'chocolate', 'vanilla extract', 'baking powder', 'baking soda', 'yeast'],
    "utensils": ['bowl', 'mixing bowl', 'whisk', 'spoon', 'fork', 'knife', 'cutting board', 'grater', 'peeler',
                 'colander', 'strainer', 'measuring cup', 'measuring spoon', 'rolling pin', 'pastry brush', 'oven mitt',
                 'pot', 'pan', 'skillet', 'saucepan', 'ladle', 'tongs', 'spatula', 'slotted spoon', 'baking dish',
                 'baking sheet', 'pie dish', 'casserole dish', 'grill pan', 'wok', 'slow cooker', 'blender',
                 'food processor', 'hand mixer', 'stand mixer', 'pastry cutter'],
    "parameters": []}

nlp = spacy.load("en_core_web_sm")

# Parameters to swap in and out for transformations
veggie_ingredients = ['beans', 'lentils', 'tofu', 'tempeh', 'seitan', 'quinoa', 'brown rice', 'wild rice', 'bulgur',
                      'farro', 'barley', 'oats', 'almonds', 'cashews', 'pistachios', 'walnuts', 'pecans', 'hazelnuts',
                      'macadamia nuts', 'brazil nuts', 'chia seeds', 'flax seeds', 'hemp seeds', 'pumpkin seeds',
                      'sesame seeds', 'sunflower seeds', 'poppy seeds', 'nutritional yeast', 'spinach', 'kale',
                      'broccoli', 'cauliflower', 'carrots', 'beets', 'sweet potatoes', 'mushrooms', 'zucchini',
                      'bell peppers', 'tomatoes', 'onions', 'garlic', 'ginger', 'eggplant', 'cabbage', 'celery',
                      'asparagus', 'green beans', 'peas', 'apples', 'oranges', 'bananas', 'berries', 'grapes', 'melons',
                      'pineapple', 'mango', 'papaya', 'kiwi', 'avocado', 'pomegranate', 'basil', 'cilantro', 'parsley',
                      'rosemary', 'thyme', 'dill', 'mint', 'sage', 'oregano', 'bay leaves', 'cumin', 'coriander',
                      'turmeric',
                      'paprika', 'chili powder', 'cinnamon', 'nutmeg', 'cardamom', 'cloves', 'allspice',
                      'mustard seeds',
                      'almond milk', 'soy milk', 'oat milk', 'coconut milk']

veggie_methods = ['bake', 'blanch', 'boil', 'braise', 'broil', 'can', 'dehydrate', 'deep-fry', 'ferment', 'fry',
                  'grill', 'grill on skewers', 'poach', 'pressure cook', 'roast', 'roast in salt crust', 'sauté',
                  'sear', 'sear and braise', 'shallow-fry', 'simmer', 'smoke', 'steam', 'stew', 'stir-fry', 'toast',
                  'whisk', 'beat',
                  'fold', 'marinate', 'pickle', 'brine', 'caramelize', 'glaze', 'grate', 'chop', 'dice', 'mince',
                  'puree', 'blend', 'juice', 'zest', 'slice', 'shred', 'grate', 'julienne', 'spiralize', 'knead',
                  'proof', 'roll', 'stuff', 'toss', 'wrap', 'dust', 'season', 'garnish', 'infuse', 'reduce', 'thicken',
                  'emulsify', 'clarify', 'strain', 'pickle', 'preserve', 'cure', 'chill', 'freeze', 'thaw', 'reheat',
                  'sous-vide cook']

non_veggie_ingredients = ["beef", "pork", "lamb", "veal", "goat", "rabbit", "chicken", "turkey", "duck", "goose",
                          "quail", "game meat", "fish", "shellfish", "crustaceans", "oysters", "clams", "mussels",
                          "scallops", "shrimp", "prawns", "crab", "lobster", "crayfish", "anchovies", "sardines",
                          "tuna", "salmon", "cod", "haddock", "tilapia", "catfish", "trout", "mahi-mahi", "swordfish",
                          "octopus", "squid", "calamari", "cuttlefish", "snails", "frogs", "turtle", "alligator",
                          "bacon", "ham", "prosciutto", "sausage", "chorizo", "salami", "pepperoni", "pastrami",
                          "bologna", "hot dogs", "meatballs", "meatloaf", "liver", "kidneys", "heart", "tongue",
                          "tripe", "brain", "bone marrow", "blood", "pate", "liverwurst", "foie gras",
                          "beef or chicken broth"]

non_veggie_methods = ["bake", "barbecue", "blanch", "braise", "brine", "broast", "broil", "can", "caramelize",
                      "deep-fry", "ferment", "freeze", "glaze", "grill", "hot-smoke", "marinate", "pan-fry", "pickle",
                      "poach", "pressure cook", "roast", "rotisserie", "sauté", "sear", "shallow-fry", "simmer",
                      "slow-cook", "smoke", "sous-vide cook", "steam", "stew", "stir-fry", "stovetop smoke",
                      "roast in salt crust", "stir-fry on high heat", "flash-sear on high heat", "pit-roast",
                      "plank-grill", "caveman-style cook (directly on coals)", "reverse-sear", "par-cook",
                      "double-cook", "butterfly grill", "butterfly roast", "char", "blacken", "spit-roast", "griddle",
                      "bard", "lard", "pudding", "pâté", "terrine", "meatloaf", "roulade"]

unhealthy_ingredients = ['sugar', 'high fructose corn syrup', 'artificial sweeteners', 'hydrogenated oils',
                         'trans fats', 'processed meats', 'canned meats', 'refined grains', 'white flour',
                         'white rice', 'white bread', 'packaged snacks', 'instant noodles', 'processed cheese',
                         'cheese spreads', 'cream cheese', 'heavy cream', 'sour cream', 'margarine', 'shortening',
                         'artificial flavorings', 'artificial colors', 'artificial preservatives',
                         'monosodium glutamate (MSG)', 'sodium nitrate', 'sodium benzoate', 'food dyes',
                         'carrageenan', 'brominated vegetable oil (BVO)', 'aspartame', 'saccharin',
                         'acesulfame potassium', 'butylated hydroxyanisole (BHA)', 'butylated hydroxytoluene (BHT)',
                         'propyl gallate']

unhealthy_methods = ['deep-fry', 'pan-fry', 'sauté in butter or oil', 'bread and fry',
                     'cook with hydrogenated oils or trans fats', 'grill or barbecue over high heat', 'charbroil',
                     'overcook or burn food', 'cook with excessive salt', 'cook with excessive sugar',
                     'microwave in plastic containers or wrap', 'use non-stick cookware at high temperatures',
                     'cook with processed meats or highly processed ingredients', 'cook with MSG',
                     'cook with artificial sweeteners or flavorings', 'use pre-packaged or convenience foods',
                     'add excessive amounts of cheese or creamy sauces to dishes',
                     'a boatload of heavy cream or butter', 'a ton of processed and refined carbohydrates',
                     'a ton of red meat or fatty cuts of meat']

healthy_ingredients = ['almonds', 'apples', 'apricots', 'artichokes', 'arugula', 'asparagus', 'avocados', 'bananas',
                       'barley', 'basil', 'beans', 'beets', 'bell peppers', 'black beans', 'blackberries',
                       'blueberries', 'bok choy', 'broccoli', 'Brussels sprouts', 'buckwheat', 'butternut squash',
                       'cabbage', 'cantaloupe', 'carrots', 'cashews', 'cauliflower', 'celery', 'chard', 'cherries',
                       'chickpeas', 'chia seeds', 'chicken (skinless)', 'cilantro', 'cinnamon', 'coconut',
                       'collard greens', 'cranberries', 'cucumbers', 'dill', 'edamame', 'eggplant', 'eggs', 'farro',
                       'fennel', 'figs', 'flaxseeds', 'garlic', 'ginger', 'grapefruit', 'grapes', 'Greek yogurt',
                       'green beans', 'green onions', 'hemp seeds', 'honey', 'kale', 'kiwis', 'lentils', 'leeks',
                       'lemon', 'lettuce', 'lima beans', 'limes', 'macadamia nuts', 'mangoes', 'millet', 'mung beans',
                       'mushrooms', 'mustard greens', 'navy beans', 'nectarines', 'nuts (various)', 'oats',
                       'okra', 'olive oil', 'olives', 'onions', 'oranges', 'papayas', 'parsley', 'passion fruit',
                       'peaches', 'pears', 'peas', 'pecans', 'persimmons', 'pine nuts', 'pineapples', 'pistachios',
                       'pomegranates']

healthy_methods = ['roast vegetables', 'steam with herbs', 'grill lean protein', 'sauté with healthy fats',
                   'bake with whole grains', 'use slow cooker', 'grill or roast veggies', 'poach fish in broth',
                   'use citrus or vinegar dressings', 'stir-fry with colorful veggies', 'use pressure cooker',
                   'grill or roast fruit', 'make soups and stews with veggies and lean protein',
                   'use herbs and spices', 'cook with plant-based protein', 'grill or roast low-fat dairy']

pakistani_or_north_indian_cuisine_ingredients = ['haldi (turmeric)', 'dhania (coriander)', 'jeera (cumin)',
                                                 'kali mirch (black pepper)', 'laung (clove)', 'elaichi (cardamom)',
                                                 'dalchini (cinnamon)', 'kasuri methi (dried fenugreek leaves)',
                                                 'ajwain (carom seeds)', 'saunf (fennel)',
                                                 'amchur (dried mango powder)', 'anardana (dried pomegranate seeds)',
                                                 'garam masala (spice blend)', 'chaat masala (spice blend)',
                                                 'hing (asafoetida)', 'mustard seeds', 'curry leaves',
                                                 'green cardamom', 'bay leaves', 'red chili powder',
                                                 'kasoori methi (dried fenugreek leaves)', 'cumin powder',
                                                 'coriander powder', 'mustard oil', 'ghee (clarified butter)',
                                                 'besan (gram flour)', 'urad dal (black gram)',
                                                 'chana dal (split chickpeas)', 'moong dal (mung beans)',
                                                 'toor dal (pigeon peas)', 'masoor dal (red lentils)',
                                                 'paneer (cottage cheese)', 'dahi (yogurt)', 'ghee (clarified butter)',
                                                 'desi ghee', 'coconut milk', 'tamarind', 'jaggery', 'basmati rice',
                                                 'atta (whole wheat flour)', 'maida (all-purpose flour)',
                                                 'suji (semolina)', 'ajwain seeds', 'kalonji (nigella seeds)',
                                                 'saffron', 'kewra essence', 'rose water', 'cardamom powder',
                                                 'almond powder', 'cashew powder', 'poppy seeds', 'sesame seeds',
                                                 'coconut flakes']

pakistani_or_north_indian_cuisine_methods = ['chop', 'grate', 'mince', 'peel', 'grate', 'grind', 'blend', 'mix',
                                             'marinate', 'sauté', 'roast', 'bake', 'fry', 'boil', 'simmer', 'steam',
                                             'grill', 'barbecue', 'tandoori', 'smoke', 'pressure-cook', 'slow-cook',
                                             'ferment', 'pickle', 'can', 'preserve', 'dry', 'sun-dry', 'temper',
                                             'season', 'stuff', 'garnish', 'toast', 'roast in salt crust',
                                             'stir-fry', 'shallow-fry', 'deep-fry', 'braise', 'blanch', 'parboil',
                                             'char-grill', 'griddle', 'roast on spit', 'baste', 'smoke',
                                             'cook in clay oven (tandoor)', 'cook in a deep pot (handi)',
                                             'cook on a griddle (tawa)', 'cook on a flat pan (tava)',
                                             'cook in a wok (kadhai)', 'cook in a clay pot (matka)',
                                             'cook in a pressure cooker (nagari)', 'cook in a slow cooker (dam pukht)',
                                             'cook on a hot plate (plancha)', 'cook in a large pot (degh)',
                                             'cook in a double boiler (kund)']

gluten_and_lactose_free_ingredients = ["Kale", "Collard greens", "Spinach", "Chard", "Cabbage", "Broccoli",
                                        "Red or green leaf lettuce", "Cauliflower", "Green beans", "Asparagus",
                                        "Eggplant", "Sweet potatoes or yams", "Potatoes (all varieties)", "Carrots",
                                        "Beets", "Acorn Squash", "Butternut Squash", "Zucchini", "Delicata Squash",
                                        "Spaghetti Squash", "Tomatoes", "Eggplant", "Kabocha Squash", "Pumpkin",
                                        "Onions", "Garlic", "Shallots", "Leeks", "Mushrooms", "Peppers", "Avocado",
                                        "White rice", "Brown rice", "Jasmine rice", "Wild rice", "Arborio rice",
                                        "Quinoa", "Kasha (buckwheat)",
                                        "Quick-cooking, steel cut, or rolled old fashioned oats (choose “gluten-free” oats)",
                                        "Amaranth", "Teff", "Millet", "Popcorn", "Sorghum"]


# For a given step, find out ingredients and tools used for it
def extract_items(parts_of_speech):
    ingredients = []
    utensils = []
    if 'NOUN' in parts_of_speech and parts_of_speech['NOUN']:
        for noun in parts_of_speech['NOUN']:
            noun = str(noun)
            if noun in lexicon['ingredients']:
                ingredients.append(noun)
            elif noun in lexicon['utensils']:
                utensils.append(noun)
    return ingredients, utensils


# Do dependency parsing on each sentence. If any of the verbs are cooking verbs, then it is a valid step
# and we store the step and dependency parsing results. Basically initializing every step
def parse_sentences(sentences):
    for sentence in sentences:
        sentence = str(sentence).replace('\n', '').lower()
        # print(sentence)
        # print()
        sent_obj = nlp(sentence)
        sentence_verbs = []

        # TODO: dependency parsing misses phrases like "hand mixer" and doesn't count them as nouns although they're
        #  valid tools to use
        token_by_part_of_speech = {}
        for token in sent_obj:  # filling dict of tokens by the part of speech assigned to them by en_core_web_sm dependency parser
            if token.pos_ not in token_by_part_of_speech:
                token_by_part_of_speech[token.pos_] = []
            else:
                token_by_part_of_speech[token.pos_].append(token)

        # check if the sentence has verbs in it, specificaly cooking verbs
        if 'VERB' in token_by_part_of_speech and token_by_part_of_speech['VERB']:
            for verb in token_by_part_of_speech['VERB']:
                if str(verb) in lexicon["actions"]:
                    sentence_verbs.append(verb)

            # if cooking verbs were found, filter out the parts of speech dict, and
            # create a new Step object and store it
            if len(sentence_verbs) > 0:
                for key in token_by_part_of_speech.keys():
                    token_by_part_of_speech[key] = list(set(token_by_part_of_speech[key]))
                    token_by_part_of_speech[key] = [str(x).lower() for x in token_by_part_of_speech[key] if
                                                    "." not in str(x) and "#" not in str(x) and ";" not in str(
                                                        x) and "}" not in str(
                                                        x) and "{" not in str(x) and "@" not in str(x)]

                misc_dict = {}
                # extract the ingredients and utensils
                ingredients, utensils = extract_items(token_by_part_of_speech)

                if utensils:
                    misc_dict = {'utensils': utensils}

                # extract temperature
                temp_pattern = r'([+-]?\d+(\.\d+)*)\s?°([CcFf])'
                matches = re.findall(temp_pattern, sentence)
                if matches:
                    first_match = matches[0]
                    temp_str = first_match[0] + ' °' + first_match[2].upper()
                    misc_dict['temperature'] = temp_str

                # extract time TODO doesn't entirely match a phrase like 15 to 20 minutes
                time_pattern = r'(\d+)(\s*)(second(s*)|minute(s*)|hour(s*))'
                matches = re.findall(time_pattern, sentence)
                if matches:
                    first_match = matches[0]
                    time_str = first_match[0] + ' ' + first_match[2]
                    misc_dict['time'] = time_str

                new_step = Step(sentence, sentence_verbs, ingredients, misc_dict)
                all_steps.append(new_step)


# extract recipe text from website given URL
def get_recipe_from_url(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    # print(soup.text)
    # print(soup)

    # Html for every ingredient, this assumes that we only use allrecipes.com urls AND that they all follow the same
    # general html structure
    all_ingredients_html = soup.find("div", {"id": "mntl-structured-ingredients_1-0"}).find_all("li")
    # print(all_ingredients_html)
    # print('\n\n')

    for ingredient in all_ingredients_html:
        # extract the quantity, unit, and name of the ingredient
        quantity_tag = ingredient.find('span', {'data-ingredient-quantity': 'true'})
        unit_tag = ingredient.find('span', {'data-ingredient-unit': 'true'})
        name_tag = ingredient.find('span', {'data-ingredient-name': 'true'})

        if quantity_tag and unit_tag and name_tag:
            quantity = quantity_tag.text.strip()
            unit = unit_tag.text.strip()
            name = name_tag.text.strip()

            # print(quantity, unit, name)

            ingredients_dict[name] = {'quantity': quantity, 'unit': unit, 'text': f'{quantity} {unit} {name}'}

    # print(ingredients_dict)
    recipe_doc = nlp(soup.text)  # extract text from site
    return recipe_doc


# sets up data from recipe text to a format the chatbot can answer questions with
def setup(url):
    recipe_doc = get_recipe_from_url(url)
    sentences = list(recipe_doc.sents)
    parse_sentences(sentences)
    # for step in all_steps:  # this loop's just nice for debugging
    #     print(step)
    print(get_recipe_details())


def get_recipe_details():
    recipe_details = {}
    recipe_details['ingredients'] = []
    recipe_details['methods'] = []
    recipe_details['utensils'] = []
    recipe_details['times'] = []
    recipe_details['temperatures'] = []

    # text field of ingredient is just quantity, unit, name of ingredient
    for ingr, quantity_unit_dict in ingredients_dict.items():
        recipe_details['ingredients'].append(f'{quantity_unit_dict["text"]}')

    for step in all_steps:
        # for ingredient in step.ingredients:
        #     recipe_details['ingredients'].append(ingredient)
        for method in step.actions:
            recipe_details['methods'].append(method)
        if 'utensils' in step.misc:
            for utensil in step.misc['utensils']:
                recipe_details['utensils'].append(utensil)
        if 'time' in step.misc:
            recipe_details['times'].append(step.misc['time'])
        if 'temperature' in step.misc:
            recipe_details['temperatures'].append(step.misc['temperature'])

    # TODO display in a human-readable format
    output = "Here are the ingredients you will need:\n"
    for ingr in recipe_details["ingredients"]:
        output += "   " + ingr + "\n"

    # output += "\nHere are the tools you will need:\n"
    # for utensil in recipe_details['utensils']:
    #     output += utensil + ", "

    return output
    # return recipe_details


# interprets questions and provides a tuple of current step number and answer
def answer_question(curr_step, prompt, question, last_answer):
    if prompt == "show me the ingredients list":
        all_ingredients = []
        for step in all_steps:
            for ingredient in step.ingredients:
                if ingredient not in all_ingredients:
                    all_ingredients.append(ingredient)
        return (curr_step, f"Here are all the ingredients: {all_ingredients}")

    elif prompt == "go to the next step":
        if curr_step < len(all_steps) - 1:
            return (curr_step + 1, f"Here's the next step: {all_steps[curr_step + 1].text}")
        return (curr_step, "This is the final step!")

    elif prompt == "go back one step":
        if curr_step > 0:
            return (curr_step - 1, f"Here's the step before this one: {all_steps[curr_step - 1].text}")
        return (curr_step, "This is the first step!")

    elif prompt == "take me to the":
        digit_list = [x for x in re.findall("[0-9]*", question) if x != '']
        if len(digit_list) == 0:
            return (curr_step, None)  # exit returning no information, malformed question
        step_num = digit_list[0]
        if int(step_num) < len(all_steps) and int(step_num) > 0:
            return (int(step_num) - 1, f"Here's step {int(step_num)}: {all_steps[int(step_num) - 1].text}")
        return (curr_step, f"There isn't a {int(step_num)}th step in this recipe!")

    elif prompt == "repeat please":
        return (curr_step, last_answer)

    elif prompt == "how do i do that":
        help_url_stem = "https://www.youtube.com/results?search_query=how+to+"
        for step in all_steps:
            if step.text in last_answer:
                if len(step.actions) != 0:
                    help_url_stem += str(step.actions[0])
                    if len(step.ingredients) != 0:
                        help_url_stem += "+" + str(step.ingredients[0])
                    return (curr_step, f"No worries. I found a reference for you: {help_url_stem}")
        return (curr_step, "I unfortunately could not find a reference for that step.")

    elif prompt == "how do i":
        help_url_stem = "https://www.youtube.com/results?search_query=how+to"
        action = question.replace(prompt, "").strip()
        if action == "":
            return (curr_step, None)  # exit returning no information, malformed question
        words = action.split()
        for word in words:
            help_url_stem += "+" + word
        return (curr_step, f"No worries. I found a reference for you: {help_url_stem}")

    elif prompt == "what temperature":
        curr_step_obj = all_steps[curr_step]
        if 'temperature' in curr_step_obj.misc:
            return curr_step, f'The recipe recommends {curr_step_obj.misc["temperature"]}!'
        else:
            return curr_step, None

    elif prompt == "how long do i":
        curr_step_obj = all_steps[curr_step]
        if 'time' in curr_step_obj.misc:
            return curr_step, f'The recipe recommends {curr_step_obj.misc["time"]}!'
        else:
            return curr_step, None

    elif prompt == "what is a":
        help_url_stem = "https://en.wikipedia.org/wiki/"
        action = question.replace(prompt, "").strip()
        if action == "":
            return (curr_step, None)
        words = action.split()
        for word in words:
            help_url_stem += word + "_"  # add underscores between words
        return (curr_step, f"Here's a Wikipedia article for you: {help_url_stem}")

    elif prompt == "when is it done":  # confused on what 'it' is referring to, last step or time for current step?
        return (
        len(all_steps) - 1, f"The recipe is done when you reach this step: {all_steps[len(all_steps) - 1].text}")

    elif prompt == "what can i substitute for":
        help_url_stem = "https://www.google.com/search?q=what+can+i+substitute+for+"
        action = question.replace(prompt, "").strip()
        if action == "":
            return (curr_step, None)
        words = action.split()
        for word in words:
            help_url_stem += word
        return (curr_step, f"Here's a Google search for you: {help_url_stem}")
    elif prompt == "transform this recipe to":
        is_detail_required = False
        transform_type = question.replace(prompt, "").strip().upper()
        if transform_type == "VEGETARIAN":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    random_veg_ing_index = random.randint(0, len(veggie_ingredients) - 1)
                    step.text = step.text.replace(str(step.ingredients[i]), veggie_ingredients[random_veg_ing_index])
                    step.ingredients[i] = veggie_ingredients[random_veg_ing_index]
                for i in range(len(step.actions)):
                    random_veg_method_index = random.randint(0, len(veggie_methods) - 1)
                    step.text = step.text.replace(str(step.actions[i]), veggie_methods[random_veg_method_index])
                    step.actions[i] = veggie_methods[random_veg_method_index]
        elif transform_type == "NON-VEGETARIAN":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    random_non_veg_ing_index = random.randint(0, len(non_veggie_ingredients) - 1)
                    step.text = step.text.replace(str(step.ingredients[i]),
                                                  non_veggie_ingredients[random_non_veg_ing_index])
                    step.ingredients[i] = non_veggie_ingredients[random_non_veg_ing_index]
                for i in range(len(step.actions)):
                    random_non_veg_method_index = random.randint(0, len(non_veggie_methods) - 1)
                    step.text = step.text.replace(str(step.actions[i]), non_veggie_methods[random_non_veg_method_index])
                    step.actions[i] = non_veggie_methods[random_non_veg_method_index]
        elif transform_type == "HEALTHY":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    random_healthy_ing_index = random.randint(0, len(healthy_ingredients) - 1)
                    step.text = step.text.replace(str(step.ingredients[i]),
                                                  healthy_ingredients[random_healthy_ing_index])
                    step.ingredients[i] = healthy_ingredients[random_healthy_ing_index]
                for i in range(len(step.actions)):
                    random_healthy_methods_index = random.randint(0, len(healthy_methods) - 1)
                    step.text = step.text.replace(str(step.actions[i]), healthy_methods[random_healthy_methods_index])
                    step.actions[i] = healthy_methods[random_healthy_methods_index]
        elif transform_type == "UNHEALTHY":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    random_unhealthy_ing_index = random.randint(0, len(unhealthy_ingredients) - 1)
                    step.text = step.text.replace(str(step.ingredients[i]),
                                                  unhealthy_ingredients[random_unhealthy_ing_index])
                    step.ingredients[i] = unhealthy_ingredients[random_unhealthy_ing_index]
                for i in range(len(step.actions)):
                    random_unhealthy_methods_index = random.randint(0, len(unhealthy_methods) - 1)
                    step.text = step.text.replace(str(step.actions[i]),
                                                  unhealthy_methods[random_unhealthy_methods_index])
                    step.actions[i] = unhealthy_methods[random_unhealthy_methods_index]
        elif transform_type == "NORTH INDIAN OR PAKISTANI CUISINE":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    random_ing_index = random.randint(0, len(pakistani_or_north_indian_cuisine_ingredients) - 1)
                    step.text = step.text.replace(str(step.ingredients[i]),
                                                  pakistani_or_north_indian_cuisine_ingredients[random_ing_index])
                    step.ingredients[i] = pakistani_or_north_indian_cuisine_ingredients[random_ing_index]
                for i in range(len(step.actions)):
                    random_methods_index = random.randint(0, len(pakistani_or_north_indian_cuisine_methods) - 1)
                    step.text = step.text.replace(str(step.actions[i]),
                                                  pakistani_or_north_indian_cuisine_methods[random_methods_index])
                    step.actions[i] = pakistani_or_north_indian_cuisine_methods[random_methods_index]
        elif transform_type == "DOUBLE":
            for ingr, quantity_unit_dict in ingredients_dict.items():
                quantity = unicodedata.normalize("NFKD", quantity_unit_dict['quantity']).split()
                if len(quantity) == 1:
                    try:
                        new_quantity = float(quantity[0]) * 2
                        ingredients_dict[ingr]["quantity"] = str(new_quantity)
                        ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
                    except ValueError:
                        fraction = parse_fraction(quantity[0])
                        new_quantity = fraction * 2
                        ingredients_dict[ingr]["quantity"] = str(new_quantity)
                        ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
                elif len(quantity) == 2:
                    whole_number = float(quantity[0])
                    fraction = parse_fraction(quantity[1])
                    curr_quantity = whole_number + fraction
                    new_quantity = curr_quantity * 2
                    ingredients_dict[ingr]["quantity"] = str(new_quantity)
                    ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
            is_detail_required = True  

        elif transform_type == "HALF":
            for ingr, quantity_unit_dict in ingredients_dict.items():
                quantity = unicodedata.normalize("NFKD", quantity_unit_dict['quantity']).split()
                if len(quantity) == 1:
                    try:
                        new_quantity = float(quantity[0]) / 2
                        ingredients_dict[ingr]["quantity"] = str(new_quantity)
                        ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
                    except ValueError:
                        fraction = parse_fraction(quantity[0])
                        new_quantity = fraction / 2
                        ingredients_dict[ingr]["quantity"] = str(new_quantity)
                        ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
                elif len(quantity) == 2:
                    whole_number = float(quantity[0])
                    fraction = parse_fraction(quantity[1])
                    curr_quantity = whole_number + fraction
                    new_quantity = curr_quantity / 2
                    ingredients_dict[ingr]["quantity"] = str(new_quantity)
                    ingredients_dict[ingr]["text"] = f'{new_quantity} {quantity_unit_dict["unit"]} {ingr}'
            is_detail_required = True  
        elif transform_type == "BAKE TO STIR FRY":
            for step in all_steps:
                for i in range(len(step.actions)):
                    if str(step.actions[i]) == "bake":
                        step.actions[i] = "stir fry"
                        step.text = step.text.replace("bake", "stir fry")
        elif transform_type == "GLUTEN AND LACTOSE FREE":
            for step in all_steps:
                for i in range(len(step.ingredients)):
                    if str(step.ingredients[i]) in gluten_and_lactose_free_ingredients:
                        random_gluten_and_lactose_free_ing_index = random.randint(0,
                                                                                  len(gluten_and_lactose_free_ingredients) - 1)
                        step.text = step.text.replace(str(step.ingredients[i]), gluten_and_lactose_free_ingredients[
                            random_gluten_and_lactose_free_ing_index])
                        step.ingredients[i] = gluten_and_lactose_free_ingredients[
                            random_gluten_and_lactose_free_ing_index]
        # for step in all_steps:
        #     print(step)
        if is_detail_required:
            print(get_recipe_details())
        return (curr_step, "")
    else:
        return (curr_step, None)


def parse_fraction(fraction_str):
    pattern = r'(\d+)[^\d](\d+)'
    fraction_str = re.match(pattern, fraction_str)
    numerator = fraction_str.group(1)
    denominator = fraction_str.group(2)
    fraction = float(numerator) / float(denominator)
    return fraction


"""
elif prompt == "how much of":
"""


# fields user questions and responds
def chat_with_user():
    valid_url = None
    recipe_url = input("Hi, I'm Alex! Please enter a recipe URL. ").strip()  # most basic name ever 💀
    while not valid_url:
        valid_url = True
        # try:
        setup(
            recipe_url)  # you'll have to input https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/ when prompted for debugging
        # except:
        #     valid_url = False
        #     recipe_url = input("Please enter a valid URL. ")

    curr_step = 0
    answer = ""
    last_ans = "Ask me a question regarding this recipe. Alternatively, enter 'bye' to quit.\n"
    prompt_in_Q = False
    while True:
        question = input("Ask me a question regarding this recipe. Alternatively, enter 'bye' to quit.\n").lower()
        for q in chatbot_Qs:
            if q in question:
                curr_step, answer = answer_question(curr_step, q.lower(), question, last_ans)
                if answer == None:
                    answer = "Sorry, I didn't understand your question. Please try to reformulate it."
                prompt_in_Q = True
                print(answer + "\n")
                break
        if not prompt_in_Q:
            print("Sorry, I didn't understand your question. Please try to reformulate it.\n")
        if question == 'bye':
            print("Bye!")
            break
        last_ans = answer
        prompt_in_Q = False


chat_with_user()
''' Original dependency parsing code below: '''
# token_by_part_of_speech = {}
# for token in recipe_doc:  # filling dict of tokens by the part of speech assigned to them by en_core_web_sm dependency parser
#     if token.pos_ not in token_by_part_of_speech:
#         token_by_part_of_speech[token.pos_] = []
#     else:
#         token_by_part_of_speech[token.pos_].append(token)
#
# token_by_part_of_speech.pop('SPACE')  # removing space from the dictionary to focus on words
# token_by_part_of_speech.pop('PUNCT')  # removing punctuation from the dictionary to focus on words
# token_by_part_of_speech.pop('SYM')  # removing symbols from the dictionary to focus on words
# for key in token_by_part_of_speech.keys():
#     token_by_part_of_speech[key] = list(set(token_by_part_of_speech[key]))
#     token_by_part_of_speech[key] = [str(x).lower() for x in token_by_part_of_speech[key] if
#                                     "." not in str(x) and "#" not in str(x) and ";" not in str(x) and "}" not in str(
#                                         x) and "{" not in str(x) and "@" not in str(x)]
# removed duplicates from lists and filtered out some trash from the lists (also lowercased all tokens)

# print(token_by_part_of_speech)
# print(token_by_part_of_speech.keys())
# https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/
