from dotenv import load_dotenv

from langchain_core.messages import HumanMessage,SystemMessage
from langchain_openai import ChatOpenAI

from android_world.agents.darkagent_system_prompts import generate_long_term_prompt, get_long_term_parser

load_dotenv()


class LongTermReasoner:
    def __init__(self,long_term_task):
        
        self.text_content = generate_long_term_prompt(
        long_term_task=long_term_task
        )

        self.messages = [
            SystemMessage(self.text_content)
        ] 
        self.model = ChatOpenAI(model="gpt-4.1")
        self.chain = self.model | get_long_term_parser()


    def get_long_term_task(self, history, screenshot):
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "\n".join(f"{i + 1}. {item}" for i, item in enumerate(history))},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot}", "detail": "high"}
                },
            ],
        )
        self.messages.append(message)
        
        success = False
        while not success:
            try:
                response = self.chain.invoke(self.messages)
                success = True
            except:
                print("Error in getting new task, retrying")
                continue
        return response
    