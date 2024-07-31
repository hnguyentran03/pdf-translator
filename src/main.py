import json
import os
import openai
import pathlib
import pymupdf

def get_system_prompt(path: str):
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


def get_span_from_block(block: dict):
    """
    Gets the text information from the span in a given block.

    Arguments
    ---------
    block: dict
        The block that will be extracted from.

    Returns
    -------
    list[dict]
        List of spans that holds information on the text and its position, font, etc.
    """
    spans = []
    for lines in block["lines"]:
        for span in lines["spans"]:
            spans.append(span)
    return spans


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

    message = completion.choices[0].message.content
    return message

def insert_text_dynamic(page: pymupdf.TextPage, 
                        text: str,
                        color: tuple,
                        bbox: tuple, 
                        max_size: int
):
    """
    Writes text onto the page, adjusting the length to ensure it fits inside a bounding box.

    Arguments
    ---------
    page: pymupdf.TextPage
        The page to be written on.
    text: str
        The text that will be written on the page.
    color: tuple
        The color of the text.
    bbox: tuple
        A tuple (x0, y0, x1, y1) of the bounding box of the text.
    max_size: int
        The maximum font size for the text.
    """
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0

    font_size = 1
    text_width, text_height = pymupdf.get_text_length(text, fontsize=font_size), font_size

    # Incrementally increase font size until the text no longer fits
    while text_width < width and text_height < height and font_size <= max_size:
        font_size += 1
        text_width, text_height = pymupdf.get_text_length(text, fontsize=font_size), font_size

    font_size -= 1

    # Text alignment
    text_width, text_height = pymupdf.get_text_length(text, fontsize=font_size), font_size
    x = x0 + 1  # + 1 for padding
    y = y0 + (height - text_height) / 2 + text_height

    page.insert_text(pymupdf.Point(x, y),
                     text,
                     fontsize=font_size,
                     color=color
                     )

def replace_text(page: pymupdf.TextPage, 
                 spans: dict, 
                 replacement_texts: dict
):
    """
    Writes each of the translate text on top of the whiteout area based on the span.

    Arguments
    ---------
    page: pymupdf.TextPage
        The page to be written on.
    spans: dict
        A dictionary mapping {pos: text_info} where text_info is a dict containing the position, font, etc. of the text.
    replacement_texts: dict
        A dictionary mapping {pos: translated_text} where pos corresponds to the pos in spans.
    """
    for pos, replacement_text in replacement_texts.items():
        pos = int(pos) # Because spans initialized pos as an int
        if pos in spans:
            span = spans[pos]
            insert_text_dynamic(page=page, 
                                text=replacement_text, 
                                color=pymupdf.sRGB_to_pdf(span["color"]),
                                bbox=span["bbox"], 
                                max_size=span["size"])

def main():
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Replace api_key if needed

    # Gets the system prompt and puts in the desire language
    language = input("What is the language you want to translate to? ")
    system_prompt = get_system_prompt("src/prompts/system_prompt.txt") # Replace path here for different prompts
    system_prompt = system_prompt.replace("{language}", language)

    # Because the pdfs are in the folder `pdfs/{filename}` for organization
    filename = input("Which PDF file do you want to translate (name of the folder/file)? ")
    input_path = pathlib.Path(f"pdfs/{filename}/{filename}.pdf")

    # PDF processing
    with pymupdf.open(input_path) as doc:
        for page in doc:
            page_info = page.get_text("dict")
            spans = []
            for block in page_info["blocks"]:
                if "image" not in block:
                    whiteout_block(page, block)
                    spans.extend(get_span_from_block(block))
            
            spans = dict(enumerate(spans)) # Tries to maintain the position of the text after translation by enumerating them
            texts = {pos: span["text"] for pos, span in spans.items()}

            response = query(client, json.dumps(texts),system_prompt=system_prompt)
            translated_texts = json.loads(response)
            replace_text(page, spans, translated_texts)
        
        output_path = pathlib.Path(f"pdfs/{filename}/{filename}_result.pdf")
        doc.save(output_path)
        print("Done!")
    

if __name__ == "__main__":
    main()