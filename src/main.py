import json
import os
import openai
import pathlib
import pymupdf

def get_system_prompt(path):
    """Retrieves the system prompt for the system message from path."""
    system_prompt_file = pathlib.Path(path)
    with open(system_prompt_file, "r") as f:
        return f.read()

def whiteout_block(page: pymupdf.TextPage, block: dict):
    """
    Whiteout the block on the page.

    Arguments
    ---------
    page: pymupdf.TextPage
        The page that will be written on.
    block: dict
        The block that will be whiteout.
    """
    for lines in block["lines"]:
        for span in lines["spans"]:
            page.draw_rect(span["bbox"], fill=(1, 1, 1), width=0)


def query(client: openai.OpenAI, 
          data: str,
          model: str = "gpt-4o-mini",
          system_prompt: str = "You are a helpful assistant."
) -> str:
    """
    Receives a query from the user and outputs the result of the model.
    
    Arguments
    ---------
    client: openai.OpenAI
        An OpenAI client to send requests over.
    data: str
        The query that the user is making.
    model: str
        The model that is being used. Defaults to gpt-4o-mini.
    system_prompt: str
        The system message that will be passed into the model to dictate how the agent behaves. Defaults to be a general assistant.
    
    Returns
    -------
    str
        The result of the model given the query and system prompt.
    """
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
    language = input("What is the language you want to translate to? ")
    system_prompt = get_system_prompt("src/prompts/system_prompt.txt")
    system_prompt = system_prompt.replace("{language}", language)

    filename = input("Which PDF file do you want to translate (name of the folder/file)? ")
    input_path = pathlib.Path(f"pdfs/{filename}/{filename}.pdf")
    with pymupdf.open(input_path) as doc:
        for page in doc:
            page_info = page.get_text("dict")

            for block in page_info["blocks"]:
                if "image" not in block:
                    whiteout_block(page, block)
        
        
        output_path = pathlib.Path(f"pdfs/{filename}/{filename}_result.pdf")
        doc.save(output_path)
        print("Done!")


    # data = {"1": "Chào mội người", "2": "tên em là Hiếu", "3": "AI in 13 years"}
    # message = query(client, json.dumps(data), system_prompt=system_prompt)
    # print(message)
    

if __name__ == "__main__":
    main()