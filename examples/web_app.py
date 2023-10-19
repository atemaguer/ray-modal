import time
from fastapi.responses import StreamingResponse

from modal import Stub, Image, web_endpoint

# image = Image.debian_slim()

# stub = Stub(name="test-web-app", image=image)
stub = Stub(name="test-web-app")

def fake_video_streamer():
    for i in range(10):
        yield f"frame {i}: some data\n".encode()
        time.sleep(0.5)


@stub.function()
@web_endpoint()
def stream_me():
    return StreamingResponse(
        fake_video_streamer(), media_type="text/event-stream"
    )