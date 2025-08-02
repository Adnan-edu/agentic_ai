from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input is needed from the user, or clarifications, or the assistant is stuck")


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        # Create a new ChatOpenAI instance for the evaluator role
        # This LLM will be responsible for evaluating whether the worker's responses meet the success criteria
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Configure the evaluator LLM to output structured data using the EvaluatorOutput schema
        # This ensures the evaluator returns feedback, success status, and whether user input is needed
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is the success criteria:
    {state['success_criteria']}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """
        
        # This condition checks if the evaluator has provided feedback on a previous attempt
        # The state['feedback_on_work'] is set by the evaluator node when it determines
        # that the success criteria has not been met and provides specific feedback
        # on what needs to be improved or corrected in the worker's response
        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state['feedback_on_work']}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
        
        # Add in the system message

        # Flag to track if we found an existing system message in the conversation
        found_system_message = False
        
        # Get the current conversation messages from the state
        messages = state["messages"]
        
        # Iterate through all messages in the conversation to look for existing system messages
        for message in messages:
            # Check if the current message is a SystemMessage type
            if isinstance(message, SystemMessage):
                # Update the existing system message with our new system_message content
                # This ensures the system message contains the latest success criteria and feedback
                message.content = system_message
                # Mark that we found and updated an existing system message
                found_system_message = True
        
        # If no existing system message was found in the conversation
        if not found_system_message:
            # Create a new SystemMessage with our updated content and prepend it to the messages list
            # We prepend it (add to beginning) because system messages should come first in the conversation
            # This ensures the LLM receives the system instructions before processing user messages
            messages = [SystemMessage(content=system_message)] + messages
        
        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)
        
        # Return updated state
        return {
            "messages": [response],
        }


    def worker_router(self, state: State) -> str:
        # Get the most recent message from the conversation history
        # This is the last message that was added to the state's messages list
        last_message = state["messages"][-1]
        
        # Check if the last message has tool_calls attribute and if it contains any tool calls
        # Tool calls indicate that the LLM wants to use tools (like file operations, web search, etc.)
        # This happens when the LLM determines it needs to perform actions to complete the task
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # If there are tool calls, route to the "tools" node
            # The tools node will execute the requested tools (like writing files, searching web, etc.)
            return "tools"
        else:
            # If there are no tool calls, route to the "evaluator" node
            # The evaluator will assess whether the current response meets the success criteria
            # or if more work/user input is needed to complete the task
            return "evaluator"
        
    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation
        
    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = f"""You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user."""
        
        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

    The entire conversation with the assistant, with the user's original request and all replies, is:
    {self.format_conversation(state['messages'])}

    The success criteria for this assignment is:
    {state['success_criteria']}

    And the final response from the Assistant that you are evaluating is:
    {last_response}

    Respond with your feedback, and decide if the success criteria is met by this response.
    Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

    The Assistant has access to a tool to write files. If the Assistant says they have written a file, then you can assume they have done so.
    Overall you should give the Assistant the benefit of the doubt if they say they've done something. But you should reject if you feel that more work should go into this.

    """
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."
        
        evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [{"role": "assistant", "content": f"Evaluator Feedback on this answer: {eval_result.feedback}"}],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"


    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        # Add conditional edges from worker node - routes to either tools or evaluator based on worker_router logic
        graph_builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
        
        # Add direct edge from tools back to worker - tools always return to worker after execution
        graph_builder.add_edge("tools", "worker")
        
        # Add conditional edges from evaluator node - routes to either worker (for retry) or END based on evaluation results
        graph_builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END})
        
        # Add entry point - graph starts at the worker node
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    
    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False
        }
        result = await self.graph.ainvoke(state, config=config)
        # Create a user message object with the original user input
        # This represents the user's request that was processed by the graph
        user = {"role": "user", "content": message}
        
        # Extract the assistant's main response from the result messages
        # result["messages"][-2] gets the second-to-last message, which is the worker's final response
        # This contains the main answer or solution to the user's request
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        
        # Extract the evaluator's feedback from the result messages
        # result["messages"][-1] gets the last message, which is the evaluator's assessment
        # This contains feedback about whether the success criteria were met and any additional comments
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]
    
    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
