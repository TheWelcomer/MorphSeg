from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home_root():
    return {"message": "success, is that all you got?"}

@app.get("/health")
async def home_root():
    return {"message": "healthy"}

@app.get("/seg_list/{string}")
async def seg_list(string: str):
    return {"message": "seg_list success"}

@app.get("/seg_string/{string}")
async def seg_string():
    return {"message": "seg_string success"}