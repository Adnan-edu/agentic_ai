from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage


class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")

class TrendingCompanyList(BaseModel):
    """ List of multiple trending companies that are in the news """
    companies: List[TrendingCompany] = Field(description="List of companies trending in the news")


# The TrendingCompanyResearch model defines the structure for detailed research on a company.
# It includes fields for the company name, market position, future outlook, and investment potential.
# By specifying these fields and their descriptions, we guide the agent to produce structured and comprehensive research responses.
# This approach ensures the agent's output is consistent and contains all necessary information for investment analysis.

class TrendingCompanyResearch(BaseModel):
    """ Detailed research on a company """
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")

class TrendingCompanyResearchList(BaseModel):
    """ A list of detailed research on all the companies """
    research_list: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # We enable memory for trending_company_finder and stock_picker because:
    # - trending_company_finder benefits from remembering previously found companies to avoid duplicates and track trends over time.
    # - stock_picker needs memory to recall past decisions and notifications, ensuring consistent investment logic and user communication.
    # We do NOT enable memory for financial_researcher because its role is to perform fresh, stateless research on the provided companies each time, without needing to recall previous research sessions.
    
    # When deciding whether to add or remove memory from an agent, consider the following questions:
    # 1. Does the agent need to recall information from previous runs or sessions to perform its task effectively?
    # 2. Will remembering past outputs, decisions, or discovered data improve the agent's performance or avoid redundancy?
    # 3. Is the agent's role inherently stateless, requiring only the current input to generate its output?
    # 4. Could enabling memory introduce unwanted bias or stale information into the agent's reasoning?
    # 5. Does the agent need to track user interactions, historical context, or evolving knowledge over time?
    # 6. Is there a privacy or resource concern with storing and recalling past data for this agent?
    # 7. Will memory help the agent coordinate or collaborate better with other agents in the crew?

    @agent
    def trending_company_finder(self) -> Agent:
        # Memory is enabled because this agent benefits from recalling previously found companies to avoid duplicates and track trends.
        return Agent(config=self.agents_config['trending_company_finder'],
                     tools=[SerperDevTool()], memory=True)
    
    @agent
    def financial_researcher(self) -> Agent:
        # Memory is NOT enabled because this agent should perform fresh, stateless research each time.
        return Agent(config=self.agents_config['financial_researcher'], 
                     tools=[SerperDevTool()])

    @agent
    def stock_picker(self) -> Agent:
        # Memory is enabled because this agent needs to recall past decisions and notifications for consistent investment logic.
        return Agent(config=self.agents_config['stock_picker'], 
                     tools=[PushNotificationTool()], memory=True
                     )
    
    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
        )
    



    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        # We create the manager agent separately here because the Crew requires a dedicated manager_agent
        # parameter, which is responsible for overseeing and delegating tasks among other agents.
        # By instantiating the manager agent explicitly, we can set specific options (like allow_delegation=True)
        # and ensure that the manager's configuration is distinct from the other agents in the crew.
        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )
            
        return Crew(
            # List of agent instances to be used by the Crew
            # There are 3 agents in the crew:
            # 1. trending_company_finder: Finds trending companies in the news
            # 2. financial_researcher: Researches trending companies
            # 3. stock_picker: Picks the best company for investment
            agents=self.agents,
            # List of task instances to be performed by the Crew
            tasks=self.tasks, 
            # Use hierarchical process: LLM determines which agent does which task based on the task description
            process=Process.hierarchical, # Assign the LLM to figure which agent does what task based on the task description
            # Enable verbose output for debugging and transparency
            verbose=True,
            # Assign a manager agent to oversee and delegate tasks
            manager_agent=manager,
            # Enable memory for the Crew (required for persistent and contextual operations)
            memory=True,
            # Long-term memory for persistent storage across sessions
            long_term_memory = LongTermMemory(
                # Use SQLite storage backend for long-term memory
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            # Short-term memory for current context using Retrieval-Augmented Generation (RAG)
            short_term_memory = ShortTermMemory(
                storage = RAGStorage(
                        # Configure the embedder for RAG storage using OpenAI embeddings
                        embedder_config={
                            "provider": "openai",
                            "config": {
                                "model": 'text-embedding-3-small'
                            }
                        },
                        # Specify this storage as short-term memory
                        type="short_term",
                        # Path to store short-term memory data
                        path="./memory/"
                    )
                ),
            # Entity memory for tracking key information about entities (e.g., companies)
            entity_memory = EntityMemory(
                storage=RAGStorage(
                    # Configure the embedder for entity memory using OpenAI embeddings
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": 'text-embedding-3-small'
                        }
                    },
                    # Specify this storage as short-term memory for entities
                    type="short_term",
                    # Path to store entity memory data
                    path="./memory/"
                )
            ),
        )
