from dotenv import load_dotenv

import replicate

load_dotenv()
 
 
 
def warmup_model():
    replicate.async_run(
    "deepseek-ai/deepseek-vl2:e5caf557dd9e5dcee46442e1315291ef1867f027991ede8ff95e304d4f734200",
    input={"prompt":"hello world","image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAJ0lEQVR4nGJZ6JfJwMDw0tcTSDIxIAHGqucXgFRS+HV0GUAAAAD//9dPBqJFiMM1AAAAAElFTkSuQmCC"}
    )
    

 
def get_pixel_pos(task,image_file):
    
    b64encoding = f"data:image/png;base64,{image_file}"
    
    input = {"temperature":0.1,
             "prompt":f" <image>\n<|grounding|>Locate the: {task}. Choose only ONE thing to locate.",
             "image":b64encoding}

    output = replicate.run(
    "deepseek-ai/deepseek-vl2:e5caf557dd9e5dcee46442e1315291ef1867f027991ede8ff95e304d4f734200",
    input=input
    )
    print(output)

    import re
    
    match = re.search(r"\[\[([+-]?\d+(?:\.\d+)?),\s*([+-]?\d+(?:\.\d+)?),\s*([+-]?\d+(?:\.\d+)?),\s*([+-]?\d+(?:\.\d+)?)\]\]", output)

    if match:
        x1 = int(match.group(1))
        y1 = int(match.group(2))
        x2 = int(match.group(3))
        y2 = int(match.group(4))
        
        x_center = ((x1 + x2)/2)
        y_center = ((y1 + y2)/2)
        
        if x_center > 999 or y_center > 999 or (x1 == 0 and x2 == 0 and y1 == 0 and y2 == 0):
            print("Coordinates not found")
            return False,0,0
        return True,x_center,y_center
    return False,0,0

