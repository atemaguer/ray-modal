import jinja2
from modal import Image, Stub, asgi_app, web_endpoint, method
import modal as modal
from typing import Dict
from typing import Optional

from fastapi import FastAPI, Header, UploadFile
from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware
import json
import time

# from PIL import Image

origins = ["http://localhost:3000"]

environment = jinja2.Environment()

MODEL_NAME = "TheBloke/chronos-hermes-13B-GPTQ"

model_directory = "/mnt/TheBloke/chronos-hermes-13B-GPTQ"


def download_model():
    from huggingface_hub import snapshot_download

    print("We are  downloading gnow")
    snapshot_download(MODEL_NAME, local_dir=model_directory)


web_app = FastAPI()
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
image = (
    Image.from_dockerhub(
        "nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04",
        setup_dockerfile_commands=[
            "RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y ninja-build python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*",
            "RUN ln -s /usr/bin/python3 /usr/bin/python",
        ],
    )
    .apt_install("git")
    .pip_install("torch==2.0.1", index_url="https://download.pytorch.org/whl/cu118")
    .pip_install(
        [
            "safetensors==0.3.1",
            "sentencepiece>=0.1.97",
            "firebase-admin",
            "ninja==1.11.1",
            "huggingface_hub",
            "pillow",
        ]
    )
    .run_function(download_model)
    .dockerfile_commands(
        [
            "WORKDIR exllama",
            "RUN git clone https://github.com/turboderp/exllama.git .",
            "RUN mv * /root/",
        ]
    )
)

stub = Stub("truly-organic-backenda", image=image)


class Item(BaseModel):
    name: str


def get_client():
    import firebase_admin
    from firebase_admin import credentials, firestore, auth, storage
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP

    if not firebase_admin._apps:
        cred = credentials.Certificate("/root/creds/service.json")
        firebase_admin.initialize_app(
            cred, {"storageBucket": "truly-organic.appspot.com"}
        )
    return firestore.client()


@web_app.get("/")
async def handle_root(user_agent: Optional[str] = Header(None)):
    client = get_client()
    print(f"GET /   - received user_agent={user_agent}")
    print(client)
    client.collection("hi").document("hi").set({"hi": "hi"})
    return "Hello World"


class Character(BaseModel):
    name: str
    personality: str
    introduction: str
    initialMessage: str
    scenario: str
    exampleChats: str


class CreateCharacterBody(BaseModel):
    id_token: str
    character: Character
    image: str


@web_app.post("/create_character")
async def create_character(body: CreateCharacterBody):
    import firebase_admin
    from firebase_admin import credentials, storage, auth
    import base64
    import io
    from PIL import Image

    client = get_client()
    character = vars(body.character)
    decoded_token = auth.verify_id_token(body.id_token)
    uid = decoded_token["uid"]
    character["creator_id"] = uid

    # Upload the photo to firebase
    image_contents = base64.b64decode(body.image[23:])

    image_stream = io.BytesIO(image_contents)
    image = Image.open(image_stream)

    def crop_to_square(image):
        # Get the dimensions of the image
        width, height = image.size

        # Determine the size of the square
        size = min(width, height)

        # Calculate the crop box coordinates
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        # Crop the image
        cropped_image = image.crop((left, top, right, bottom))

        # Return the cropped image
        return cropped_image

    image = crop_to_square(image)
    image_contents = image.getvalue()

    docref = client.collection("characters").document()
    bucket = storage.bucket()

    blob = bucket.blob(f"character-images/{docref.id}.jpg")
    blob.upload_from_string(image_contents)
    blob.make_public()

    userref = client.collection("profiles").document(uid).get()
    if not userref.exists:
        return {"Status": "Creator does not exist"}

    image_url = blob.public_url

    character["image_url"] = image_url
    character["creator"] = userref.to_dict()
    print(f"THIS IS OUR CHARACTER {character}")

    docref.set(character)

    print(f"Post / Creating Character with name {body.character.name}")


class CreateChatBody(BaseModel):
    character_id: str
    id_token: str


