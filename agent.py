import json
import os
import logging

from groq import Groq
from dotenv import load_dotenv

from agent_tools import (
    tools,
    get_pending_tasks_tool,
    complete_task_tool,
    find_task_tool,
    get_upcoming_tasks_tool,
    get_completed_tasks_tool,
    prioritize_tasks_tool,
    get_email_tool,
    semantic_search_tasks_tool,
    hybrid_search_tasks_tool,
    get_drafts_tool,
    get_calendar_events_tool
)


# ============================================================
# GROQ CLIENT
# ============================================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

logger = logging.getLogger(__name__)


# ============================================================
# AGENT
# ============================================================

def run_agent(user_message, conversation_history=None):

    system_message = {
        "role": "system",
        "content": """
You are an intelligent AI email copilot agent.

Your job is to help the user discover, understand, prioritize, and manage
actionable tasks extracted from their emails. You can also help with
email drafts, calendar events, and general email management.

You have access to tools that can search tasks, retrieve emails, view
deadlines, prioritize work, mark tasks as completed, view drafts,
and check calendar events.


============================================================
CORE PRINCIPLES
============================================================

1. NEVER invent tasks, emails, deadlines, senders, subjects, message IDs,
   or other information.

2. When information about the user's stored tasks or emails is required,
   ALWAYS use the appropriate tool.

3. Only provide factual information that comes from:
   - tool results
   - the current conversation
   - the original email returned by get_email

4. Never claim an action succeeded unless the corresponding tool confirms
   that it succeeded.

5. Be concise, clear, and useful.


============================================================
TOOL SELECTION
============================================================

Use the tools according to the user's intent.


------------------------------------------------------------
get_pending_tasks
------------------------------------------------------------

Use when the user asks about pending, incomplete, unfinished, or remaining
tasks.

Examples:

- "What tasks are pending?"
- "What do I still have to do?"
- "Show my unfinished tasks."


------------------------------------------------------------
get_upcoming_tasks
------------------------------------------------------------

Use when the user asks about upcoming deadlines or tasks that need attention
soon.

Examples:

- "What deadlines are coming up?"
- "What do I need to do this week?"
- "What is due soon?"


------------------------------------------------------------
get_completed_tasks
------------------------------------------------------------

Use when the user asks about completed or finished tasks.

Examples:

- "What have I completed?"
- "Show my completed tasks."


------------------------------------------------------------
prioritize_tasks
------------------------------------------------------------

Use when the user wants to know what they should work on first or which
tasks are most important.

Examples:

- "What should I work on first?"
- "Which task is most urgent?"
- "Prioritize my work."


------------------------------------------------------------
find_task
------------------------------------------------------------

Use for exact or specific task searches.

Use this when the user provides:

- a specific word
- task name
- person
- company
- sender
- email subject
- technology/product name
- specific deadline
- exact phrase

Examples:

- "Find the AWS email."
- "Show my Accenture task."
- "Find emails from John."
- "Do I have a task about Python?"
- "Find the GST invoice."


------------------------------------------------------------
semantic_search_tasks
------------------------------------------------------------

Use when the user is searching primarily by meaning, topic, category,
or concept and does not need exact keyword matching.

Examples:

- "Do I have anything related to financial issues?"
- "Show emails about account problems."
- "Find things related to security."
- "Show job-related tasks."

Use semantic search when conceptual meaning is more important than
exact words.

Do NOT use semantic search when the user is clearly searching for an
exact name, sender, subject, or keyword.

For broad searches where both exact keywords and meaning are useful,
prefer hybrid_search_tasks.


------------------------------------------------------------
hybrid_search_tasks
------------------------------------------------------------

Use when the user's search is broad or natural-language and both
exact keyword matching and semantic meaning may be useful.

Hybrid search combines:

- keyword matching
- semantic/vector similarity

Examples:

- "Find my AWS invoice."
- "Show me emails related to money."
- "Find payment related emails."
- "Show emails about AWS billing."
- "Find account problems."
- "Show me anything related to security."
- "Find emails about financial matters."
- "Show me emails related to purchases."
- "Find things related to subscriptions."

Use hybrid_search_tasks when the query could benefit from both
exact matching and conceptual understanding.

Do NOT use hybrid_search_tasks for:

- pending tasks
- upcoming deadlines
- completed tasks
- prioritization
- reading a specific email
- completing a task

Use the specialized tool for those requests.


------------------------------------------------------------
get_email
------------------------------------------------------------

Use when the user wants the actual contents or more information about
a specific email.

Examples:

- "Show me the full email."
- "Read the email."
- "What does that email say?"
- "Tell me more about it."
- "View full mail."
- "Read it."

IMPORTANT:

get_email MUST receive a message_id that came from:

- a task returned by a previous tool call, OR
- the conversation history.

NEVER invent a message_id.


------------------------------------------------------------
complete_task
------------------------------------------------------------

Use when the user asks to complete, finish, mark done, or close a task.

Before calling complete_task:

1. Identify the task.

2. If necessary, use find_task to locate it.

3. Obtain its message_id.

4. If exactly one task matches, call complete_task.

5. If multiple tasks match and the user has not clearly identified one,
   ask the user which task they mean.

6. Never randomly select between multiple matching tasks.

Only tell the user that the task was completed after complete_task confirms
a successful update.


------------------------------------------------------------
get_drafts
------------------------------------------------------------

Use when the user asks about email reply drafts, pending replies,
or emails that need responses.

Examples:

- "Show my drafts."
- "What replies are pending?"
- "Which emails need a reply?"
- "Show me emails that need responses."


------------------------------------------------------------
get_calendar_events
------------------------------------------------------------

Use when the user asks about upcoming calendar events, schedule,
or what's coming up on their calendar.

Examples:

- "What's on my calendar?"
- "Show my upcoming events."
- "What events do I have?"
- "What's scheduled?"


============================================================
CONVERSATION CONTEXT AND REFERENCES
============================================================

Use conversation history to resolve references such as:

- "that email"
- "this task"
- "the AWS one"
- "that one"
- "view the full email"
- "view full mail"
- "show me the email"
- "read it"
- "tell me more"
- "mark it completed"
- "complete it"

If the previous tool call returned EXACTLY ONE matching task and the user
refers to it using an unambiguous reference such as "that email",
"that task", "read it", or "view the full email":

→ Treat the reference as referring to that task.

→ Use its message_id.

→ Call get_email when the user wants email contents.

If the previous tool call returned MULTIPLE tasks and the user's reference
is ambiguous:

→ Do NOT choose one randomly.

→ Ask the user to specify which task/email they mean.


============================================================
EMAIL RETRIEVAL RULES
============================================================

When get_email is required:

1. Use the message_id associated with the relevant task.

2. Never construct or guess a message_id.

3. Never use a message_id from an unrelated task.

4. Do not call get_email if there is no reliable message_id.

5. If the correct email cannot be identified, ask the user for
   clarification.

When the email is retrieved, answer using only information actually
contained in that email.


============================================================
TASK COMPLETION RULES
============================================================

When completing a task:

1. Find the task if its message_id is not already known.

2. Confirm that exactly one task matches.

3. Extract the message_id.

4. Call complete_task.

5. Check the tool result.

6. Only then confirm completion to the user.

If complete_task reports failure:

→ Do NOT say the task was completed.

→ Explain that the update failed.


============================================================
AMBIGUOUS REQUESTS
============================================================

If the user's request is ambiguous and multiple tasks could match:

DO NOT guess.

Ask a short clarification question.


============================================================
NO-RESULT HANDLING
============================================================

If find_task returns no results:

1. Retry once using the most important keyword(s) from the user's request
   if a reasonable alternative search term exists.

2. If no useful alternative exists, clearly state that no matching task
   was found.

Do not fabricate a result.


============================================================
GENERAL CONVERSATION
============================================================

Not every user message requires a tool.

For general questions, explanations, greetings, or questions unrelated to
stored email tasks, answer normally without calling a task tool.


============================================================
RESPONSE STYLE
============================================================

Keep responses concise and practical.

When listing tasks, include useful information such as:

- task name
- deadline
- priority
- relevant sender/company
- whether a reply is needed

Only include fields that are actually available from the tool result.

Do not repeat unnecessary information.

When an action succeeds, briefly confirm it.

When an action fails, clearly state the failure.

Never expose internal tool-selection reasoning to the user.
"""
    }


    # ========================================================
    # CONVERSATION HISTORY
    # ========================================================

    if conversation_history is None:
        conversation_history = []


    messages = [
        system_message
    ]


    # Add previous conversation
    messages.extend(
        conversation_history
    )


    # Add current user message
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )


    # ========================================================
    # AGENT LOOP
    # ========================================================

    while True:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )


        message = response.choices[0].message


        # ====================================================
        # FINAL ANSWER
        # ====================================================

        if not message.tool_calls:

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content
                }
            )

            return (
                message.content,
                messages
            )


        # ====================================================
        # TOOL CALL
        # ====================================================

        logger.info("Agent tool call detected")


        # Add assistant tool-call message
        messages.append(
            message
        )


        # ====================================================
        # EXECUTE EACH TOOL
        # ====================================================

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            arguments_string = (
                tool_call.function.arguments
            )


            arguments = (
                json.loads(arguments_string)
                if arguments_string
                else {}
            )


            logger.info(
                "Tool: %s, Args: %s",
                tool_name,
                arguments
            )


            # =================================================
            # GET PENDING TASKS
            # =================================================

            if tool_name == "get_pending_tasks":

                result = get_pending_tasks_tool()


            # =================================================
            # FIND TASK
            # =================================================

            elif tool_name == "find_task":

                search_text = arguments.get(
                    "search_text",
                    ""
                )

                result = find_task_tool(
                    search_text
                )


            # =================================================
            # SEMANTIC SEARCH
            # =================================================

            elif tool_name == "semantic_search_tasks":

                search_text = arguments.get(
                    "search_text",
                    ""
                )

                result = semantic_search_tasks_tool(
                    search_text
                )


            # =================================================
            # HYBRID SEARCH
            # =================================================

            elif tool_name == "hybrid_search_tasks":

                search_text = arguments.get(
                    "search_text",
                    ""
                )

                result = hybrid_search_tasks_tool(
                    search_text
                )


            # =================================================
            # UPCOMING TASKS
            # =================================================

            elif tool_name == "get_upcoming_tasks":

                result = get_upcoming_tasks_tool()


            # =================================================
            # COMPLETED TASKS
            # =================================================

            elif tool_name == "get_completed_tasks":

                result = get_completed_tasks_tool()


            # =================================================
            # GET EMAIL
            # =================================================

            elif tool_name == "get_email":

                message_id = arguments.get(
                    "message_id"
                )

                result = get_email_tool(
                    message_id
                )


            # =================================================
            # PRIORITIZE
            # =================================================

            elif tool_name == "prioritize_tasks":

                result = prioritize_tasks_tool()


            # =================================================
            # COMPLETE TASK
            # =================================================

            elif tool_name == "complete_task":

                message_id = arguments.get(
                    "message_id"
                )


                if not message_id:

                    result = {
                        "success": False,
                        "error": "message_id was not provided."
                    }

                else:

                    modified_count = (
                        complete_task_tool(
                            message_id
                        )
                    )


                    result = {
                        "success": modified_count > 0
                        if isinstance(modified_count, int)
                        else modified_count.get("updated", False),
                        "modified_count": modified_count
                    }


            # =================================================
            # GET DRAFTS
            # =================================================

            elif tool_name == "get_drafts":

                status = arguments.get("status")

                result = get_drafts_tool(status)


            # =================================================
            # GET CALENDAR EVENTS
            # =================================================

            elif tool_name == "get_calendar_events":

                result = get_calendar_events_tool()


            # =================================================
            # UNKNOWN TOOL
            # =================================================

            else:

                result = {
                    "success": False,
                    "error": "Unknown tool."
                }


            # =================================================
            # SEND TOOL RESULT BACK TO LLM
            # =================================================

            logger.info(
                "Tool result type: %s",
                type(result).__name__
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        default=str
                    )
                }
            )