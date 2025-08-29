
from fastapi import FastAPI, APIRouter
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()
    yield
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()


for name, stream in streams.items():
    stream.start()

router = APIRouter(prefix="/api")
api = FastAPI(lifespan=lifespan)

@router.get("/")
def root():
    return [
        {
            "name": stream.stream_name,
            "mount": stream.mount,
        } for stream in streams.values()
    ]

api.include_router(router)
uvicorn.run(api, host="0.0.0.0", port=5000)