@web_app.post("/create_chat")
async def create_chat(body: CreateChatBody):
    import firebase_admin
    from firebase_admin import auth
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP

    client = get_client()
    character_id = body.character_id
    docref = client.collection("chat").document()

    decoded_token = auth.verify_id_token(body.id_token)
    uid = decoded_token["uid"]

    character_doc = client.collection(
        "characters").document(body.character_id).get()
    init_msg_ref = client.collection("messages").document()

    if character_doc.exists:
        docref.set(
            {
                "user_id": uid,
                "character_id": character_id,
                "character": character_doc.to_dict(),
            }
        )

        init_msg_ref.set(
            {
                "created_at": SERVER_TIMESTAMP,
                "chat_id": docref.id,
                "user_id": uid,
                "msg_type": "BOT",
                "message": character_doc.get("initialMessage"),
            }
        )
    else:
        print("COMPLAINING")

    return {"chat_id": docref.id}


class MessageBody(BaseModel):
    id_token: str
    chat_id: str
    message: str


def format(character_name, user_name, messages):
    result = ""
    print("hello")
    for m in messages:
        if m.get("msg_type") == "USER":
            result += f"USER: {user_name}: " + m.get("message") + "\n"
        elif m.get("msg_type") == "BOT":
            result += f"ASSISTANT: {character_name}: " + \
                m.get("message") + "\n"
    print(result)
    return result


@web_app.post("/send_message")
async def send_message(body: MessageBody):
    import firebase_admin
    from firebase_admin import credentials, firestore, auth, storage
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP
    import jinja2

    environment = jinja2.Environment()

    client = get_client()
    decoded_token = auth.verify_id_token(body.id_token)
    uid = decoded_token["uid"]

    chat_ref = client.collection("chat").document(body.chat_id).get()
    if not chat_ref.exists:
        return {"Status": "ERROR 1"}
    character_ref = (
        client.collection("characters").document(
            chat_ref.get("character_id")).get()
    )
    if not character_ref.exists:
        return {"Status": "ERROR 2"}
    user_ref = client.collection("profiles").document(uid).get()
    if not user_ref.exists:
        return {"Status": "ERROR 3"}

    message_ref = client.collection("messages").document()
    if chat_ref.exists and character_ref.exists:
        message_ref.set(
            {
                "created_at": SERVER_TIMESTAMP,
                "user_id": uid,
                "msg_type": "USER",
                "chat_id": body.chat_id,
                "message": body.message,
            }
        )

    # get previous message history
    docs = (
        client.collection("messages")
        .where("chat_id", "==", body.chat_id)
        .order_by("created_at")
        .get()
    )

    pre_conversation_template = """BEGINNING OF CONVERSATION: A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed and fitting answers to the user's questions.
Write {{char}}'s next reply in a fictional roleplay scenario between between {{user}} and {{char}}.

This is {{char}}'s persona:
{{persona}}

This is how {{char}} should talk:
{{example_chats}}

Then the fictional roleplay between {{user}} and {{char}} begins.

ASSISTANT: Scenario: {{scenario}}"""

    post_conversation_template = """ASSISTANT: {{char}}:"""

    model = Model()

    character_name = chat_ref.get("character").get("name")
    user_name = user_ref.get("display_name")

    template = environment.from_string(
        chat_ref.get("character").get("scenario"))
    scenario = template.render(
        user=user_name,
        char=character_name,
    )

    template = environment.from_string(pre_conversation_template)
    pre_prompt = template.render(
        user=user_name,
        char=character_name,
        persona=chat_ref.get("character").get("personality"),
        initial_message=chat_ref.get("character").get("initialMessage"),
        scenario=scenario,
        example_chats=chat_ref.get("character").get("exampleChats"),
    )

    template = environment.from_string(post_conversation_template)
    post_prompt = template.render(
        char=character_name,
    )

    dict_docs = []
    for doc in docs:
        dict_docs.append(doc.to_dict())

    def wrapper():
        for x in model.generate.call(
            dict_docs, pre_prompt, post_prompt, user_name, character_name
        ):
            if x["msg_type"] == "whole_msg":
                message_ref = client.collection("messages").document()
                message_ref.set(
                    {
                        "created_at": SERVER_TIMESTAMP,
                        "user_id": uid,
                        "msg_type": "BOT",
                        "chat_id": body.chat_id,
                        "message": x["msg"],
                    }
                )
            else:
                yield json.dumps(x)

    # Add all the messages to firebaseo

    return StreamingResponse(wrapper(), media_type="text/event-stream")


