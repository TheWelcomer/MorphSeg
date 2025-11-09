from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from testmorphseg import MorphemeSegmenter

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "success, is that all you got?"}


@app.get("/health")
async def health():
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
