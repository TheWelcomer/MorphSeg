import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token, Span

def predict(word:str)->list[str]:
    return [word[:len(word)//2],word[len(word)//2:]]

Token.set_extension("morphemes",default=None)#do this in the global scope so it happens when imported
Span.set_extension("morphemes",getter=lambda obj: [i._.morphemes for i in obj])#unsure if this is doing its thing
Doc.set_extension("morphemes",getter=lambda obj: [i._.morphemes for i in obj])
@Language.component("tung_tung_seghur")
def segment_doc(doc):
    for token in doc:
        token._.morphemes = predict(token.text) #set segmentations for every token in doc
    
    return doc

if __name__=="__main__":
    cls = spacy.util.get_lang_class("en")
    nlp = cls()   
    nlp.add_pipe("tung_tung_seghur")
    result = nlp("I WANNA BE SEGGED SO BAD")
    print([token._.morphemes for token in result])
    print(result._.morphemes)