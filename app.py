import streamlit as st
from datetime import datetime

# Try safe imports from your agent - if a function is missing, provide a local fallback.
try:
    from src.agent import (
        generate_headlines,
        generate_body,
        generate_adaptive_keywords,
        refine_post,
        generate_ctas,
        generate_engagement_score,
        extract_tone_from_profile,
        conversational_followup,
    )
except Exception:
    # Minimal fallbacks if functions are missing so app doesn't crash.
    # These fallbacks raise informative errors at call-time if used.
    def _missing(name):
        def _fn(*args, **kwargs):
            raise ImportError(f"Required function '{name}' not found in src.agent. Please add it.")
        return _fn

    generate_headlines = _missing("generate_headlines")
    generate_body = _missing("generate_body")
    generate_adaptive_keywords = _missing("generate_adaptive_keywords")
    refine_post = _missing("refine_post")
    generate_ctas = _missing("generate_ctas")
    generate_engagement_score = _missing("generate_engagement_score")
    extract_tone_from_profile = _missing("extract_tone_from_profile")

    # Provide a simple conversational fallback
    def conversational_followup(draft):
        if not draft.get("tone"):
            return "Do you want this post to sound more professional, casual, or story-driven?"
        if not draft.get("audience"):
            return "Who should this post speak to? (e.g., recruiters, peers, hiring managers)"
        if not draft.get("user_keywords"):
            return "Any keywords you'd like included? (comma-separated)"
        return "Would you like the post shorter, more narrative, or punchier?"

from src.storage import save_post, load_history, get_analytics

# -------------------------
# Page setup
# -------------------------
st.set_page_config(page_title="LinkedIn AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 LinkedIn AI Post Agent")

# -------------------------
# Session state initialization (safe defaults)
# -------------------------
if "step" not in st.session_state:
    st.session_state.step = "topic"
if "draft" not in st.session_state:
    st.session_state.draft = {}
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "selected_headline" not in st.session_state:
    st.session_state.selected_headline = None
if "selected_adaptive" not in st.session_state:
    st.session_state.selected_adaptive = []
if "headlines" not in st.session_state:
    st.session_state.headlines = []
if "ctas" not in st.session_state:
    st.session_state.ctas = []
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

draft = st.session_state.draft

# -------------------------
# Sidebar - Refinement controls (separate by section)
# -------------------------
st.sidebar.header("Refinement & Regeneration")

st.sidebar.subheader("Headline Tools")
headline_mode = st.sidebar.selectbox(
    "Preset headline mode (optional)",
    ["", "professional", "punchy", "storytelling", "empathetic"],
    key="headline_mode"
)
headline_instr = st.sidebar.text_input("Free instruction for headline (optional)", key="headline_instr")
if st.sidebar.button("Regenerate Headline"):
    # regenerate headlines list
    try:
        st.session_state.headlines = generate_headlines(
            draft.get("topic", ""),
            tone=draft.get("tone"),
            profile_summary=draft.get("profile_summary"),
        )
    except Exception as e:
        st.sidebar.error(f"Headline regen failed: {e}")
    else:
        st.session_state.selected_headline = st.session_state.headlines[0] if st.session_state.headlines else None
        draft["headlines"] = st.session_state.headlines
        draft["headline"] = st.session_state.selected_headline
        st.rerun()

