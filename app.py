from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from huggingface_hub import InferenceClient
app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"

MEMORY_FILE = "chat_memory.json"
USER_MEMORY_FILE = "user_memory.json"


# =========================
# LOAD USER MEMORY
# =========================

if os.path.exists(USER_MEMORY_FILE):

    try:

        with open(
            USER_MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            user_memory = json.load(file)

    except:

        user_memory = []

else:

    user_memory = []


# =========================
# LOAD CHAT MEMORY
# =========================

if os.path.exists(MEMORY_FILE):

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            chat_history = json.load(file)

    except:

        chat_history = []

else:

    chat_history = []


# =========================
# SAVE CHAT MEMORY
# =========================

def save_memory():

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chat_history,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================
# SAVE USER MEMORY
# =========================

def save_user_memory():

    with open(
        USER_MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            user_memory,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================
# AUTOMATIC MEMORY DETECTOR
# =========================

def detect_memory(message):

    text = message.strip()

    lower = text.lower()


    patterns = [

        "my favourite subject is ",
        "my favorite subject is ",

        "my favourite color is ",
        "my favorite color is ",

        "my favourite colour is ",
        "my favorite colour is ",

        "my hobby is ",

        "my goal is ",

        "i like ",

        "i love "

    ]


    for pattern in patterns:

        if lower.startswith(pattern):

            memory = text[len(pattern):].strip()


            if memory:

                saved_memory = text


                if saved_memory not in user_memory:

                    user_memory.append(
                        saved_memory
                    )

                    save_user_memory()


                return saved_memory


    return None


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return render_template(
        "index.html",
        history=chat_history
    )


# =========================
# AI CHAT
# =========================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json()

        message = data.get(
            "message",
            ""
        ).strip()


        if not message:

            return jsonify({

                "reply":
                "Please type a message."

            })


        # =========================
        # AUTOMATIC MEMORY
        # =========================

        detect_memory(message)


        # =========================
        # MANUAL REMEMBER COMMAND
        # =========================

        if message.lower().startswith(
            "remember that "
        ):

            memory = message[13:].strip()


            if (
                memory
                and memory not in user_memory
            ):

                user_memory.append(
                    memory
                )

                save_user_memory()


            return jsonify({

                "reply":
                "Okay! I will remember that. 🧠"

            })


        # =========================
        # FORGET MEMORY COMMAND
        # =========================

        if message.lower().startswith(
            "forget that "
        ):

            memory_to_forget= message[12:].strip()


            if memory_to_forget in user_memory:

                user_memory.remove(
                    memory_to_forget
                )

                save_user_memory()


                return jsonify({

                    "reply":
                    "Okay! I have forgotten that memory. 🧠"

                })


            return jsonify({

                "reply":
                "I couldn't find that exact memory."

            })


        # =========================
        # SAVE USER MESSAGE
        # =========================

        chat_history.append({

            "role":
            "user",

            "content":
            message

        })


        # =========================
        # MINI AI PERSONALITY
        # =========================

        conversation = """
Talk casually and naturally.
Never say "How can I assist you today?" or "What would you like me to help you with?".
Talk like a normal friend having a conversation.
When the user says hello or asks casual questions, respond casually instead of offering help.
 Do not use phrases like "How can I assist you today?" unless the user actually asks for help.

You are Mini AI, a natural, friendly and intelligent personal AI assistant.

Conversation style:
- Talk naturally like a real helpful friend.
- Do not sound robotic, repetitive, or overly formal.
- Understand the user's mood and context.
- Keep the conversation flowing naturally.
- Give direct and practical answers.
- For simple questions, give simple answers.
- For difficult questions, explain step by step.
- Ask a short follow-up question when it helps continue the conversation.
- Do not ask unnecessary questions.
- Do not repeat the same information again and again.
- Use emojis naturally, but don't overuse them.
- Be supportive and friendly.
- Never pretend to know something you don't know.
- If you are unsure, say so honestly.

Language:
- Reply in the same language as the user.
- If the user writes Hinglish, reply in simple Hinglish.
- If the user writes Hindi, reply in Hindi.
- If the user writes English, reply in English.

Identity:
- Your name is Mini AI.
- You are a personal AI assistant.
- You can help with study, coding, technology, writing, ideas and general questions.

"""


        # =========================
        # ADD SAVED USER MEMORY
        # =========================

        if user_memory:

            conversation += """

Saved user memory:

"""


            for memory in user_memory:

                conversation += (
                    "- "
                    + memory
                    + "\n"
                )


            conversation += "\n"


        # =========================
        # ADD CHAT HISTORY
        # =========================

        for item in chat_history:

            if item["role"] == "user":

                conversation += (
                    "User: "
                    + item["content"]
                    + "\n"
                )

            else:

                conversation += (
                    "Mini AI: "
                    + item["content"]
                    + "\n"
                )


        conversation += "Mini AI:"
                # NATURAL CASUAL REPLIES
        casual_replies = {
            "hi": "Hii Ritesh 😄",
            "hello": "Hello Ritesh! 😄",
            "hii": "Hii Guru! 😎",
            "hey": "Hey Ritesh! 👋",
            "how are you": "Main badhiya hoon 😄 Tum batao?",
            "kya haal hai": "Main ekdum badhiya hoon 😎 Tumhara kya haal hai?",
            "kaise ho": "Main badhiya hoon 😄 Tum kaise ho?"
        }

        if message.lower().strip() in casual_replies:
            reply = casual_replies[message.lower().strip()]

            chat_history.append({
                "role": "assistant",
                "content": reply
            })

            save_memory()

            return jsonify({
                "reply": reply
                        })

        # =========================
        # OLLAMA
        # =========================

        response = requests.post(

            OLLAMA_URL,

            json={

                "model":
                MODEL,

                "prompt":
                conversation,

                "stream":
                False,

                "options": {

                    "temperature":
                    0.7,

                    "num_predict":
                    200

                }

            },

            timeout=120

        )


        result = response.json()


        if "response" not in result:

            return jsonify({

                "reply":
                "AI did not return a response."

            }), 500


        reply = result["response"].strip()


        # =========================
        # SAVE AI REPLY
        # =========================

        chat_history.append({

            "role":
            "assistant",

            "content":
            reply

        })


        save_memory()


        return jsonify({

            "reply":
            reply

        })


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )


        return jsonify({

            "reply":
            "AI ERROR: "
            + str(e)

        }), 500


# =========================
# HISTORY
# =========================

@app.route("/history")
def history():

    return jsonify(
        chat_history
    )


# =========================
# MEMORY STATUS
# =========================

@app.route("/memory")
def memory_status():

    return jsonify({

        "memory_enabled":
        True,

        "messages_saved":
        len(chat_history),

        "saved_memories":
        len(user_memory),

        "memory_file":
        MEMORY_FILE,

        "user_memory_file":
        USER_MEMORY_FILE

    })


# =========================
# GET SAVED MEMORIES
# =========================

@app.route("/memories")
def get_memories():

    return jsonify({

        "memories":
        user_memory

    })


# =========================
# DELETE SAVED MEMORY
# =========================

@app.route(
    "/delete-memory",
    methods=["POST"]
)
def delete_memory():

    global user_memory


    data = request.get_json()


    memory = data.get(
        "memory",
        ""
    ).strip()


    if memory in user_memory:

        user_memory.remove(
            memory
        )

        save_user_memory()


        return jsonify({

            "success":
            True

        })


    return jsonify({

        "success":
        False,

        "message":
        "Memory not found."

    })


# =========================
# CLEAR CHAT MEMORY
# =========================

@app.route(
    "/clear",
    methods=["POST"]
)
def clear_memory():

    global chat_history


    chat_history = []


    save_memory()


    return jsonify({

        "success":
        True

    })


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )
