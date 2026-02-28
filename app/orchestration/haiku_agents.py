import os 
from dotenv import load_dotenv, find_dotenv
from agents import Agent, Runner
from pydantic import BaseModel
import asyncio


class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int
    

class HaikuAgents:
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
        self.__knowledge_path = os.path.join(self.__path, 'knowledge')
        load_dotenv(find_dotenv())
        self.__create_agents()
    
    def __get_knowledge(self, filename):
        if not filename.endswith('.md'):
            filename += '.md'
        filepath = os.path.join(self.__knowledge_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Knowledge file {filepath} not found.") 
        with open(filepath, 'r') as file:
            return file.read()
    
    def __create_agents(self):
        # evaluator agent
        self.evaluator = Agent(
            name="Haiku Evaluator",
            instructions=(
                "You are a strict but helpful haiku reviewer. "
                "Evaluate a haiku written for a given subject according to haiku conventions. "
                "Check that the poem has exactly three lines, uses concise and concrete imagery, "
                "captures a single moment of perception, and approximately follows the 5–7–5 "
                "syllable pattern. Avoid abstraction, moral judgment, and explanation. "
                "Return a score from 0 to 10, brief bullet-point feedback, and if the score is "
                "below 7, propose a revised haiku that better follows the rules while preserving "
                "the original subject."
            ) ,
            output_type = HaikuResponse,
            model="gpt-4.1-mini"
            )
        # writer agent
        self.writer = Agent(
            name="Haiku Writer", 
            instructions="You are a haiku poem writer." + self.__get_knowledge('haiku_writer'),
            output_type = HaikuResponse,
            handoffs=[self.evaluator],
            model= "gpt-4.1-mini"
            ) 
    
    async def run(self, subject):
        prompt = "Write a haiku about." + subject 
        result = await Runner.run(self.writer, prompt) 
        return result.final_output
    
    def run_sync(self, subject):
        return asyncio.run(self.run(subject))
        