if st.sidebar.button("Refine Headline"):
    if not draft.get("headline"):
        st.sidebar.error("No headline to refine. Generate one first.")
    else:
        try:
            draft_headline = refine_post(headline_instr or "Make headline more engaging", {"body": draft.get("headline"), **draft}, mode=headline_mode or None)
            draft["headline"] = draft_headline
            st.sidebar.success("Headline refined.")
            st.experimental_rerun()
        except Exception as e:
            st.sidebar.error(f"Headline refine failed: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("Body Tools")

body_mode = st.sidebar.selectbox(
    "Preset body mode",
    ["", "shorten", "punchier", "storytelling", "professional", "casual", "witty", "more_data", "recruiter_friendly"],
    key="body_mode"
)
body_instr = st.sidebar.text_input("Free instruction for body (optional)", key="body_instr")

if st.sidebar.button("Regenerate Body"):
    try:
        # regenerate body using adaptive keywords if selected
        adaptive = st.session_state.selected_adaptive if st.session_state.selected_adaptive else None
        draft["body"] = generate_body(
            draft.get("headline", ""),
            tone=draft.get("tone"),
            audience=draft.get("audience"),
            keywords=draft.get("user_keywords"),
            adaptive_keywords=adaptive,
            profile_summary=draft.get("profile_summary"),
        )
    except Exception as e:
        st.sidebar.error(f"Body regen failed: {e}")
    else:
        st.sidebar.success("Body regenerated.")
        st.rerun()

if st.sidebar.button("Refine Body"):
    if not draft.get("body"):
        st.sidebar.error("No body to refine. Generate body first.")
    else:
        try:
            draft["body"] = refine_post(body_instr or "Make the post clearer and more engaging.", draft, mode=body_mode or None)
        except Exception as e:
            st.sidebar.error(f"Body refine failed: {e}")
        else:
            st.sidebar.success("Body refined.")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("CTA Tools")

cta_mode = st.sidebar.selectbox("CTA preset (optional)", ["", "short_cta", "invite_to_connect", "ask_question"], key="cta_mode")
cta_instr = st.sidebar.text_input("Free CTA instruction (optional)", key="cta_instr")

if st.sidebar.button("Regenerate CTAs"):
    try:
        st.session_state.ctas = generate_ctas(draft.get("topic", ""), profile_summary=draft.get("profile_summary"))
        draft["ctas"] = st.session_state.ctas
        draft["cta"] = draft.get("ctas", [None])[0]
    except Exception as e:
        st.sidebar.error(f"CTA regen failed: {e}")
    else:
        st.sidebar.success("CTAs regenerated.")
        st.rerun()

if st.sidebar.button("Refine CTA"):
    if not draft.get("cta"):
        st.sidebar.error("No CTA to refine.")
    else:
        try:
            draft["cta"] = refine_post(cta_instr or "Make CTA concise and actionable.", {"body": draft.get("cta"), **draft}, mode=cta_mode or None)
        except Exception as e:
            st.sidebar.error(f"CTA refine failed: {e}")
        else:
            st.sidebar.success("CTA refined.")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Full Post Tools")
if st.sidebar.button("Regenerate Entire Post (headline, body, CTA)"):
    try:
        st.session_state.headlines = generate_headlines(draft.get("topic", ""), tone=draft.get("tone"), profile_summary=draft.get("profile_summary"))
        draft["headlines"] = st.session_state.headlines
        st.session_state.selected_headline = st.session_state.headlines[0] if st.session_state.headlines else None
        draft["headline"] = st.session_state.selected_headline

        adaptive = st.session_state.selected_adaptive if st.session_state.selected_adaptive else None
        draft["body"] = generate_body(draft.get("headline", ""), tone=draft.get("tone"), audience=draft.get("audience"), keywords=draft.get("user_keywords"), adaptive_keywords=adaptive, profile_summary=draft.get("profile_summary"))
        st.session_state.ctas = generate_ctas(draft.get("topic", ""), profile_summary=draft.get("profile_summary"))
        draft["ctas"] = st.session_state.ctas
        draft["cta"] = draft.get("ctas", [None])[0]
    except Exception as e:
        st.sidebar.error(f"Full regen failed: {e}")
    else:
        st.sidebar.success("Full post regenerated.")
        st.rerun()

if st.sidebar.button("Refine Entire Post"):
    # apply refinement instruction across headline/body/cta using refine_post
    full_instr = st.sidebar.text_input("Instruction for full-post refine (applies to headline/body/cta)", key="full_instr")
    # if no instruction typed, use default
    instr = full_instr.strip() or "Make the whole post more engaging and concise while preserving tone."
    try:
        # refine headline
        if draft.get("headline"):
            try:
                draft["headline"] = refine_post(instr, {"body": draft.get("headline"), **draft}, mode=None)
            except Exception:
                # fallback: keep headline
                pass
        # refine body
        if draft.get("body"):
            draft["body"] = refine_post(instr, draft, mode=None)
        # refine cta
        if draft.get("cta"):
            try:
                draft["cta"] = refine_post(instr, {"body": draft.get("cta"), **draft}, mode=None)
            except Exception:
                pass
    except Exception as e:
        st.sidebar.error(f"Full refine failed: {e}")
    else:
        st.sidebar.success("Full post refined.")
        st.rerun()

st.sidebar.markdown("---")
# quick grammar button
if st.sidebar.button("Quick Grammar & Clarity (body)"):
    try:
        draft["body"] = refine_post("Improve grammar and clarity while preserving tone.", draft, mode="clarity")
    except Exception as e:
        st.sidebar.error(f"Grammar refine failed: {e}")
    else:
        st.sidebar.success("Grammar improved.")
        st.rerun()

# -------------------------
# Reset / New Chat
# -------------------------
def reset_all():
    st.session_state.step = "topic"
    st.session_state.draft = {}
    st.session_state.conversation = []
    st.session_state.selected_headline = None
    st.session_state.selected_adaptive = []
    st.session_state.headlines = []
    st.session_state.ctas = []
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Reset All & Start New Chat"):
    reset_all()

# -------------------------
# Main UI - conversation & workflow
# -------------------------
# Show conversation history
for msg in st.session_state.conversation:
    with st.chat_message(msg.get("role", "assistant")):
        st.markdown(msg.get("message", ""))

tabs = st.tabs(["Chat Agent", "History & Analytics"])
tab1, tab2 = tabs

with tab1:
    # Step 1: Topic
    if st.session_state.step == "topic":
        with st.form("topic_form"):
            topic_input = st.text_input("Enter your post topic:", value=draft.get("topic", ""))
            submitted = st.form_submit_button("Next")
            if submitted and topic_input.strip():
                draft["topic"] = topic_input.strip()
                st.session_state.conversation.append({"role": "user", "message": draft["topic"]})
                try:
                    follow = conversational_followup(draft)
                except Exception:
                    follow = "Tell me more about the angle you want to take on this topic."
                st.session_state.conversation.append({"role": "assistant", "message": follow})
                st.session_state.step = "tone"
                st.rerun()

    # Step 2: Tone
    elif st.session_state.step == "tone":
        with st.form("tone_form"):
            tone_input = st.text_input("Enter desired tone (optional):", value=draft.get("tone", ""))
            submitted = st.form_submit_button("Next")
            if submitted:
                draft["tone"] = tone_input.strip() or None
                st.session_state.conversation.append({"role": "user", "message": tone_input or "[no tone]"})
                try:
                    follow = conversational_followup(draft)
                except Exception:
                    follow = "Who should this post speak to?"
                st.session_state.conversation.append({"role": "assistant", "message": follow})
                st.session_state.step = "audience"
                st.rerun()

    # Step 3: Audience
    elif st.session_state.step == "audience":
        with st.form("audience_form"):
            audience_input = st.text_input("Target audience (optional):", value=draft.get("audience", ""))
            submitted = st.form_submit_button("Next")
            if submitted:
                draft["audience"] = audience_input.strip() or None
                st.session_state.conversation.append({"role": "user", "message": audience_input or "[no audience]"})
                try:
                    follow = conversational_followup(draft)
                except Exception:
                    follow = "Any keywords you want included?"
                st.session_state.conversation.append({"role": "assistant", "message": follow})
                st.session_state.step = "keywords"
                st.rerun()

    # Step 4: Keywords
    elif st.session_state.step == "keywords":
        with st.form("keywords_form"):
            keywords_input = st.text_input("Enter keywords to include (comma separated, optional):", value=draft.get("user_keywords", "") or "")
            submitted = st.form_submit_button("Next")
            if submitted:
                draft["user_keywords"] = keywords_input.strip() or None
                st.session_state.conversation.append({"role": "user", "message": keywords_input or "[no keywords]"})
                st.session_state.step = "profile"
                st.rerun()

    # Step 5: LinkedIn About
    elif st.session_state.step == "profile":
        with st.form("profile_form"):
            profile_input = st.text_area("Paste your LinkedIn 'About' section (optional):", value=draft.get("profile_summary", "") or "", height=160)
            submitted = st.form_submit_button("Generate Post")
            if submitted:
                draft["profile_summary"] = profile_input.strip() or None
                if profile_input.strip():
                    try:
                        tone_info = extract_tone_from_profile(profile_input)
                        draft["extracted_tone"] = tone_info
                        if not draft.get("tone"):
                            draft["tone"] = tone_info.get("tone_summary") if isinstance(tone_info, dict) else None
                    except Exception:
                        pass
                st.session_state.step = "generate_post"
                st.rerun()

    # Step 6: Generate post UI
    if st.session_state.step == "generate_post":
        # Headlines
        if not draft.get("headlines"):
            try:
                draft["headlines"] = generate_headlines(draft.get("topic", ""), tone=draft.get("tone"), profile_summary=draft.get("profile_summary"))
                st.session_state.headlines = draft["headlines"]
            except Exception as e:
                st.error(f"Headline generation error: {e}")
                draft["headlines"] = []

        # ensure a headline exists
        if not st.session_state.headlines:
            st.session_state.headlines = draft.get("headlines", [])

        if st.session_state.headlines:
            # safe index
            try:
                idx = st.session_state.headlines.index(st.session_state.selected_headline) if st.session_state.selected_headline in st.session_state.headlines else 0
            except Exception:
                idx = 0
            choice = st.radio("Select a headline:", st.session_state.headlines, index=idx, key="headline_radio")
            st.session_state.selected_headline = choice
            draft["headline"] = choice
        else:
            st.info("No headlines available. Try regenerating.")

        # Body generation
        if not draft.get("body"):
            try:
                draft["body"] = generate_body(draft.get("headline", ""), tone=draft.get("tone"), audience=draft.get("audience"), keywords=draft.get("user_keywords"), adaptive_keywords=st.session_state.selected_adaptive or None, profile_summary=draft.get("profile_summary"))
            except Exception as e:
                st.error(f"Body generation error: {e}")
                draft["body"] = ""

        # Body editor (editable)
        edited_body = st.text_area("Generated Body (editable):", value=draft.get("body", "") or "", height=220, key="body_main")
        draft["body"] = edited_body

        # Adaptive keywords (generate if missing)
        if "adaptive_keywords" not in draft:
            try:
                draft["adaptive_keywords"] = generate_adaptive_keywords(draft.get("topic", ""), profile_summary=draft.get("profile_summary"))
            except Exception:
                draft["adaptive_keywords"] = []

        if draft.get("adaptive_keywords"):
            st.markdown("**Adaptive Keywords** (optional - check to include and regenerate body with them):")
            sel = []
            for k in draft.get("adaptive_keywords", []):
                checked = st.checkbox(k, key=f"ak_{k}", value=(k in st.session_state.selected_adaptive))
                if checked:
                    sel.append(k)
            st.session_state.selected_adaptive = sel
            if sel:
                # regenerate body incorporating adaptive keywords
                try:
                    draft["body"] = generate_body(draft.get("headline", ""), tone=draft.get("tone"), audience=draft.get("audience"), keywords=draft.get("user_keywords"), adaptive_keywords=sel, profile_summary=draft.get("profile_summary"))
                except Exception as e:
                    st.error(f"Adaptive body generation failed: {e}")

        # Regenerate & Refine controls (in-page quick buttons)
        rcol1, rcol2, rcol3 = st.columns(3)
        with rcol1:
            if st.button("Regenerate Body (quick)"):
                try:
                    draft["body"] = generate_body(draft.get("headline", ""), tone=draft.get("tone"), audience=draft.get("audience"), keywords=draft.get("user_keywords"), adaptive_keywords=st.session_state.selected_adaptive or None, profile_summary=draft.get("profile_summary"))
                    st.success("Body regenerated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Regenerate body failed: {e}")
        with rcol2:
            if st.button("Regenerate Headline (quick)"):
                try:
                    st.session_state.headlines = generate_headlines(draft.get("topic", ""), tone=draft.get("tone"), profile_summary=draft.get("profile_summary"))
                    draft["headlines"] = st.session_state.headlines
                    st.session_state.selected_headline = st.session_state.headlines[0] if st.session_state.headlines else None
                    draft["headline"] = st.session_state.selected_headline
                    st.success("Headlines regenerated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Regenerate headline failed: {e}")
        with rcol3:
            if st.button("Regenerate CTAs (quick)"):
                try:
                    st.session_state.ctas = generate_ctas(draft.get("topic", ""), profile_summary=draft.get("profile_summary"))
                    draft["ctas"] = st.session_state.ctas
                    draft["cta"] = draft.get("ctas", [None])[0]
                    st.success("CTAs regenerated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Regenerate CTAs failed: {e}")

        # CTA selection
        if not draft.get("ctas"):
            try:
                draft["ctas"] = generate_ctas(draft.get("topic", ""), profile_summary=draft.get("profile_summary"))
            except Exception:
                draft["ctas"] = []
        cta_opts = draft.get("ctas", ["Let's connect!"])
        cta_choice = st.radio("Select CTA:", cta_opts, index=0, key="cta_radio")
        draft["cta"] = cta_choice

        # Engagement score (safe)
        if "predicted_engagement" not in draft:
            try:
                draft["predicted_engagement"] = generate_engagement_score(draft.get("headline", ""), draft.get("body", ""), audience=draft.get("audience"), profile_summary=draft.get("profile_summary"))
            except Exception:
                draft["predicted_engagement"] = "n/a"
        st.markdown(f"**Predicted Engagement:** {draft.get('predicted_engagement', 'n/a')}")

        # Put all together (copy-ready)
        if st.button("📋 Put It All Together"):
            final_text = f"{draft.get('headline','')}\n\n{draft.get('body','')}"
            if draft.get("cta"):
                final_text = f"{final_text}\n\n{draft.get('cta')}"
            st.text_area("Final Post (copy & paste ready):", value=final_text, height=280, key="final_post")

        # LinkedIn-style preview (always safe)
        st.markdown("### 🔵 LinkedIn Preview")
        st.markdown(
            f"""
            <div style='border:1px solid #ddd; padding:16px; border-radius:8px; background:#ffffff;'>
                <h3 style='margin-bottom:8px; font-weight:600;'>{draft.get('headline','')}</h3>
                <p style='color:#111; white-space:pre-line;'>{draft.get('body','')}</p>
                {f"<p style='color:#0a66c2; font-weight:600;'>{draft.get('cta')}</p>" if draft.get('cta') else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Save Post
        if st.button("Save Post"):
            save_post({
                "topic": draft.get("topic"),
                "tone": draft.get("tone"),
                "headline": draft.get("headline"),
                "body": draft.get("body"),
                "adaptive_keywords": draft.get("adaptive_keywords", []),
                "cta": draft.get("cta"),
                "predicted_engagement": draft.get("predicted_engagement"),
                "extracted_tone": draft.get("extracted_tone"),
                "timestamp": datetime.now().isoformat()
            })
            st.success("Post saved to history!")

with tab2:
    history = load_history()
    if history:
        st.subheader("Post History")
        for p in reversed(history):
            st.markdown(f"### {p.get('headline','[no headline]')}")
            st.markdown(p.get("body", ""))
            st.markdown(f"**CTA:** {p.get('cta','')}")
            st.markdown(f"**Saved:** {p.get('timestamp','')}")
            st.markdown("---")

        analytics = get_analytics()
        st.subheader("Analytics")
        st.markdown(f"- Total Posts: {analytics.get('total_posts',0)}")
        avg = analytics.get('average_engagement', 0)
        try:
            st.markdown(f"- Avg Engagement: {avg:.1f}")
        except Exception:
            st.markdown(f"- Avg Engagement: {avg}")
        st.markdown(f"- Tone Distribution: {analytics.get('tone_distribution', {})}")
    else:
        st.info("No posts in history yet.")
