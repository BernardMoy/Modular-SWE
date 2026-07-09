from .agent_prompts.analyzer import get_analyzer_prompt
from .agent_prompts.decomposer import get_decomposer_prompt
from .agent_prompts.coders.modular_coder import get_modular_coder_prompt
from .agent_prompts.coders.all_at_once_coder import get_all_at_once_coder_prompt
from .agent_prompts.coders.no_design_coder import get_no_design_coder_prompt
 
def get_prompt(agent_name, *args):
    # Given the agent name and a variable number of arguments. 
    # Return the prompt for these agents 
    # (You need to have the correct number of arguments).  

    # For agent_name, the corresponding function to get its prompt is 
    # get_[agent_name]_prompt. 

    if agent_name == "analyzer": 
        return get_analyzer_prompt(*args) 
    elif agent_name == "decomposer": 
        return get_decomposer_prompt(*args) 
    elif agent_name == "modular_coder": 
        return get_modular_coder_prompt(*args) 
    elif agent_name == "all_at_once_coder": 
        return get_all_at_once_coder_prompt(*args)
    elif agent_name == "no_design_coder": 
        return get_no_design_coder_prompt(*args)
    else: 
        # none match, throw error 
        raise Exception(f"Invalid agent name: {agent_name}")