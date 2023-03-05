from bs4 import BeautifulSoup  # webscraper
import requests  # html request maker
import spacy

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

all_steps = []  # "You need a data structure to support navigation forward and backward."


# "To support question-answering, you need to annotate each step object with the following information:"
class Step:
    def __init__(self, text, actions=[], ingredients=[], misc=[]):
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


# TODO by "You will need a lexicon of words used in recipes corresponding to this simple semantic model.", I think
#  they mean that we should have a hard-coded structure of words that would most commonly show up???
# just used chatgpt to generate some words for now, but basically we could use the lexicon for the type checking system
#
# TODO all generated, might need to think of more words ourselves to account for
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
    "parameters": []}  # TODO look for numbers that represent things like time and temperature

nlp = spacy.load("en_core_web_sm")

# TODO Make it work w any url and test accordingly
url = "https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/"
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')
# print(soup.text)

recipe_doc = nlp(soup.text)  # extract text from site

sentences = list(recipe_doc.sents)

"""
Going forward: maybe we do this dependency parsing for each sentence and then have a dictionary of sentences to part of speech info for it.
or maybe try to figure out how to typecheck nouns for ingredients or something like that. honestly it's unclear to me our exact goal so I'll
stop here for now. doing any of this other stuff seems pretty simple anyway.
"""


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
def parse_sentences():
    for sentence in sentences:
        sentence = str(sentence).replace('\n', '').lower()
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
                new_step = Step(sentence, sentence_verbs)

                # extract the ingredients and utensils
                new_step.ingredients, new_step.misc = extract_items(token_by_part_of_speech)
                all_steps.append(new_step)


parse_sentences()

for step in all_steps:
    print(step)

# TODO For question answering stuff:
#  for every step we have found, then figure out the ingredients, utensils, parameters, etc.




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
