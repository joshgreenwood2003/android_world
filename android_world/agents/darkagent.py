import base64
import time
from android_world.agents import base_agent
from android_world.agents import infer
from android_world.agents.darkagent_long_term_reasoner import LongTermReasoner
from android_world.agents.darkagent_short_term_reasoner import ShortTermReasoner
from android_world.env import interface
from android_world.env import json_action


class DarkAgent(base_agent.EnvironmentInteractingAgent):

  def __init__(
      self,
      env: interface.AsyncEnv,
      name: str = 'DarkAgent',
  ):

    super().__init__(env, name)
    self.history = []
    self.additional_guidelines = None
    self.short_term_task = None
    self.finish_criteria = None
    self.previous_screenshot = None
    

  def reset(self, go_home_on_reset: bool = False):
    super().reset(go_home_on_reset)
    self.env.hide_automation_ui()
    self.history = []

  def set_task_guidelines(self, task_guidelines: list[str]) -> None:
    self.additional_guidelines = task_guidelines
    
    
    
    
    
    
    
  def do_long_term_analysis(self, screenshot,step_data):
    response = self.long_term_reasoner.get_long_term_task(self.history,screenshot)
    completed,self.short_term_task,self.finish_criteria = response["completed"],response["task"],response["finish"]
    print("New short term task:",self.short_term_task)
    return completed
      
    

  def step(self, goal: str) -> base_agent.AgentInteractionResult:
    step_data = {
        'before_screenshot': None,
        'after_screenshot': None,
        'before_element_list': None,
        'after_element_list': None,
        'action_prompt': None,
        'action_output': None,
        'action_raw_response': None,
        'summary_prompt': None,
        'summary': None,
        'summary_raw_response': None,
    }
    
    print('----------step ' + str(len(self.history) + 1))

    state = self.get_post_transition_state()

    
    screenshot = base64.b64encode(infer.array_to_jpeg_bytes(state.pixels)).decode('utf-8')
    
    #If first loop, get a short term task from the longer task.
    if len(self.history) ==0:
      self.long_term_reasoner = LongTermReasoner(goal)
      self.short_term_reasoner = ShortTermReasoner(goal)
      completed = self.do_long_term_analysis(screenshot,step_data)
      self.previous_screenshot = screenshot
      if completed:
        return base_agent.AgentInteractionResult(True,step_data)
      
    converted_action_json,finished,self.history = self.short_term_reasoner.get_short_term_task(self.short_term_task,self.history,screenshot,self.previous_screenshot,self.finish_criteria)
    converted_action = json_action.JSONAction(**converted_action_json)
    
    #If the short term task is finished, get a new one.
    if finished:
      print("Finished step:", self.history[-1]) 
      
      if converted_action.action_type == 'answer':
        self.env.execute_action(converted_action)
        return base_agent.AgentInteractionResult(True,step_data)
      
      completed = self.do_long_term_analysis(screenshot,step_data)
      if completed:
        return base_agent.AgentInteractionResult(True,step_data)
      else:
        converted_action_json,finished,self.history = self.short_term_reasoner.get_short_term_task(self.short_term_task,self.history,screenshot,self.previous_screenshot,self.finish_criteria)
        converted_action = json_action.JSONAction(**converted_action_json)
    print("Latest step:", self.history[-1]) 
    self.previous_screenshot = screenshot
    #Perform the action
    try:
      self.env.execute_action(converted_action)
    except Exception as e:
      print(
          'Some error happened executing the action ',
          converted_action.action_type,
      )
      print(str(e))
      step_data['summary'] = (
          'Some error happened executing the action '
          + converted_action.action_type
      )
      self.history.append(step_data)

    time.sleep(10)
    return base_agent.AgentInteractionResult(
        False,
        step_data,
    )

    
