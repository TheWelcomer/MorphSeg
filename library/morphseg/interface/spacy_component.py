import spacy
import warnings

from spacy.language import Language
from spacy.tokens import Doc, Token, Span
from morphseg.interface.morpheme_segmenter import MorphemeSegmenter

Token.set_extension("morphemes", default=None)  # do this in the global scope so it happens when imported
Span.set_extension("morphemes",
                   getter=lambda obj: [i._.morphemes for i in obj])  # unsure if this is doing its thing
Doc.set_extension("morphemes", getter=lambda obj: [i._.morphemes for i in obj])


def predict(segmenter, word: str) -> list[str]:
    result = segmenter.segment(word)
    if not result or len(result) == 0:
        return [word]
    return result[0]


@Language.factory("morpheme_segmenter", default_config={"load_pretrained": True, "model_filepath": None, "is_local": True})
def seg_factory(nlp, name, load_pretrained, model_filepath, is_local):  # stateful component to handle different languages
    segmenter = MorphemeSegmenter(nlp.lang, load_pretrained=load_pretrained, model_filepath=model_filepath, is_local=is_local)
    nlp.segmenter = segmenter  # attach segmenter to nlp object for access later

    def segment_doc(doc):
        for token in doc:
            token._.morphemes = predict(nlp.segmenter, token.text)  # set segmentations for every token in doc
        return doc

    return segment_doc


def load_spacy_integration(lang, load_pretrained=True, model_filepath=None, is_local=True):
    cls = spacy.util.get_lang_class(lang)
    nlp = cls()
    nlp.add_pipe("morpheme_segmenter", config={"load_pretrained": load_pretrained, "model_filepath": model_filepath, "is_local": is_local})
    return nlp
