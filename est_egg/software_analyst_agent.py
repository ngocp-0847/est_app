from typing import List, Dict, Optional
from pydantic import Field
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator
import instructor
import openai
import os

class SoftwareAnalysisInputSchema(BaseIOSchema):
    """
    Schema for the input to the software analysis agent.
    """
    requirement: Optional[str] = Field(default=None, description="Software requirement or feature description to analyze.")

class TaskBreakdown(BaseIOSchema):
    """Schema for a single task in the breakdown."""
    task_name: Optional[str] = Field(default=None, description="Name of the task")
    description: Optional[str] = Field(default=None, description="Detailed description of the task")
    difficulty: Optional[str] = Field(default=None, description="Difficulty level: Easy, Medium, Hard")
    time_estimate: Optional[str] = Field(default=None, description="Estimated time to complete (e.g., '2-4 hours', '1-2 days')")

class APIEndpoint(BaseIOSchema):
    """Schema for API endpoint analysis."""
    endpoint: Optional[str] = Field(default=None, description="API endpoint path")
    method: Optional[str] = Field(default=None, description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    purpose: Optional[str] = Field(default=None, description="Purpose of this endpoint")
    request_params: Optional[Dict[str, str]] = Field(default=None, description="Request parameters or body structure")
    response_structure: Optional[Dict[str, str]] = Field(default=None, description="Expected response structure")

class ERDEntity(BaseIOSchema):
    """Schema for ERD entity analysis."""
    entity_name: Optional[str] = Field(default=None, description="Name of the entity")
    attributes: Optional[Dict[str, str]] = Field(default=None, description="Attributes with their data types")
    relationships: Optional[List[str]] = Field(default=None, description="Relationships with other entities")

class SoftwareAnalysisOutputSchema(BaseIOSchema):
    """
    Schema for the output from the software analysis agent.
    """
    summary: Optional[str] = Field(default=None, description="Summary of the analysis for the requirement.")
    task_breakdown: Optional[List[TaskBreakdown]] = Field(default=[], description="Detailed breakdown of tasks needed to implement the requirement.")
    total_estimate: Optional[str] = Field(default=None, description="Total estimated time to complete all tasks.")
    api_analysis: List[APIEndpoint] = Field(default=[], description="Analysis of required API endpoints.")
    erd_analysis: List[ERDEntity] = Field(default=[], description="Analysis of required database entities and relationships.")
    risks_and_considerations: Optional[List[str]] = Field(default=[], description="Potential risks and considerations for implementation.")
    suggested_questions: Optional[List[str]] = Field(default=[], description="Suggested follow-up questions for further analysis.")

# Set up the system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "You are an expert software analyst with deep knowledge of software development processes.",
        "You specialize in breaking down requirements, estimating development time, and analyzing architectural components.",
        "You understand APIs, databases, and modern software development practices.",
        "Your estimates are realistic and include buffer time for testing and edge cases."
    ],
    steps=[
        "Analyze the requirement to understand the scope and complexity.",
        "Break down the requirement into specific implementable tasks.",
        "Estimate time for each task based on complexity and possible challenges.",
        "Design necessary API endpoints with detailed specifications.",
        "Identify database entities and their relationships needed for the feature.",
        "Highlight potential risks and considerations.",
        "Suggest follow-up questions to clarify any ambiguities."
    ],
    output_instructions=[
        "Provide a concise summary of your understanding of the requirement.",
        "Break down tasks with realistic time estimates.",
        "Be specific about API designs including endpoints, methods, and data structures.",
        "Include detailed ERD analysis with entities, attributes, and relationships.",
        "Highlight any risks or special considerations for implementation.",
        "Suggest 3-5 relevant follow-up questions for further clarification."
    ]
)

api_key = os.environ.get("OPENAI_API_KEY")
print('api_key', api_key)

# Initialize the agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=api_key)),
        model="gpt-4o",
        system_prompt_generator=system_prompt_generator,
        input_schema=SoftwareAnalysisInputSchema,
        output_schema=SoftwareAnalysisOutputSchema
    )
)

# Example requirement
requirement = "Implement a user authentication system with registration, login, password reset, and OAuth integration with Google and Facebook."
input_data = SoftwareAnalysisInputSchema(requirement=requirement)

# Use the agent
response = agent.run(input_data)

# Display the results
print(f"Summary: {response.summary}\n")

print("Task Breakdown:")
for task in response.task_breakdown:
    print(f"- {task.task_name} ({task.difficulty}): {task.description}")
    print(f"  Estimate: {task.time_estimate}\n")

print(f"Total Estimate: {response.total_estimate}\n")

print("API Analysis:")
for api in response.api_analysis:
    print(f"- {api.method} {api.endpoint}: {api.purpose}")
    print(f"  Request: {api.request_params}")
    print(f"  Response: {api.response_structure}\n")

print("ERD Analysis:")
for entity in response.erd_analysis:
    print(f"- Entity: {entity.entity_name}")
    print(f"  Attributes: {entity.attributes}")
    print(f"  Relationships: {entity.relationships}\n")

print("Risks and Considerations:")
for risk in response.risks_and_considerations:
    print(f"- {risk}")

print("\nSuggested Questions:")
for question in response.suggested_questions:
    print(f"- {question}")
