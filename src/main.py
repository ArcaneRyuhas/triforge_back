from fastapi import FastAPI

app = FastAPI()


@app.post("/")
async def root():
    return {"message": "Api generated by TryForce"}

@app.get("/getDocumentation/{id}")
async def get_documentation(id: int):
    return {
        "message": f"This is the endpoint that is goint to get the documentation of an account {id}",
    }