from cipher.skills import skill
from cipher.core import scheduler


@skill("schedule_post",
       "Schedule a social media post. CIPHER messages the post text to the user at "
       "that time so they can publish it. 'when' is local time as YYYY-MM-DD HH:MM.",
       {"text": {"type": "string"}, "when": {"type": "string"}}, ["text", "when"])
def schedule_post(text, when):
    try:
        p = scheduler.add_post(text, when)
    except ValueError as e:
        return f"Could not schedule: {e}. Use the format YYYY-MM-DD HH:MM."
    return f"Scheduled #{p['id']} for {p['when']}."


@skill("list_posts", "List the user's scheduled posts.")
def list_posts():
    posts = scheduler.list_posts()
    return "\n".join(f"#{p['id']} {p['when']} {p['text'][:60]}" for p in posts) \
        or "No scheduled posts."


@skill("cancel_post", "Cancel a scheduled post by its ID.",
       {"post_id": {"type": "string"}}, ["post_id"])
def cancel_post(post_id):
    return "Cancelled." if scheduler.cancel_post(post_id.lstrip("#")) else "No post with that ID."
