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
                 f'ACTIONS: {self.actions}\n\n'
        return output


# TODO by "You will need a lexicon of words used in recipes corresponding to this simple semantic model.", I think
#  they mean that we should have a hard-coded structure of words that would most commonly show up???

# just used chatgpt to generate some words for now, but basically we could use the lexicon for the type checking system
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
                "whisking",  # <-- TODO all generated, might need to think of more
                "prepare", "preparing", "allow", "allowing", "set", "setting"],  # other words I thought of
    "ingredients": [],
    "utensils": [],
    "parameters": []}   # TODO look for numbers that represent things like time and temperature

nlp = spacy.load("en_core_web_sm")
url = "https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/"
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')
# print(soup.text)

recipe_doc = nlp(soup.text)  # extract text from site
token_by_part_of_speech = {}
for token in recipe_doc:  # filling dict of tokens by the part of speech assigned to them by en_core_web_sm dependency parser
    if token.pos_ not in token_by_part_of_speech:
        token_by_part_of_speech[token.pos_] = []
    else:
        token_by_part_of_speech[token.pos_].append(token)

token_by_part_of_speech.pop('SPACE')  # removing space from the dictionary to focus on words
token_by_part_of_speech.pop('PUNCT')  # removing punctuation from the dictionary to focus on words
token_by_part_of_speech.pop('SYM')  # removing symbols from the dictionary to focus on words
for key in token_by_part_of_speech.keys():
    token_by_part_of_speech[key] = list(set(token_by_part_of_speech[key]))
    token_by_part_of_speech[key] = [str(x).lower() for x in token_by_part_of_speech[key] if
                                    "." not in str(x) and "#" not in str(x) and ";" not in str(x) and "}" not in str(
                                        x) and "{" not in str(x) and "@" not in str(x)]
# removed duplicates from lists and filtered out some trash from the lists (also lowercased all tokens)

# print(token_by_part_of_speech)
# print(token_by_part_of_speech.keys())

sentences = list(recipe_doc.sents)

"""
Going forward: maybe we do this dependency parsing for each sentence and then have a dictionary of sentences to part of speech info for it.
or maybe try to figure out how to typecheck nouns for ingredients or something like that. honestly it's unclear to me our exact goal so I'll
stop here for now. doing any of this other stuff seems pretty simple anyway.
"""

# TODO I think we could use the dependency parsing for each sentence to improve this idea:
# General idea for now. it does get decent enough results in an okay amount of time.
for sentence in sentences:
    sentence = str(sentence).replace('\n', '').lower()
    sentence_verbs = []

    for verb in lexicon["actions"]:  # typechecking to see if the sentence contains any cooking actions
        if f' {verb} ' in sentence:  # ignore words in which the verb is a subset of it (e.g. "BAKEry" or "COOKie")
            sentence_verbs.append(verb)

    if len(sentence_verbs) > 0:
        new_step = Step(sentence, sentence_verbs)
        all_steps.append(new_step)

for step in all_steps:
    print(step)

# TODO For question answering stuff:
#  for every step we have found, then figure out the ingredients, utensils, parameters, etc.


