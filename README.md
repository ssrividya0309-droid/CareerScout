# CareerScout

CareerScout is a job-fit investigation agent that evaluates whether a job may be a meaningful fit for a candidate. Instead of calculating a fixed match score or following a predetermined checklist, the agent decides what information it needs to investigate before making a recommendation.

This project was created for BUAN 6V99: Agentic AI & Process Automation.

## Problem

Job seekers often compare their experience with a job posting by checking obvious criteria such as skills, education, and experience. A normal filtering script can determine whether keywords match, but it cannot decide which pieces of evidence are most meaningful for a particular candidate and job.

CareerScout addresses this by allowing a language model to decide what evidence it needs to investigate. Python tools retrieve factual information, while the model is responsible for interpreting that evidence and deciding what to investigate next.

## How CareerScout Works

CareerScout uses a hand-written agent loop rather than an agent framework.

The general process is:

1. Load the candidate and job data.
2. Send the available information and agent instructions to the Gemini API.
3. Gemini decides which factual tool would be useful.
4. Python runs the selected tool.
5. The tool result is returned to Gemini.
6. Gemini uses the new evidence to decide whether another investigation is needed.
7. The loop continues until Gemini determines that it has enough evidence to return a final assessment.
8. A human reviews whether the evidence used by CareerScout is actually meaningful.

The sequence of tools is not predetermined in the Python code. The next action depends on the evidence the model receives during the investigation.

## Available Tools

CareerScout currently has three factual tools:

### `check_required_skills`

Compares the candidate's skills with the required skills listed for the job and returns the matched and missing skills.

### `check_preferred_skills`

Compares the candidate's skills with the preferred skills listed for the job and returns the matched and missing skills.

### `get_candidate_experience`

Returns the candidate's experience together with the job requirements so the model can evaluate whether the experience provides meaningful evidence of fit.

The tools do not decide whether the candidate is a good match. They only return facts. The language model makes the judgment.

## Why This Is an Agent

CareerScout is different from a normal script because the entire investigation path is not known before the program runs.

A traditional script could run:

`check skills -> check experience -> calculate score -> return result`

CareerScout instead asks the model what information it needs next. After receiving a tool result, the model evaluates that result and chooses whether to use another tool or make a final judgment.

The model therefore controls the next step of the investigation based on what it has already learned.

## Evidence-Based Final Assessment

When CareerScout has enough information, it returns a final assessment containing:

- Job Evidence
- Candidate Evidence
- Reasoning
- Recommendation

The model is instructed to use evidence from the supplied candidate data, job data, and tool results rather than inventing information about the candidate or company.

## Human-in-the-Loop

CareerScout includes a human review step after the model produces its final assessment.

The user is shown the evidence and reasoning and is asked whether the evidence is meaningful for evaluating the candidate's fit.

This keeps the final decision with the human rather than allowing the model's recommendation to automatically trigger an application or another consequential action.

## Safety and Reliability

CareerScout includes several controls:

- A maximum agent step limit prevents an unlimited API loop.
- Temporary Gemini server errors are retried a limited number of times.
- The program stops safely if the API remains unavailable.
- The API key is stored in a `.env` file.
- `.env` is excluded from Git using `.gitignore`.
- The project uses synthetic candidate and job data.

## Project Structure

```text
CareerScout/
├── agent.py
├── tools.py
├── requirements.txt
├── .gitignore
├── data/
│   ├── candidate.json
│   └── job.json
└── .env
```

`agent.py` contains the Gemini API call, agent loop, tool routing, retry logic, and human review.

`tools.py` contains the factual tools available to CareerScout.

`candidate.json` and `job.json` contain the synthetic data used by the agent.

`requirements.txt` contains the Python packages needed to run the project.

`.env` stores the Gemini API key locally and is intentionally not included in the GitHub repository.

## Setup

### 1. Clone the repository

Clone the repository and open the CareerScout folder.

### 2. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a file named `.env` in the project folder and add:

```text
GEMINI_API_KEY=your_api_key_here
```

Do not commit the `.env` file to GitHub.

### 4. Run CareerScout

```bash
python3 agent.py
```

CareerScout will investigate the candidate and job, display each agent decision and factual tool result, produce a final assessment, and ask for human review.

## Model

The current version uses Google's Gemini API with:

`gemini-3.5-flash-lite`

The project calls the model directly from Python using the `google-genai` package. No agent framework such as LangChain, LangGraph, or CrewAI is used.

## Current Test Scenario

The included synthetic example evaluates Alex Morgan, a Master's student in Business Analytics, for a Data Analyst Intern position at the fictional company BrightPath Technologies.

The test data is intentionally non-sensitive and is used only to demonstrate the agent's investigation process.

## Key Design Choice

The main design principle behind CareerScout is:

**Tools return facts. The model makes the judgment.**

This separation makes it possible to see which information came directly from the data and which part of the process required language-model reasoning.