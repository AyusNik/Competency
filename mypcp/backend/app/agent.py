from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from fastmcp import Client
import json, os
from dotenv import load_dotenv

load_dotenv()

MCP_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003/mcp")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")


# ── Call MCP tool via FastMCP Client ─────────────────────────

async def call_mcp(tool_name: str, arguments: dict) -> str:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(tool_name, arguments)
        content = result.content if hasattr(result, "content") else result
        if content and hasattr(content[0], 'text'):
            return content[0].text
        return json.dumps(content) if content else "{}"


# ── Tool schemas ──────────────────────────────────────────────

class UserIdArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")

class CheckCourseArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    course_title: str = Field(description="Partial or full course title to check")

class RaiseTicketArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    course_title: str = Field(description="The course title the ticket is for")
    issue: str = Field(description="Description of the issue")


class CheckAssessmentArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    competency_unit: str = Field(description="The competency unit name provided by the user")
    competency_element: str = Field(description="The competency element name provided by the user")


class ValidateUnitArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    competency_unit: str = Field(description="The competency unit name to validate")

class ValidateElementArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    competency_unit: str = Field(description="The already-validated competency unit name")
    competency_element: str = Field(description="The competency element name to validate")


class CheckOdysseyArgs(BaseModel):
    competency_name: str = Field(description="The competency name to check odyssey configuration for")


# ── LangChain tools ───────────────────────────────────────────

@tool("get_user_profile", args_schema=UserIdArgs)
async def get_user_profile(user_id: str) -> str:
    """Get the profile of a user (name, job title, email)."""
    return await call_mcp("get_user_profile", {"user_id": user_id})

@tool("get_my_competencies", args_schema=UserIdArgs)
async def get_my_competencies(user_id: str) -> str:
    """Get all competencies assigned to the user."""
    return await call_mcp("get_my_competencies", {"user_id": user_id})

@tool("get_my_courses", args_schema=UserIdArgs)
async def get_my_courses(user_id: str) -> str:
    """Get all iLearn courses assigned to the user via competency mappings."""
    return await call_mcp("get_my_courses", {"user_id": user_id})

@tool("get_my_assessments", args_schema=UserIdArgs)
async def get_my_assessments(user_id: str) -> str:
    """Get all iLearn assessments assigned to the user via competency mappings."""
    return await call_mcp("get_my_assessments", {"user_id": user_id})

@tool("check_course_assigned", args_schema=CheckCourseArgs)
async def check_course_assigned(user_id: str, course_title: str) -> str:
    """Check if a specific course (by partial title) is assigned to the user."""
    return await call_mcp("check_course_assigned", {"user_id": user_id, "course_title": course_title})

@tool("validate_competency_unit", args_schema=ValidateUnitArgs)
async def validate_competency_unit(user_id: str, competency_unit: str) -> str:
    """Validate that a competency unit name exists in the user's assigned competencies. Returns valid=True with matched name, or valid=False with available unit names."""
    return await call_mcp("validate_competency_unit", {"user_id": user_id, "competency_unit": competency_unit})

@tool("validate_competency_element", args_schema=ValidateElementArgs)
async def validate_competency_element(user_id: str, competency_unit: str, competency_element: str) -> str:
    """Validate that a competency element exists under the given unit. Returns valid=True with matched name, or valid=False with available element names."""
    return await call_mcp("validate_competency_element", {"user_id": user_id, "competency_unit": competency_unit, "competency_element": competency_element})


@tool("check_assessment_access", args_schema=CheckAssessmentArgs)
async def check_assessment_access(user_id: str, competency_unit: str, competency_element: str) -> str:
    """Check whether the assessment for a specific competency unit/element has a release date blocking access. Returns date_locked and release_date."""
    return await call_mcp("check_assessment_access", {"user_id": user_id, "competency_unit": competency_unit, "competency_element": competency_element})


@tool("check_odyssey_config", args_schema=CheckOdysseyArgs)
async def check_odyssey_config(competency_name: str) -> str:
    """Check if a competency has promotion_from and promotion_to configured for the Odyssey tracker."""
    return await call_mcp("check_odyssey_config", {"competency_name": competency_name})


@tool("get_manager_details", args_schema=UserIdArgs)
async def get_manager_details(user_id: str) -> str:
    """Get the Business Line Manager contact details for the user."""
    return await call_mcp("get_manager_details", {"user_id": user_id})


@tool("raise_ticket", args_schema=RaiseTicketArgs)
async def raise_ticket(user_id: str, course_title: str, issue: str) -> str:
    """Raise a support ticket for a user regarding a course content issue."""
    return await call_mcp("raise_ticket", {"user_id": user_id, "course_title": course_title, "issue": issue})


AGENT_TOOLS = [
    get_user_profile, get_my_competencies, get_my_courses,
    get_my_assessments, check_course_assigned, validate_competency_unit,
    validate_competency_element, check_assessment_access,
    get_manager_details, raise_ticket, check_odyssey_config,
]
TOOLS_BY_NAME = {t.name: t for t in AGENT_TOOLS}


# ── LangGraph state ───────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str


