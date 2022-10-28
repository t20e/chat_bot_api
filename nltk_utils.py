import numpy as np
import nltk
# nltk.download('punkt')
from nltk.stem.porter import PorterStemmer
stemmer = PorterStemmer()


def tokenize(sentence):
    # splits sentence into separate words
    return nltk.word_tokenize(sentence)


def stem(word):
    # makes words into simaliar smaller words like the example below becomes "organ"
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, all_words):
    tokenized_sentence = [stem(w) for w in tokenized_sentence]
    bag = np.zeros(len(all_words), dtype=np.float32)
    for idx, w in enumerate(all_words):
        if w in tokenized_sentence:
            bag[idx] = 1.0
    return bag



# sentence = ["hello", "how", "are", "you"]
# words = ["hi", "hello", "i", "you", "bye", "thank", "cool"]
# bog = bag_of_words(sentence, words)
# print(bog)
# a = 'how are u '
# print(a)
# a = tokenize(a)
# print(a)

# words = ["Organize", "organizes", "organizing"]
# stemmed_words = [stem(w) for w in words]
# print(stemmed_words)