class GetMessagesBody(BaseModel):
    id_token: str
    chat_id: str


@web_app.post("/get_chat")
async def get_chat(body: GetMessagesBody):
    from firebase_admin import auth

    client = get_client()
    decoded_token = auth.verify_id_token(body.id_token)
    uid = decoded_token["uid"]
    chat_ref = client.collection("chat").document(body.chat_id).get()
    if chat_ref.exists:
        if chat_ref.get("user_id") != uid:
            return {"Status": "ERROR 1"}
    else:
        return {"Status": "ERROR 2"}
    messages = (
        client.collection("messages")
        .where("chat_id", "==", body.chat_id)
        .order_by("created_at")
        .get()
    )
    processed_messages = []

    for message in messages:
        processed_messages.append(message.to_dict())

    return {"chat": chat_ref.to_dict(), "messages": processed_messages}


@web_app.post("/create_user")
async def set_display_name(data: Dict):
    import firebase_admin
    from firebase_admin import credentials, firestore, auth, storage
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP

    display_name = data["display_name"]
    user_name = data["username"]
    password = data["password"]
    client = get_client()
    try:
        # Create a new user
        email = "{}@truly.organic".format(user_name)
        user = auth.create_user(email=email, password=password)
        client.collection("profiles").document(user.uid).set(
            {
                "display_name": display_name,
                "username": user_name,
                "created_at": SERVER_TIMESTAMP,
            }
        )
        print("Successfully created new user:", user.uid)
        return {"msg": "Successfully created new account."}
    except firebase_admin.auth.EmailAlreadyExistsError:
        print("User with the provided email already exists.")
        return {"msg": "Username is not available."}
    except Exception as e:
        print("Error creating new user:", str(e))
        return {"msg": "Error creating new user: {}".format(str(e))}


@stub.function(
    image=image,
    mounts=[
        modal.Mount.from_local_dir(
            "/Users/atemaguer/Development/truly-organic/creds",
            remote_path="/root/creds",
        )
    ],
    keep_warm=1,
    container_idle_timeout=600,
)
@asgi_app()
def fastapi_app():
    import firebase_admin

    return web_app


@stub.function()
def fake_video_streamer():
    for i in range(10):
        yield f"frame {i}: some data\n".encode()
        time.sleep(0.5)


@stub.function()
@web_endpoint()
def stream_me():
    return StreamingResponse(fake_video_streamer.call(), media_type="text/event-stream")


