Basic goals:

Recipe retrieval and display (see example above, including "Show me the ingredients list");
Navigation utterances ("Go back one step", "Go to the next step", "Repeat please", "Take me to the 1st step", "Take me to the n-th step");
Vague "how to" questions ("How do I do that?", in which case you can infer a context based on what's parsed for the current step);
Specific "how to" questions ("How do I <specific technique>?");
Simple "what is" questions ("What is a <tool being mentioned>?");
Asking about the parameters of the current step ("How much of <ingredient> do I need?", "What temperature?", "How long do I <specific technique>?", "When is it done?");
Ingredient substitution questions ("What can I substitute for <ingredient>?");
Name your bot :)


We cover all basic goals, including failure states for all basic goals and questions, by taking in a recipe and breaking that text up into actions, ingredients, and misc objects stored in a dictionary, which we then call to and retrieve relevant words from when answering the user's question. We used beautifulsoup for web scraping and spaCy's en_core_web_sm as our dependency parser.