from bs4 import BeautifulSoup  # webscraper
import requests  # html request maker
import spacy

nlp = spacy.load("en_core_web_sm")
url = "https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/"
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')
#print(soup.text)

recipe_doc = nlp(soup.text) #extract text from site
token_by_part_of_speech = {} 
for token in recipe_doc: #filling dict of tokens by the part of speech assigned to them by en_core_web_sm dependency parser
    if token.pos_ not in token_by_part_of_speech:
      token_by_part_of_speech[token.pos_] = []
    else:
      token_by_part_of_speech[token.pos_].append(token)

token_by_part_of_speech.pop('SPACE') #removing space from the dictionary to focus on words
token_by_part_of_speech.pop('PUNCT') #removing punctuation from the dictionary to focus on words
token_by_part_of_speech.pop('SYM') #removing symbols from the dictionary to focus on words
for key in token_by_part_of_speech.keys():
  token_by_part_of_speech[key] = list(set(token_by_part_of_speech[key])) 
  token_by_part_of_speech[key] = [str(x).lower() for x in token_by_part_of_speech[key] if "." not in str(x) and "#" not in str(x) and ";" not in str(x) and "}" not in str(x) and "{" not in str(x) and "@" not in str(x)]
#removed duplicates from lists and filtered out some trash from the lists (also lowercased all tokens)

print(token_by_part_of_speech)
print(token_by_part_of_speech.keys())
sentences = list(recipe_doc.sents)
#for sentence in sentences:
#	print(f'{sentence[:5]}...')
"""
Going forward: maybe we do this dependency parsing for each sentence and then have a dictionary of sentences to part of speech info for it.
or maybe try to figure out how to typecheck nouns for ingredients or something like that. honestly it's unclear to me our exact goal so I'll
stop here for now. doing any of this other stuff seems pretty simple anyway.
"""
