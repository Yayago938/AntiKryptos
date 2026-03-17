from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    
    origins = [
        "http://localhost:3000",   # React
        "http://127.0.0.1:3000",
        "http://localhost:5173",   # Vite
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )