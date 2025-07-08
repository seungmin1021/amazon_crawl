import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# uvicorn main:app --host 0.0.0.0 --port 8000
# curl "http://localhost:8000/api/stream/ranking?access_key=123&last_seq=0&count=1"