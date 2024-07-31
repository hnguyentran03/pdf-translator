import json
import os
import openai
import pathlib

def get_system_prompt(path):
    system_prompt_file = pathlib.Path(path)
    with open(system_prompt_file, "r") as f:
        return f.read()

def query(client: openai.OpenAI, 
          data: str,
          model: str = "gpt-4o-mini",
          system_prompt: str = "You are a helpful assistant."
) -> str:
    user_msg = {"role": "user", "content": data}
    system_msg = {"role": "system", "content": system_prompt}
    
    completion = client.chat.completions.create(
        model=model,
        messages=[system_msg, user_msg]
    )

    message = completion.choices[0].message
    return message


def main():
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Gets the system prompt and puts in the desire language
    language = "English"
    system_prompt = get_system_prompt("src/prompts/system_prompt.txt")
    system_prompt = system_prompt.replace("{language}", language)

    data = {"1": "Chào mội người", "2": "tên em là Hiếu", "3": "AI in 13 years"}
    message = query(client, json.dumps(data), system_prompt=system_prompt)
    print(message)
    

if __name__ == "__main__":
    main()