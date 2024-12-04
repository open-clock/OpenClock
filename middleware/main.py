from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import msal
import json
import httpx
import os
import asyncio

# Cache file configuration
CACHE_PATH = os.path.join(".", "cache.bin")

# MSAL configuration
CLIENT_ID = "cda7262c-6d80-4c31-adb6-5d9027364fa7"
SCOPES = ["User.Read", "Mail.Read"]
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Initialize token cache
cache = msal.SerializableTokenCache()

def load_cache():
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, 'r') as f:
                cache.deserialize(f.read())
    except Exception as e:
        print(f"Token cache load error: {e}")

def save_cache():
    try:
        if cache.has_state_changed:
            with open(CACHE_PATH, 'w') as f:
                f.write(cache.serialize())
    except Exception as e:
        print(f"Token cache save error: {e}")

# Initialize MSAL client
app_msal = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority="https://login.microsoftonline.com/common",
    token_cache=cache
)

# Global cache for graph data
cached_result = None

async def update_cache():
    global cached_result
    while True:
        print("Updating cache...")
        try:
            accounts = app_msal.get_accounts()
            if accounts:
                chosen = accounts[0]
                result = app_msal.acquire_token_silent(scopes=SCOPES, account=chosen)
                if result and "access_token" in result:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{GRAPH_API_ENDPOINT}/me",
                            headers={'Authorization': f'Bearer {result["access_token"]}'}
                        )
                        cached_result = response.json()
                        print("Cache updated successfully")
                        save_cache()  # Save token cache after successful update
        except Exception as e:
            print(f"Cache update error: {e}")
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load token cache on startup
    load_cache()
    
    # Start cache update task
    cache_task = asyncio.create_task(update_cache())
    yield
    
    # Cleanup on shutdown
    cache_task.cancel()
    try:
        await cache_task
    except asyncio.CancelledError:
        pass
    save_cache()  # Final save on shutdown

app = FastAPI(
    title="OpenClock API",
    description="This is the API for OpenClock.",
    summary="OpenClock API",
    version="0.0.1",
    license_info={
        "name": "AGPL V3",
        "url": "https://github.com/WernBe220007/OpenClock/blob/main/LICENSE",
    },
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=update_cache, daemon=True).start()

@app.get("/")
async def root():
    return {"message": "Hello World"}

async def get_token(flow):
    await asyncio.sleep(2)
    app_msal.acquire_token_by_device_flow(flow)

@app.get("/microsoft/authenticate")
async def authenticate(background_tasks: BackgroundTasks):
    flow = app_msal.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))
    background_tasks.add_task(get_token, flow)
    return {
        "message": flow["message"],
        "verification_uri": flow["verification_uri"],
        "user_code": flow["user_code"]
    }

@app.get("/microsoft/graph")
async def get_graph_data():
    if cached_result:
        return cached_result
    return {"error": "No cached result available"}