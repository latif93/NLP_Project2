from bs4 import BeautifulSoup  # webscraper
import requests  # html request maker
import spacy


nlp = spacy.load("en_core_web_sm")
url = "https://www.bhg.com/recipes/how-to/bake/how-to-make-cupcakes/"
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')
print(soup.text)

recipe_doc = nlp(soup.text)
# for token in recipe_doc:
# 	print(token, token.idx)

sentences = list(recipe_doc.sents)

for sentence in sentences:
	print(f'{sentence[:5]}...')
