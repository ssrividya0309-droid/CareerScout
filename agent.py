import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from tools import (
    check_required_skills,
    check_preferred_skills,
    get_candidate_experience,
)

# --------------------------------------------------
# SETUP
# --------------------------------------------------

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash-lite"

# Prevent the agent from running forever
MAX_STEPS = 5

# Retry temporary Gemini server errors
MAX_RETRIES = 3


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

with open("data/candidate.json", "r") as file:
    candidate = json.load(file)

with open("data/job.json", "r") as file:
    job = json.load(file)


# --------------------------------------------------
# TOOL ROUTER
# --------------------------------------------------

def run_tool(tool_name):
    """
    Runs the factual tool selected by the language model.
    The tools return evidence only.
    They do not decide whether the candidate is a good fit.
    """

    if tool_name == "check_required_skills":
        return check_required_skills(candidate, job)

    elif tool_name == "check_preferred_skills":
        return check_preferred_skills(candidate, job)

    elif tool_name == "get_candidate_experience":
        return get_candidate_experience(candidate, job)

    else:
        return {
            "error": f"Unknown tool: {tool_name}"
        }


# --------------------------------------------------
# GEMINI API CALL WITH RETRY
# --------------------------------------------------

def ask_model(history):
    """
    Sends the current investigation history to Gemini.

    If Gemini temporarily returns a 503 high-demand error,
    CareerScout waits briefly and tries again.
    """

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=history,
            )

            return response.text.strip()

        except errors.ServerError as error:

            if error.code == 503:

                if attempt < MAX_RETRIES:
                    wait_time = attempt * 3

                    print(
                        f"\nGemini is temporarily busy. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:
                    print(
                        "\nGemini is still unavailable after "
                        "multiple attempts."
                    )

                    return None

            else:
                raise


# --------------------------------------------------
# AGENT INSTRUCTIONS
# --------------------------------------------------

instructions = f"""
You are CareerScout, a job-fit investigation agent.

Your goal is to determine whether this particular job could be a
meaningful fit for this candidate.

You are not a fixed scoring system.

Do NOT calculate a match percentage.

Do NOT automatically follow a predetermined checklist.

Instead, examine the available evidence and decide what information
would be most useful to investigate next.

AVAILABLE TOOLS

1. check_required_skills

This tool returns which required skills from the job are present
in the candidate's listed skills and which are missing.


2. check_preferred_skills

This tool returns which preferred skills from the job are present
in the candidate's listed skills and which are missing.


3. get_candidate_experience

This tool returns the candidate's actual experience statements
together with the job's stated requirements.


IMPORTANT RULES

The Python tools only return facts.

YOU make the judgment about whether those facts are meaningful.

You decide which tool should be used next based on evidence from
previous tool results.

Do not automatically call every tool.

Do not invent candidate experience or job requirements.

Do not claim something is supported unless it appears in the
candidate data, job data, or a tool result.

If you need more evidence, respond in EXACTLY this format:

TOOL: tool_name
REASON: explain briefly why this evidence is useful

The tool_name must be exactly one of these:

check_required_skills
check_preferred_skills
get_candidate_experience


When you believe you have enough evidence, respond in EXACTLY
this format:

FINAL:
Job Evidence: cite specific evidence from the job information
Candidate Evidence: cite specific evidence from the candidate information
Reasoning: explain why the evidence is meaningful for this particular candidate
Recommendation: give your final assessment

The final judgment must be based on checkable evidence rather than
general or plausible-sounding assumptions.


CANDIDATE DATA

{json.dumps(candidate, indent=2)}


JOB DATA

{json.dumps(job, indent=2)}
"""


# --------------------------------------------------
# START CAREERSCOUT
# --------------------------------------------------

print("\n======================================")
print("          CAREERSCOUT AGENT")
print("======================================")

print("\nCandidate:", candidate["name"])
print("Job:", job["job_title"])
print("Company:", job["company"])

print(
    "\nCareerScout will investigate the job "
    "before making a final judgment."
)


# The history changes after every model decision and tool result.
# This allows the next step to depend on what happened previously.

history = instructions

final_answer = None


# --------------------------------------------------
# AGENT LOOP
# --------------------------------------------------

for step in range(1, MAX_STEPS + 1):

    print("\n======================================")
    print(f"             STEP {step}")
    print("======================================")

    decision = ask_model(history)

    if decision is None:
        print(
            "\nCareerScout stopped because the Gemini API "
            "is temporarily unavailable."
        )
        break

    print("\nAgent decision:")
    print(decision)


    # --------------------------------------------------
    # MODEL HAS ENOUGH EVIDENCE
    # --------------------------------------------------

    if decision.startswith("FINAL:"):

        final_answer = decision
        break


    # --------------------------------------------------
    # MODEL REQUESTS A TOOL
    # --------------------------------------------------

    elif decision.startswith("TOOL:"):

        first_line = decision.splitlines()[0]

        tool_name = first_line.replace(
            "TOOL:", ""
        ).strip()

        print("\n--------------------------------------")
        print("Tool selected:", tool_name)
        print("--------------------------------------")

        tool_result = run_tool(tool_name)

        print("\nFactual tool result:")

        print(
            json.dumps(
                tool_result,
                indent=2
            )
        )


        # Add what happened to the investigation history.
        # Gemini sees this evidence during the next loop.
        # It must then decide whether another tool is needed.

        history += f"""

PREVIOUS AGENT DECISION:

{decision}


TOOL USED:

{tool_name}


FACTUAL TOOL RESULT:

{json.dumps(tool_result, indent=2)}


You now have new evidence.

Decide what to do next based on this evidence.

Do not repeat a tool unless there is a genuine reason.

If another factual question needs investigation, select the most
useful available tool.

If you already have enough evidence to make a grounded judgment,
return FINAL.
"""


    # --------------------------------------------------
    # MODEL USED WRONG FORMAT
    # --------------------------------------------------

    else:

        print(
            "\nThe model did not follow the required "
            "TOOL or FINAL format."
        )

        history += f"""

Your previous response was:

{decision}

That response did not follow the required format.

Respond again using ONLY one of these formats:

TOOL: tool_name
REASON: explanation

OR

FINAL:
Job Evidence: ...
Candidate Evidence: ...
Reasoning: ...
Recommendation: ...
"""


# --------------------------------------------------
# SAFETY CAP
# --------------------------------------------------

if final_answer is None:

    print("\n======================================")
    print("          AGENT STOPPED")
    print("======================================")

    print(
        "\nCareerScout stopped without a final assessment."
    )

    print(
        "The program uses a maximum step limit so the "
        "agent cannot create an unlimited API loop."
    )


# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

else:

    print("\n======================================")
    print("          FINAL ASSESSMENT")
    print("======================================")

    print("\n" + final_answer)


    # --------------------------------------------------
    # HUMAN-IN-THE-LOOP REVIEW
    # --------------------------------------------------

    print("\n======================================")
    print("            HUMAN REVIEW")
    print("======================================")

    print(
        "\nCareerScout has provided the evidence it used "
        "for its judgment."
    )

    review = input(
        "\nDo you agree that this evidence is meaningful "
        "for judging the candidate's fit? (yes/no): "
    ).strip().lower()


    if review == "yes":

        print(
            "\nHuman review: Evidence approved."
        )

        print(
            "CareerScout's recommendation can move forward "
            "for consideration."
        )


    elif review == "no":

        print(
            "\nHuman review: Evidence was not approved."
        )

        print(
            "The recommendation should be reviewed before "
            "being used."
        )


    else:

        print(
            "\nHuman review: No yes/no decision was recorded."
        )