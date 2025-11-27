def build_prompt(stage, topic=None, tone=None, audience=None, keywords=None, headline=None, profile_summary=None, mode=None):
    """
    Unified prompt builder.
    stage: 'headline', 'body', 'hashtags', 'keywords', 'engagement', 'rewrite', 'cta', 'extract_tone', 'followup'
    mode: optional rewrite mode like 'shorten', 'punchier', 'storytelling', 'more_data', 'recruiter_friendly'
    """
    ctx = ""
    if profile_summary:
        ctx = (
            f"Analyze this LinkedIn profile and emulate the user's tone, style, and typical phrasing:\n"
            f"{profile_summary}\n\n"
        )

    if stage == "headline":
        return ctx + f"Write 3 catchy LinkedIn headlines about '{topic}' with a '{tone}' tone."

    if stage == "body":
        prompt = ctx + (
            f"Write a detailed LinkedIn post paragraph (3-6 sentences) based on this headline: '{headline}'. "
            f"Tone: '{tone}'. Make it engaging and professional."
        )
        if audience:
            prompt += f" Audience: {audience}."
        if keywords:
            prompt += f" Include these keywords: {keywords}."
        return prompt

    if stage == "hashtags":
        return ctx + f"Suggest 5 relevant hashtags (with #) for the LinkedIn post about: '{headline}'."

    if stage == "keywords":
        return ctx + f"Suggest 5–10 keywords to improve LinkedIn post visibility about: '{topic}'."

    if stage == "engagement":
        return ctx + (
            f"Rate the predicted engagement (1-10) and give a 1-sentence rationale for this post. "
            f"Post headline: {headline}\nPost body: {keywords}\nAudience: {audience}\nTopic: {topic}"
        )

    if stage == "rewrite":
        mm = f" (mode: {mode})" if mode else ""
        return ctx + (
            f"Here is the current LinkedIn post body:\n{headline}\n\n"
            f"Refine it{mm} according to this instruction: {keywords}\n"
            "Return only the revised post body as a paragraph (3-6 sentences)."
        )

    if stage == "cta":
        return ctx + f"Suggest 3 concise call-to-action lines for a LinkedIn post about: '{topic}'."

    if stage == "extract_tone":
        return (
            f"Read the LinkedIn profile below. Extract a short description of the user's tone, "
            f"common phrases, and 3 example sentence openers they use. Return as JSON: {{'tone_summary':..., 'phrases':[...], 'openers':[...]}}\n\n{profile_summary}"
        )

    if stage == "followup":
        # Ask clarifying question(s) based on missing info
        missing = []
        if not tone:
            missing.append("tone")
        if not audience:
            missing.append("audience")
        if not keywords:
            missing.append("keywords")
        if missing:
            m = ", ".join(missing)
            return ctx + f"Ask one concise clarifying question requesting the missing fields: {m}."
        return ctx + "Ask one concise clarifying question to better tailor the LinkedIn post."

    raise ValueError(f"Invalid stage: {stage}")
