import time
from fastapi.responses import StreamingResponse

from modal import Stub, web_endpoint

stub = Stub()

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