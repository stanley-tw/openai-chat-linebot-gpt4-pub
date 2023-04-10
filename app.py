import os
import struct
import json
import openai
import fdb
import random
from flask import Flask, request, abort, jsonify
from dotenv import load_dotenv

load_dotenv()
debug = {
    "verbose": 1
}

# Initialize environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SRV_PORT = int(os.getenv("WEBSITES_PORT", 9999))
ENTRY_FUNC_NAME = os.getenv("ENTRY_FUNC_NAME", "/callback")

# Initialize APIs
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

fdb.api_version(710)

class Chatbot:
    def __init__(self):
        self.default_model = "gpt-3.5-turbo"
        self.max_gap = 30  # keep last 30 records, plus a random number
        self.all_cmd = {
            "/clear": {"func": self.do_clear, "desc": "Reset the bot"},
            "/history": {"func": self.do_show_history, "desc": "Display conversation history"},
            "/model": {"func": self.do_show_model, "desc": "Display bot model"},
            "/help": {"func": self.do_show_help, "desc": "Display help"},
            "/?": {"func": self.do_show_help, "desc": "Display help"}
        }
        self.db = fdb.open(cluster_file="./fdb.cluster")

    def process_request(self, user_id, user_input):
        reply = "default reply"
        try:
            if debug["verbose"]: print(f"@@@ process_request user={user_id}, input={user_input}")

            if user_input.startswith("/"):
                reply = self.handle_command(user_id, user_input)
            else:
                reply = self.handle_chat(user_id, user_input)
        except Exception as e:
            reply = "Error: " + str(e)
        if debug["verbose"]: print(reply)
        return reply

    def handle_command(self, user_id, user_input):
        if debug["verbose"]: print(f"@@@ handle_command: {user_id}:{user_input}\n")

        try:
            v = self.all_cmd[user_input]
        except KeyError:
            return f"Invalid command: {user_input}"
        return v["func"](self.db, user_id, user_input)


    @fdb.transactional
    def do_show_model(self, tr, user_id, user_input):
        openai_model_gpt = []
        response = openai.Model.list()
        if debug["verbose"]: print(response)

        models = response.get("data")
        for m in models:
            if (m["id"].startswith("gpt")):
                if (debug["verbose"]): print(m["id"])
                openai_model_gpt.append(m["id"])

        msg = ""
        for m in openai_model_gpt:
            if m == self.default_model:
                msg = msg + m + " (active)\n"
            else:
                msg = msg + m + "\n"
        return msg

    @fdb.transactional
    def do_show_help(self, tr, user_id, var_ignored):
        msg = ""
        for cmd, value in self.all_cmd.items():
            msg = msg + cmd + ":" + value["desc"] + "\n"
        return msg

    def get_msg_tuple_seq(self, user_id, seq):
        t = (user_id.encode(), "msg", seq)
        k = fdb.tuple.pack(t)
        return k

    def get_seq_tuple(self, user_id, seqtype):
        t = (user_id.encode(), "seq", seqtype,)
        k = fdb.tuple.pack(t)
        return k

    @fdb.transactional
    def do_clear(self, tr, user_id, var_ignored):
        if debug["verbose"]: print(f"@@@ do_clear: user_id={user_id}\n")

        s0 = self.get_seq_tuple(user_id, "prev")
        s1 = self.get_seq_tuple(user_id, "latest")
        if not tr[s0].present() or not tr[s1].present():
            return "Conversation history already cleared"

        tr[s0] = tr[s1]

        return "Conversation history cleared"

    @fdb.transactional
    def do_show_history(self, tr, user_id, var_ignored):
        if debug["verbose"]: print(f"@@@ do_show_history: user_id={user_id}\n")

        s0 = self.get_seq_tuple(user_id, "prev")
        s1 = self.get_seq_tuple(user_id, "latest")

        if not tr[s0].present() or not tr[s1].present():
            return history

        if debug["verbose"]: print(f"    s0:{s0} = {int.from_bytes(tr[s0], byteorder='little')}")
        if debug["verbose"]: print(f"    s1:{s1} = {int.from_bytes(tr[s1], byteorder='little')}")

        begin = self.get_msg_tuple_seq(user_id, int.from_bytes(tr[s0], byteorder='little'))
        end = self.get_msg_tuple_seq(user_id, int.from_bytes(tr[s1], byteorder='little'))

        if debug["verbose"]: print(f"    begin:{begin}")
        if debug["verbose"]: print(f"    end:{end}")

        history = ""
        for k, v in tr[begin:end]:
            history = history + "\n" + v.decode()

        if debug["verbose"]: print(f"   history={history}\n")

        return history

    @fdb.transactional
    def update_history(self, tr, user_id, user_input, assistant_reply):
        if debug["verbose"]: print(f"@@@ update_history: {user_id}={user_input} assistant_reply={assistant_reply}\n")

        s1 = self.get_seq_tuple(user_id, "latest")
        seq = int.from_bytes(tr[s1], byteorder='little')
        t = self.get_msg_tuple_seq(user_id, seq)

        tr[t] = f"User: {user_input}\nAssistant: {assistant_reply}".encode()

        seq += 1
        tr[s1] = (seq).to_bytes(8, byteorder='little')

        if debug["verbose"]: print(f"    new record:{t}")
        if debug["verbose"]: print(f"    new s1: {s1} = {int.from_bytes(tr[s1], byteorder='little')}")

    @fdb.transactional
    def check_user(self, tr, user_id):
        if debug["verbose"]: print(f"@@@ check_user: {user_id}\n")

        s0 = self.get_seq_tuple(user_id, "prev")
        s1 = self.get_seq_tuple(user_id, "latest")
        if not tr[s0].present():
            tr[s0] = (0).to_bytes(8, byteorder='little')
            tr[s1] = (0).to_bytes(8, byteorder='little')

    @fdb.transactional
    def adjust_seq(self, tr, user_id):
        if debug["verbose"]: print(f"@@@ adjust_seq: {user_id}\n")

        s0 = self.get_seq_tuple(user_id, "prev")
        s1 = self.get_seq_tuple(user_id, "latest")
        seq_s0 = int.from_bytes(tr[s0], byteorder='little')
        seq_s1 = int.from_bytes(tr[s1], byteorder='little')
        if (seq_s1 - seq_s0) > (self.max_gap + random.randint(0, 10)):
            tr[s0] = (seq_s1 - 30).to_bytes(8, byteorder='little')

    def handle_chat(self, user_id, user_input):
        if debug["verbose"]: print(f"@@@ handle_chat: {user_id}={user_input}\n")

        self.check_user(self.db, user_id)

        history = self.do_show_history(self.db, user_id, user_input)
        prompt = f"{history}\nUser: {user_input}\nAssistant: "

        response = openai.ChatCompletion.create(
            model=self.default_model,
            messages=[{"role": "user", "content": user_input}],
            max_tokens=500,
            temperature=0.5,
        )

        assistant_reply = response.choices[0].message["content"]
        self.update_history(self.db, user_id, user_input, assistant_reply)
        self.adjust_seq(self.db, user_id)
        return assistant_reply

chatbot = Chatbot()

@app.route(f"{ENTRY_FUNC_NAME}", methods=["POST"])
def callback():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("user_input")

    reply = chatbot.process_request(user_id, user_input)
    return jsonify({"status": "success", "message": reply}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=SRV_PORT)
