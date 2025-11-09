from testmorphseg import spacy_pipeline
from testmorphseg import MorphemeSegmenter
import testmorphseg
import spacy
import sys
from testmorphseg.non_spacy import model
from testmorphseg.non_spacy.model import LSTMModel
cls = spacy.util.get_lang_class("en")
nlp = cls()   
nlp.add_pipe("tung_tung_seghur")
result = nlp("I WANNA BE SEGGED SO BAD")
print([token._.morphemes for token in result])
print(result._.morphemes)

#sys.modules["model"] = testmorphseg.non_spacy.model
seg = MorphemeSegmenter("eng")

seggs = seg.segment("I WANNA BE SEGGED SO BAD")
print(seggs)
