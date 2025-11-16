import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token, Span
import warnings
from library.testmorphseg.interface.morpheme_segmenter import MorphemeSegmenter

Token.set_extension("morphemes", default=None)  # do this in the global scope so it happens when imported
Span.set_extension("morphemes",
                   getter=lambda obj: [i._.morphemes for i in obj])  # unsure if this is doing its thing
Doc.set_extension("morphemes", getter=lambda obj: [i._.morphemes for i in obj])


def predict(segmenter, word: str)->list[str]:
    return segmenter.segment(word)[0]


@Language.factory("morpheme_segmenter", default_config={"model_path": None, "train_from_scratch": False})
def seg_factory(nlp, name, model_path, train_from_scratch):  # stateful component to handle different languages
    segmenter = MorphemeSegmenter(nlp.lang, model_path=model_path, train_from_scratch=train_from_scratch)
    nlp.segmenter = segmenter  # attach segmenter to nlp object for access later
    if nlp.lang != "en":  # check if language is supported
        warnings.warn(f"WARNING: tung_tung_seghur currently only works for English.\nWe have detected you are using: {nlp.lang}\nThe segmentations will not be accurate for other languages.")

    def segment_doc(doc):
        for token in doc:
            token._.morphemes = predict(nlp.segmenter, token.text)  # set segmentations for every token in doc
        return doc

    return segment_doc


def load_spacy_integration(lang, model_path=None, train_from_scratch=False):
    cls = spacy.util.get_lang_class(lang)
    seg = MorphemeSegmenter(lang)
    nlp = cls()
    nlp.add_pipe("morpheme_segmenter", config={"model_path": model_path, "train_from_scratch": train_from_scratch})
    return nlp