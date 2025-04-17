import json
from langchain_core.messages import HumanMessage,SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from android_world.agents.darkagent_system_prompts import generate_short_term_message, generate_short_term_prompt

from android_world.agents.darkagent_vision_model import get_pixel_pos
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont



with open("./android_world/agents/darkagent_mobile_functions.json") as f:
    functions = json.load(f)








class ShortTermReasoner:
    def __init__(self,long_term_task):
        
        self.text_content = generate_short_term_prompt(
        long_term_task=long_term_task
        )

        self.messages = [
            SystemMessage(self.text_content)
        ] 
        self.model = ChatOpenAI(model="gpt-4.1")


    def get_short_term_task(self, task, history, screenshot, previous_screenshot, finish):
        human_message = generate_short_term_message(
            task=task,
            history=history,
            finish=finish
        )

        # Create a font with larger size
        font = ImageFont.truetype("arial.ttf", 20)
        padding = 10

        def overlay_text_on_image(img_data, overlay_text, save_filename):
            """Decode base64 to image, draw overlay text, re-encode, and return new base64 string."""
            decoded = base64.b64decode(img_data)
            image = Image.open(BytesIO(decoded)).convert("RGB")
            draw = ImageDraw.Draw(image)

            # Calculate text bounding box
            bbox = draw.textbbox((0, 0), overlay_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x_pos = (image.width - text_width) // 2
            y_pos = padding  # Start drawing from top padding

            # Draw rectangle sized to text
            draw.rectangle(
                [
                    x_pos - padding,
                    0,  # Start rectangle at the very top
                    x_pos + text_width + padding,
                    y_pos + text_height + padding  # Bottom edge of the box
                ],
                fill="black"
            )
            # Draw text
            draw.text((x_pos, y_pos), overlay_text, fill="white", font=font)

            # (Optional) save for debugging
            image.save(save_filename)

            # Re-encode the modified image
            buff = BytesIO()
            image.save(buff, format="PNG")
            return base64.b64encode(buff.getvalue()).decode("utf-8")

        # Process 'current' screenshot
        # screenshot = overlay_text_on_image(
        #     screenshot,
        #     "Current Screenshot (This is the image \n you should perform an action to)",
        #     "current_screenshot.png"
        # )

        # Process 'previous' screenshot - REMOVED
        # previous_screenshot = overlay_text_on_image(
        #     previous_screenshot,
        #     "Previous Screenshot (This is what the phone \nlooked like before the previous action)",
        #     "previous_screenshot.png"
        # )


        # print("New screenshot and previous screenshot made and being overlaid into the message")


        #Pop up 2 new windows displaying the screenshots
        # image = Image.open(BytesIO(base64.b64decode(screenshot)))
        # image.show()
        # image = Image.open(BytesIO(base64.b64decode(previous_screenshot))) # REMOVED
        # image.show() # REMOVED


        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot}", "detail": "high"}
                },
                # REMOVED previous_screenshot image_url entry
                # {
                #     "type": "image_url",
                #     "image_url": {"url": f"data:image/png;base64,{previous_screenshot}", "detail": "high"}
                # },
                {"type": "text", "text": human_message}
            ],
        )

        # Append the new human message
        self.messages.append(message)


        #self.messages.append(message) # Original line commented out

        success = False
        while not success:
            try:
                print("Getting next action")
                # Pass the current message history
                response = self.model.invoke(self.messages, functions=functions)
                # Append the assistant's response to the history
                self.messages.append(response)
                success = True
            except Exception as e:
                print("Error in getting new task, retrying:", e)
                continue
            
        if getattr(response, 'additional_kwargs', None) is not None and \
            response.additional_kwargs.get('function_call') is not None:
                if response.content:
                    print("Additional content:",response.content)
                    
                    
              
                
                functionArguments = response.additional_kwargs["function_call"]
                arguments = json.loads(functionArguments["arguments"])
                
                if functionArguments["name"] == "type":
                    to_type = arguments["text"]
                    
                            
                    success = False
                    while not success:
                        try:
                            found,req_x,req_y = get_pixel_pos(arguments["position"],screenshot)
                            success = True
                        except Exception as e:
                            print("Error getting coordinates, trying again:",e)
                    if found:
                        x = round((req_x * 1080) / 999)
                        y = round((req_y * 2400) / 999)
                        history.append(f"Action taken: typing the following text: '{to_type}' inside the input field '{arguments['position']}'. Justification: {arguments['justification']}")
                        return {"action_type": "input_text", "text": to_type.replace("\'",""),"x":x,"y":y},False,history   
                    else:
                        history.append(f"Vision model could not find coordinates for the specified item '{arguments['position']}', be more specific or choose another item")     
                    
    
                elif functionArguments["name"] == "tap":
                    success = False
                    while not success:
                        try:
                            found,req_x,req_y = get_pixel_pos(arguments["position"],screenshot)
                            success = True
                        except Exception as e:
                            print("Error getting coordinates, trying again:",e)
                    if found:
                        x = round((req_x * 1080) / 999)
                        y = round((req_y * 2400) / 999)
                        history.append(f"Action taken: tapping on the object described as: '{arguments['position']}'. Justification: {arguments['justification']}")
                        return {"action_type": "click", "x": x,"y":y}, False, history
                    else:
                        history.append(f"Attempt was made to perform tap with justification: {arguments['justification']}. However vision model could not find coordinates for the specified item '{arguments['position']}' when tapping, be more specific or choose another item")       
                elif functionArguments["name"] == "long_tap":   
                    success = False
                    while not success:
                        try:
                            found,req_x,req_y = get_pixel_pos(arguments["position"],screenshot)
                            success = True
                        except Exception as e:
                            print("Error getting coordinates, trying again:",e)
                    if found:
                        x = round((req_x * 1080) / 999)
                        y = round((req_y * 2400) / 999)
                        history.append(f"Action taken: long tapping on the object described as: '{arguments['position']}'. Justification: {arguments['justification']}")
                        return {"action_type": "long_press", "x": x,"y":y}, False, history
                    else:
                        history.append(f"Attempt was made to perform long tap with justification: {arguments['justification']}. Vision model could not find coordinates for the specified item '{arguments['position']}' when long tapping, be more specific or choose another item")  
                        
                elif functionArguments["name"] == "swipe":   
                    success = False
                    while not success:
                        try:
                            found,req_x,req_y = get_pixel_pos(arguments["position"],screenshot)
                            success = True
                        except Exception as e:
                            print("Error getting coordinates, trying again:",e)
                    if found:
                        x = round((req_x * 1080) / 999)
                        y = round((req_y * 2400) / 999)
                        history.append(f"Action taken: swiping in direction {arguments['direction']} on the object described as: '{arguments['position']}'. Justification: {arguments['justification']}")
                        return {"action_type": "swipe", "x": x,"y":y,"direction":arguments["direction"]}, False, history
                    else:
                          history.append(f"Attempt was made to perform swipe with justification: {arguments['justification']}. Vision model could not find coordinates for the specified item '{arguments['position']}' when swiping, be more specific or choose another item")  
                        
                        
                elif functionArguments["name"] == "press_enter":
                    justification = arguments.get("justification", "No justification provided.")
                    history.append(f"Action taken: pressing enter on keyboard. Justification: {justification}")
                    return {"action_type": "keyboard_enter"}, False, history
                elif functionArguments["name"] == "scroll":
                    justification = arguments.get("justification", "No justification provided.")
                    history.append(f"Action taken: scrolling in direction {arguments['direction']}. Justification: {justification}")
                    if arguments["direction"] == "up":
                        return {"action_type": "scroll", "direction": "up"},False,history
                    elif arguments["direction"] == "down":
                        return {"action_type": "scroll", "direction": "down"},False,history
                elif functionArguments["name"] == "go_back":
                    history.append(f"Action taken: going back. Justification: {arguments['justification']}")
                    return {"action_type": "navigate_back"},False,history
                elif functionArguments["name"] == "go_home":
                    history.append(f"Action taken: going home. Justification: {arguments['justification']}")
                    return {"action_type": "navigate_home"},False,history
                elif functionArguments["name"] == "exit":
                    history.append(f"Action taken: exiting as short term goal has been reached. Justification: {arguments['justification']}")
                    return {"action_type": "status", "goal_status": "complete"},True,history
                elif functionArguments["name"] == "give_final_answer":
                    history.append(f"Action taken: giving a final answer to an information retrieval question. Justification: {arguments['justification']}")
                    return {"action_type": "answer", "text": arguments["answer"]},True,history
                else:
                    justification = arguments.get("justification", "No justification provided.")
                    history.append(f"An invalid action '{functionArguments['name']}' was given for some reason. Justification: {justification}")
                    return {"action_type": "status", "goal_status": "infeasible"},False,history




        else:
            print("Response failed:",response.content)
            return {"action_type": "status", "goal_status": "infeasible"},False,history


































