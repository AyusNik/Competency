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

class GetTrainingsArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    competency_element: str = Field(description="The competency element name (ce_unit) to look up trainings for")

class CheckTrainingArgs(BaseModel):
    training_name: str = Field(description="The training name to check for mapped courses")

class GetElementReqArgs(BaseModel):
    user_id: str = Field(description="The user's MongoDB ObjectId string")
    competency_element: str = Field(description="The competency element name to get requirements for")


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


@tool("get_trainings_for_element", args_schema=GetTrainingsArgs)
async def get_trainings_for_element(user_id: str, competency_element: str) -> str:
    """Get all training names mapped to a specific competency element. Returns a list for the user to pick from."""
    return await call_mcp("get_trainings_for_element", {"user_id": user_id, "competency_element": competency_element})

@tool("check_training_has_courses", args_schema=CheckTrainingArgs)
async def check_training_has_courses(training_name: str) -> str:
    """Check if a training has any iLearn courses mapped to it. Returns has_courses=True/False."""
    return await call_mcp("check_training_has_courses", {"training_name": training_name})

@tool("check_my_odyssey_config", args_schema=UserIdArgs)
async def check_my_odyssey_config(user_id: str) -> str:
    """Check odyssey promotion tier configuration for ALL competencies assigned to the user at once."""
    return await call_mcp("check_my_odyssey_config", {"user_id": user_id})

@tool("get_my_trainings_summary", args_schema=UserIdArgs)
async def get_my_trainings_summary(user_id: str) -> str:
    """Get all trainings assigned to the user with their mapped courses grouped by competency element."""
    return await call_mcp("get_my_trainings", {"user_id": user_id})

@tool("get_element_requirements", args_schema=GetElementReqArgs)
async def get_element_requirements(user_id: str, competency_element: str) -> str:
    """Get all requirements for a competency element: PLR level, assessment types, trainings and courses."""
    return await call_mcp("get_element_requirements", {"user_id": user_id, "competency_element": competency_element})

@tool("get_my_progress_summary", args_schema=UserIdArgs)
async def get_my_progress_summary(user_id: str) -> str:
    """Get the user's progress summary: completed vs total courses and assessments."""
    return await call_mcp("get_my_progress_summary", {"user_id": user_id})

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
    get_trainings_for_element, check_training_has_courses,
    get_my_trainings_summary, get_element_requirements, get_my_progress_summary,
    check_my_odyssey_config,
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
- If the user says "cannot access", "not able to access", "can't open", "access denied", "no courses available", "no course mapped", "course not available", "no course found", "courses not found", "no courses found" → this is a NO COURSES AVAILABLE issue.
- If the user message matches the pattern: 'no courses available for training "{training}" under competency element "{element}" in competency unit "{unit}"' → this is a PRE-FILLED NO COURSES issue where all context is already known. Go directly to step 9 of the NO COURSES AVAILABLE flow using the extracted training, element and unit values.
- If the user says "completed all courses", "finished training", "done with courses" AND mentions they still cannot access an assessment → this is an ASSESSMENT ACCESS issue.
- If the user message contains any of: "cannot start", "can't start", "unable to start", "cannot create", "can't create", "cannot submit", "can't submit", "unable to submit" AND contains any of: "CPA", "PLE", "CTI", "assessment" → this is an ASSESSMENT ACCESS issue.

For course CONTENT issues:
1. Ask: "Which course is having the content issue? Please tell me the course name."
2. Wait for the course name.
3. Reply: "I can see the content for **'{course name}'** is not visible. Would you like me to raise a support ticket for this issue?"
4. If yes: call raise_ticket with issue="Course content not visible/not loading". Then reply: "✅ I've raised a support ticket for **'{course name}'**. Ticket ID: #{first 8 chars of ticket_id}. Our team will resolve it shortly."
5. If no: acknowledge and offer other help.

For NO COURSES AVAILABLE issues (user says "no courses available", "no course mapped", "cannot access", "not able to access", "can't open", "access denied", "course not available"):
1. Ask: "Which Competency Unit are you referring to? Can you tell me the name?\n> 💡 *Not sure? You can find your Competency Units listed on your MyPCP Dashboard, just below the My Odyssey section on the left panel or directly in the left bottom corner. *"
2. Wait for Competency Unit name. Do NOT call any tool yet.
3. Call validate_competency_unit with the user's answer.
   - If valid=False: reply "I couldn't find a Competency Unit matching **'{input}'** in your profile. Here are your available units: {available_units}. Could you please pick one from the list?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency unit.
4. Ask: "Which Competency Element under **'{confirmed unit}'** are you referring to?"
5. Wait for Competency Element name. Do NOT call any tool yet.
6. Call validate_competency_element with the confirmed unit and the user's answer.
   - If valid=False: reply "I couldn't find a Competency Element matching **'{input}'** under **'{confirmed unit}'**. Available elements are: {available_elements}. Could you please pick one?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency element.
7. Call get_trainings_for_element with user_id and the confirmed competency element.
   - If found=False or trainings list is empty: reply "I couldn't find any trainings mapped to **'{confirmed element}'**. Please contact your Business Line Manager." Then call get_manager_details and show full contact. Then add: "Would you like to talk to your manager directly right now? Just say **'talk to manager'**!"
   - If trainings list has items: reply "Here are the trainings available under **'{confirmed element}'**:\n{numbered list of training names}\nWhich training are you having trouble with? Please pick one from the list above."