@stub.cls(gpu="A100", keep_warm=1, container_idle_timeout=600)
class Model:
    def __enter__(self):
        from generator import ExLlamaGenerator
        from tokenizer import ExLlamaTokenizer

        from model import ExLlama, ExLlamaCache, ExLlamaConfig
        import glob
        import os

        self.tokenizer_path = os.path.join(model_directory, "tokenizer.model")
        self.model_config_path = os.path.join(model_directory, "config.json")
        self.st_pattern = os.path.join(model_directory, "*.safetensors")
        self.model_path = glob.glob(self.st_pattern)[0]

        # create config from config.json
        self.config = ExLlamaConfig(self.model_config_path)
        # supply path to model weights file
        self.config.model_path = self.model_path

        # create ExLlama instance and load the weights
        model = ExLlama(self.config)
        print(f"Model loaded: {self.model_path}")

        # create tokenizer from tokenizer model file
        tokenizer = ExLlamaTokenizer(self.tokenizer_path)
        # create cache for inference
        cache = ExLlamaCache(model)
        self.generator = ExLlamaGenerator(
            model, tokenizer, cache)  # create generator

    @method()
    def generate(self, messages, pre_prompt, post_prompt, user_name, character_name):
        from tokenizer import ExLlamaTokenizer
        import torch

        tokenizer = ExLlamaTokenizer(self.tokenizer_path)

        self.generator.settings.token_repetition_penalty_max = 1.176
        self.generator.settings.token_repetition_penalty_sustain = (
            self.config.max_seq_len
        )
        self.generator.settings.temperature = 0.7
        self.generator.settings.top_p = 0.1
        self.generator.settings.top_k = 40
        self.generator.settings.typical = 0.0  # Disabled

        max_response_tokens = 600

        MAX_CONTEXT_LENGTH = 1800

        def format_max(character_name, user_name, messages, max_token_length):
            result = None
            prompt_length = 0

            for m in messages[::-1]:
                print(m)
                if m.get("msg_type") == "USER":
                    to_add = f"USER: {user_name}: " + m["message"] + "\n"
                elif m.get("msg_type") == "BOT":
                    to_add = f"ASSISTANT: {character_name}: " + \
                        m["message"] + "\n"
                tokenized_to_add = tokenizer.encode(to_add)
                to_add_length = tokenized_to_add.shape[-1]
                tokenized_length = 0 if result is None else result.shape[-1]
                if to_add_length + tokenized_length > max_token_length:
                    break
                result = (
                    torch.cat((tokenized_to_add, result), dim=1)
                    if result is not None
                    else tokenized_to_add
                )
                prompt_length += len(to_add)
            return (result, prompt_length)

        pre_in_tokens = tokenizer.encode(pre_prompt)
        post_in_tokens = tokenizer.encode(post_prompt)
        occupied_tokens = pre_in_tokens.shape[-1] + post_in_tokens.shape[-1]

        max_conversation_length = MAX_CONTEXT_LENGTH - occupied_tokens

        (conversation_tokens, text_len) = format_max(
            character_name, user_name, messages, max_conversation_length
        )

        in_tokens = torch.cat(
            (pre_in_tokens, conversation_tokens, post_in_tokens), dim=1
        )
        text_len = len(tokenizer.decode(in_tokens[0]))
        print("DECODED PROMPT", tokenizer.decode(in_tokens[0]))
        num_res_tokens = in_tokens.shape[-1]
        # Decode from here

        self.generator.gen_begin_empty()
        self.generator.gen_feed_tokens(in_tokens)

        current_message = ""

        yield {"msg_type": "new"}
        new_msg = False

        # Used to cut out the parts of the message that are not relevant
        clip_string = f"ASSISTANT:{character_name}:".lower()
        clip_str_ptr = 0

        for i in range(max_response_tokens):
            gen_token = self.generator.beam_search()

            if gen_token.item() == tokenizer.eos_token_id:
                self.generator.replace_last_token(tokenizer.newline_token_id)

            num_res_tokens += 1
            text = tokenizer.decode(
                self.generator.sequence_actual[:, -num_res_tokens:][0]
            )
            new_text = text[text_len:]
            stream_text = new_text

            clip = False

            # If starts with assistant, we trim off the letters from the stream
            cleaned_new_text = new_text.strip().lower()
            if (
                clip_str_ptr + len(cleaned_new_text) < len(clip_string)
                and cleaned_new_text
                == clip_string[clip_str_ptr: clip_str_ptr + len(cleaned_new_text)]
            ):
                stream_text = ""
                clip_str_ptr += len(cleaned_new_text)
                clip = True
            # Check that it doesn't start with user
            if new_msg and cleaned_new_text == "user: "[: len(cleaned_new_text)]:
                break

            if text.endswith(f"\n"):
                new_msg = True
                if current_message.strip() != "":
                    yield {"msg_type": "whole_msg", "msg": current_message}
                    print("Current Message", current_message)
                    current_message = ""
                clip_str_ptr = 0
            else:
                if stream_text.strip() != "" and new_msg:
                    yield {"msg_type": "new"}
                    new_msg = False
                if not clip:
                    yield {"msg_type": "add", "msg": new_text}

            text_len = len(text)

            if not clip:
                current_message += new_text
            if not clip:
                print("curr message", current_message)
            if not clip:
                print("printing new generation", new_text)

            if gen_token.item() == tokenizer.eos_token_id:
                if current_message.strip() != "":
                    yield {"msg_type": "whole_msg", "msg": current_message}
                    print("Current Message", current_message)
                    current_message = ""
                print("IN END OF LINE")
                break


@stub.function(image=image, gpu="A100")
def generate_call(prompt):
    return