SYSTEM_PROMPT = """You are a helpful assistant for the MyPCP (Personal Competency Portal) platform.
You help users with questions about their competencies, courses, assessments, and any access issues.

Always use the user_id from the context when calling tools.

DETECTING ISSUE TYPE:
- If the user says "cannot see content", "content not visible", "video not loading", "content not showing", "not able to see the content" → this is a CONTENT issue.
- If the user says "cannot access", "not able to access", "can't open", "access denied" → this is an ACCESS issue.
- If the user says "completed all courses", "finished training", "done with courses" AND mentions they still cannot access an assessment → this is an ASSESSMENT ACCESS issue.

For course CONTENT issues:
1. Ask: "Which course is having the content issue? Please tell me the course name."
2. Wait for the course name.
3. Reply: "I can see the content for **'{course name}'** is not visible. Would you like me to raise a support ticket for this issue?"
4. If yes: call raise_ticket with issue="Course content not visible/not loading". Then reply: "✅ I've raised a support ticket for **'{course name}'**. Ticket ID: #{first 8 chars of ticket_id}. Our team will resolve it shortly."
5. If no: acknowledge and offer other help.

For course ACCESS issues:
1. Ask: "Which course are you having trouble accessing? Can you tell me the Competency Unit name?"
2. Wait for Competency Unit name. Do NOT call any tool yet.
3. Call validate_competency_unit with the user's answer.
   - If valid=False: reply "I couldn't find a Competency Unit matching **'{input}'** in your profile. Here are your available units: {available_units}. Could you please pick one from the list?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency unit.
4. Ask: "Can you tell me the Competency Element name under **'{confirmed unit}'**?"
5. Wait for Competency Element name. Do NOT call any tool yet.
6. Call validate_competency_element with the confirmed unit and the user's answer.
   - If valid=False: reply "I couldn't find a Competency Element matching **'{input}'** under **'{confirmed unit}'**. Available elements are: {available_elements}. Could you please pick one?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency element.
7. Ask: "Can you tell me the training course name?"
8. Wait for training course name.
9. Call check_course_assigned with the training course name.
10. If available=False: say the course is currently unavailable, call get_manager_details, show full manager contact, add: "If you'd like, you can also talk to your manager one-on-one directly in this chat — just say **'talk to manager'**!"
11. If assigned=True and available=True: tell the user "Great news! The course **'{course name}'** is fully accessible and available for you in the system. Please try opening it again on the iLearn portal. If you still face issues, it may be a browser or device problem — try clearing your cache or using a different browser." Do NOT provide manager details in this case.
12. If assigned=False: say the course is not assigned to them and they should contact their manager.

For ASSESSMENT ACCESS issues (user completed all training courses but assessment is still locked):
1. Ask: "Which Competency Unit are you trying to access the assessment for?"
2. Wait for the answer. Do NOT call any tool yet.
3. Call validate_competency_unit with the user's answer.
   - If valid=False: reply "I couldn't find a Competency Unit matching **'{input}'** in your profile. Here are your available units: {available_units}. Could you please pick one from the list?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency unit.
4. Ask: "And what is the Competency Element name under **'{confirmed unit}'**?"
5. Wait for the answer. Do NOT call any tool yet.
6. Call validate_competency_element with the confirmed unit and the user's answer.
   - If valid=False: reply "I couldn't find a Competency Element matching **'{input}'** under **'{confirmed unit}'**. Available elements are: {available_elements}. Could you please pick one?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency element.
7. Only after BOTH are confirmed valid, call check_assessment_access with user_id, confirmed competency_unit, confirmed competency_element.
8. Regardless of the result, reply: "I can see you've completed all the required training courses — great work! However, the assessment for **'{confirmed competency_element}'** is currently not accessible. To get this issue resolved, you will need to connect with your manager. Here are your manager's details:"
   Then call get_manager_details and display the full contact (name, title, email, phone).
   Then ask: "Would you like to talk to your manager directly right now in this chat? Just say **'talk to manager'** and I'll connect you instantly!"

For ODYSSEY / PROMOTION issues (user says odyssey not visible, promotion not showing, career path blank, etc.):
1. Ask: "Which competency are you referring to? (e.g. DSA)"
2. Wait for the competency name.
3. Call check_odyssey_config with the competency name.
4. If found=False: reply "I couldn't find a competency named **'{name}'** in the system. Please check the name and try again."
5. If found=True and configured=True: reply "Your Odyssey for **'{competency}'** is configured: **{promotion_from}** → **{promotion_to}**. If it's still not showing on your dashboard, please try refreshing the page. If the issue persists, contact support."
6. If found=True and configured=False: reply "The promotion path for **'{competency}'** has not been configured yet in the system. You'll need to contact your manager to get this set up." Then call get_manager_details and show full contact. Then add: "Would you like to talk to your manager directly right now? Just say **'talk to manager'**!"

Do NOT skip steps. Do NOT call tools before collecting all required info. Be concise and helpful. Never make up data — always use tools."""


def build_agent():
    llm = ChatBedrockConverse(
        model=MODEL_ID,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    ).bind_tools(AGENT_TOOLS)

    async def call_model(state: AgentState):
        system = SYSTEM_PROMPT + f"\n\nCurrent user_id: {state['user_id']}"
        response = await llm.ainvoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [response]}

    async def call_tools(state: AgentState):
        last = state["messages"][-1]
        results = []
        for tc in last.tool_calls:
            t = TOOLS_BY_NAME.get(tc["name"])
            if t:
                result = await t.ainvoke(tc["args"])
            else:
                result = json.dumps({"error": f"Tool '{tc['name']}' is not available."})
            results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        return {"messages": results}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", call_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def get_agent():
    return build_agent()