8. Wait for the user to pick a training. IMPORTANT: The user MUST pick from the list you showed. If the user types a training name that is NOT in the list you showed, reply: "That training is not listed under **'{confirmed element}'**. Please pick one from the list I provided above." Show the list again and wait. Do NOT call any tool with an unrecognised training name.
9. Once the user picks a valid training from the list, call check_training_has_courses with that exact training name from the list.
   - If has_courses=True: reply "The training **'{training name}'** does have courses mapped to it. Please try accessing them again on the iLearn portal. If you still face issues, it may be a browser or device problem — try clearing your cache or using a different browser."
   - If has_courses=False: reply "No courses are mapped under the **'{training name}'** training for the competency element **'{confirmed element}'** under competency unit **'{confirmed unit}'**." Then call get_manager_details and show full manager contact (name, title, email, phone). Then add: "Would you like to talk to your manager directly right now in this chat? Just say **'talk to manager'** and I'll connect you instantly!"

For ASSESSMENT ACCESS issues (user cannot start/create/submit a CPA/PLE/CPI assessment):
1. Check if the user already mentioned the assessment type (CPA, PLE, or CTI) in their message. If yes, note it as confirmed_type. If not, ask: "Which type of assessment are you having trouble with? Please specify: **CPA**, **PLE**, or **CTI**."
2. Wait for assessment type if not already known.
3. Ask: "Which Competency Unit is this assessment for?\n> 💡 *Not sure? You can find your Competency Units listed on your MyPCP Dashboard, just below the My Odyssey section on the left panel or directly in the left bottom corner. *"
4. Wait for the answer. Do NOT call any tool yet.
5. Call validate_competency_unit with the user's answer.
   - If valid=False: reply "I couldn't find a Competency Unit matching **'{input}'** in your profile. Here are your available units: {available_units}. Could you please pick one from the list?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency unit.
6. Ask: "Which Competency Element under **'{confirmed unit}'** is this assessment for?"
7. Wait for the answer. Do NOT call any tool yet.
8. Call validate_competency_element with the confirmed unit and the user's answer.
   - If valid=False: reply "I couldn't find a Competency Element matching **'{input}'** under **'{confirmed unit}'**. Available elements are: {available_elements}. Could you please pick one?". Wait for a new answer and re-validate. Do NOT proceed until valid=True.
   - If valid=True: note the matched_name as the confirmed competency element.
9. Call check_assessment_access with user_id, confirmed competency_unit, confirmed competency_element.
10. Based on the result:
    - If date_locked=True: reply "The **{confirmed_type}** assessment for **'{confirmed element}'** under **'{confirmed unit}'** is currently locked. To get access or resolve this, please contact your Business Line Manager." Then call get_manager_details and display the full contact (name, title, email, phone). Then add: "Would you like to talk to your manager directly right now in this chat? Just say **'talk to manager'** and I'll connect you instantly!"
    - If courses_incomplete=True: reply "The **{confirmed_type}** assessment for **'{confirmed element}'** under **'{confirmed unit}'** is not yet accessible because your training is not complete. You have completed {completed_courses} out of {total_courses} required courses. Please complete all training courses first to unlock the assessment."
    - If date_locked=False and courses_incomplete=False: reply "The **{confirmed_type}** assessment for **'{confirmed element}'** under **'{confirmed unit}'** is accessible. Please try opening it again on the iLearn portal. If you still face issues, it may be a browser or device problem — try clearing your cache or using a different browser." Do NOT show manager details in this case.

For ODYSSEY / PROMOTION issues (user says odyssey not visible, promotion not showing, career path blank, etc.):
1. Immediately call check_my_odyssey_config with user_id. Do NOT ask the user for any competency name first.
2. If all_configured=True: reply EXACTLY with the display_message from the tool and stop.
3. If not_configured list is not empty: reply using this EXACT format — do not skip any part:

   First line: "Your **My Odyssey** section tracks your career progression and promotion path on the MyPCP platform."
   Second line: Show the display_message from the tool EXACTLY as returned.
   Third line: "To get your Odyssey configured, your PSD Manager needs to set up the promotion tiers for your competency. Please reach out to them using the details below."
   Then show: **Your PSD Manager:**
   - 👤 **Name:** {manager_name}
   - 📧 **Email:** {manager_email}
   - 📞 **Phone:** {manager_phone}
   Final line: "Would you like to talk to your PSD Manager directly right now in this chat? Just say **'talk to manager'** and I'll connect you instantly!"

Do NOT skip steps. Do NOT call tools before collecting all required info. Be concise and helpful. Never make up data — always use tools.

For GENERAL INFORMATION queries (user asks about their data, not reporting an issue):

- "how many trainings", "what trainings", "show my trainings", "list trainings" → call get_my_trainings_summary. Reply with a structured list: for each competency element, show the training name(s) and the courses under each. End with the total training count.

- "how many courses", "what courses", "show my courses", "list courses" → call get_my_courses. Reply with a list of all course titles grouped by competency element.

- "how many assessments", "what assessments", "show my assessments" → call get_my_assessments. Reply with a list of all assessment titles.

- "requirements for [element]", "what are the requirements", "how many requirements", "PLR for [element]" → Ask: "Which Competency Element are you asking about?" if not already mentioned. Then call get_element_requirements. Reply showing: PLR Level, Assessment Types required (e.g. CPA, PLE), Training(s) assigned, and Courses under each training.

- "my progress", "how many completed", "what have I completed" → call get_my_progress_summary. Reply showing completed courses vs total and completed assessments.

- "my competencies", "what competencies do I have" → call get_my_competencies. List them.

- "my profile", "who am I", "my details" → call get_user_profile. Show name, email, job title.

For any other general question about the user's data, use the most relevant tool available. Never say you don't have access to data — always try a tool first."""


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
