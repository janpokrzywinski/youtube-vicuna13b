import aiohttp
import asyncio
import json
import sys

from colorama import Fore, Style
from datetime import datetime

API_URL_BASE = "http://localhost:8000/v1"
API_URL_CHAT = f"{API_URL_BASE}/chat/completions"
API_URL_MODELS = f"{API_URL_BASE}/models"
headers = {"Content-Type": "application/json"}

async def get_model():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL_MODELS, headers=headers) as resp:
            reply = await resp.json()
            return reply["data"][0]["id"]

MODEL = asyncio.run(get_model())
payload = {
  "max_tokens": 512,
  "model": MODEL,
  "messages": []
}


def print_response(reply_content, usage, time_delta):
    print(f"{Fore.CYAN}BOT : {Fore.WHITE}{reply_content}\n")
    token_per_sec = float(usage.get('completion_tokens')) / time_delta.total_seconds()
    summary_info = {
        "prompt_tokens": usage.get('prompt_tokens'),
        "completion_tokens": usage.get('completion_tokens'),
        "total_tokens": usage.get('total_tokens'),
        "time_delta": f"{time_delta.total_seconds():.3f}",
        "tps": f"{token_per_sec:.3f}"
    }
    summary_message = f""
    for key in summary_info:
        summary_message += f"{Fore.MAGENTA}{key}={Fore.CYAN}{summary_info.get(key)} "

    summary = f"{Fore.GREEN}USAGE: {summary_message}\n"
    return summary


async def main():
    retry = False
    while True:
        if not retry:
            prompt = input(f"{Fore.YELLOW}USER: {Fore.WHITE}")
            retry = False

        message = {
          "role": "user",
          "content": f"{prompt} ### Response: "
        }
        payload["messages"].append(message)
        async with aiohttp.ClientSession() as session:
            time_start = datetime.now()
            try:
                async with session.post(API_URL_CHAT, data=json.dumps(payload), headers=headers) as resp:
                    if resp.status == 200:
                        reply = await resp.json()
                        time_end = datetime.now()
                        time_delta = time_end - time_start
                        reply_content = reply["choices"][0]["message"]["content"]
                        usage = reply["usage"]
                        summary = print_response(reply_content, usage, time_delta)
                        print(summary)
                        retry = False
                    else:
                        reply = await resp.text()
                        print(f"{Fore.RED}response text = {Fore.YELLOW}{reply}")
                        removed_message = payload["messages"].pop(0)
                        print(f"{Fore.MAGENTA}removed context = {Fore.YELLOW}{removed_message}")
                        retry = True
                        continue
            except Exception as e:
                print(f"ERROR: {e}\nresponse = {resp.text}")

        if not retry:
            msg_index = payload["messages"].index(message)
            payload["messages"][msg_index]["content"] += reply_content

asyncio.run(main())
