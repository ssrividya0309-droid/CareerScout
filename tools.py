def check_required_skills(candidate, job):
    candidate_skills = candidate["skills"]
    required_skills = job["required_skills"]

    matched = []
    missing = []

    for skill in required_skills:
        if skill in candidate_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    return {
        "matched_skills": matched,
        "missing_skills": missing
    }

def check_preferred_skills(candidate, job):
    candidate_skills = candidate["skills"]
    preferred_skills = job["preferred_skills"]

    matched = []
    missing = []

    for skill in preferred_skills:
        if skill in candidate_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    return {
        "matched_skills": matched,
        "missing_skills": missing
    }

def get_candidate_experience(candidate, job):
    return {
        "candidate_experience": candidate["experience"],
        "job_requirements": job["requirements"]
    }
