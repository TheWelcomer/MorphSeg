from fastapi import FastAPI
from testmorphseg import MorphemeSegmenter

app = FastAPI()

@app.get("/")
async def home_root():
    return {"message": "success, is that all you got?"}

@app.get("/health")
async def home_root():
    return {"message": "healthy"}

@app.get("/seg_list/{string}")
async def seg_list(string: str):
    morpheme_segmenter = MorphemeSegmenter(lang="eng", train_from_scratch=False)
    segments = morpheme_segmenter.segment(string, output_string=False)
    print(segments)
    return {"message": segments}

@app.get("/seg_string/{string}")
async def seg_string(string: str):
    morpheme_segmenter = MorphemeSegmenter(lang="eng", train_from_scratch=False)
    segments = morpheme_segmenter.segment(string, output_string=True)
    print(segments)
    return {"message": segments}