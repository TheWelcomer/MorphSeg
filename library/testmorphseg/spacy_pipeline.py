import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token, Span
import warnings
from .non_spacy.morpheme_segmenter import MorphemeSegmenter
seg = MorphemeSegmenter("eng")
def predict(word:str)->list[str]:
    return seg.segment(word)[0]

Token.set_extension("morphemes",default=None)#do this in the global scope so it happens when imported
Span.set_extension("morphemes",getter=lambda obj: [i._.morphemes for i in obj])#unsure if this is doing its thing
Doc.set_extension("morphemes",getter=lambda obj: [i._.morphemes for i in obj])
@Language.factory("tung_tung_seghur")
def seg_factory(nlp,name):#stateful component to handle different languages
    if nlp.lang != "en": # check if language is supported
        warnings.warn(f"WARNING: tung_tung_seghur currently only works for English.\nWe have detected you are using: {nlp.lang}\nThe segmentations will not be accurate for other languages.")
    def segment_doc(doc):
        for token in doc:
            token._.morphemes = predict(token.text) #set segmentations for every token in doc
        
        return doc
    
    return segment_doc

if __name__=="__main__":
    cls = spacy.util.get_lang_class("en")
    nlp = cls()   
    nlp.add_pipe("tung_tung_seghur")
    result = nlp("I WANNA BE SEGGED SO BAD")
    print([token._.morphemes for token in result])
    print(result._.morphemes)
    #test language filtering
    cls = spacy.util.get_lang_class("fr")
    nlp = cls()   
    nlp.add_pipe("tung_tung_seghur")
    result = nlp("I WANNA BE SEGGED SO BAD")
    print([token._.morphemes for token in result])
    print(result._.morphemes)

