from abc import ABC, abstractmethod
import openai, os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

class Agent(ABC):
    """
    Generic agent class that defines the basic structure of an agent.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize the agent.

        Args:
            model_name (str): The name of the model.
        """
        self.model_name = model_name
        self.agent_identifier = model_name

    @abstractmethod
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation and return the action.

        Args:
            observation (str): The input string to process.

        Returns:
            str: The response generated by the agent.
        """
        pass

    
class HumanAgent(Agent):
    """
    Human agent class that allows the user to input actions manually.
    """
    def __init__(
        self, 
        model_name: str
    ):
        """
        Initialize the human agent.
        
        Args:
            model_name (str): The name of the model.
        """

        super().__init__(model_name)

    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation and return the action.
        
        Args:
            observation (str): The input string to process.
            
        Returns:
            str: The response generated by the agent.
        """
        print(observation)
        return input("Please enter the action: ")


class GPTAgent(Agent):
    """
    GPT agent class that uses the OpenRouter API to generate responses.
    """
    def __init__(
        self, 
        model_name: str
    ):
        """
        Initialize the GPT agent.
        
        Args:
            model_name (str): The name of the model.
        """
        super().__init__(model_name)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        self.client = openai.OpenAI(base_url="https://openrouter.ai/api/v1")

    
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation using the OpenAI model and return the action.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The response generated by the model.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": observation}
                ],
                # max_tokens=150, ## optional
                n=1,
                stop=None,
                temperature=0.7,
            )
            # Extract the assistant's reply
            action = response.choices[0].message.content.strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"


class HFLocalAgent(Agent):
    """
    Hugging Face local agent class that uses the Hugging Face Transformers library.
    """
    def __init__(
        self, 
        model_name: str, 
        quantize: bool = False
    ):
        """
        Initialize the Hugging Face local agent.
        
        Args:
            model_name (str): The name of the model.
            quantize (bool): Whether to load the model in 8-bit quantized format (default: False).
        """

        super().__init__(model_name)
        self.quantize = quantize
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if quantize:
            self.model = AutoModelForCausalLM.from_pretrained(model_name, load_in_8bit=True)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.pipeline = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer)
    
    def __call__(
        self, 
        observation: str
    ) -> str:
        """
        Process the observation using the Hugging Face model and return the action.
        
        Args:
            observation (str): The input string to process.
        
        Returns:
            str: The response generated by the model.
        """
        # Generate a response
        try:
            response = self.pipeline(
                observation, 
                # max_new_tokens=300, ## optional 
                num_return_sequences=1, 
                temperature=0.7, 
                return_full_text=False
            )
            # Extract and return the text output
            action = response[0]['generated_text'].strip()
            return action
        except Exception as e:
            return f"An error occurred: {e}"