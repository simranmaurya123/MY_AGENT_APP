import tiktoken
from typing import Optional



try:
    encoder = tiktoken.encoding_for_model("gpt-4o-mini")
except Exception :
    encoder = tiktoken.get_encoding("cl100k_base")
 
    
def estimate_tokens(text: str) -> int:
    """Fast token estimation using tiktoken."""
    if not text:
        return 0
    return len(encoder.encode(text))


def count_message_tokens(message:dict) -> int:
    """ Count tokens in a single message"""
    if not message:
        return 0
    
    content = message.get("content", "")
    role = message.get("role", "")
    
    role_tokens = estimate_tokens(role)
    content_tokens=estimate_tokens(content)
    overhead = 4
    
    return role_tokens + content_tokens + overhead


def count_all_tokens(messages:list[dict]) -> int:
    """ Count total tokens in a list of messages"""
    total = 0
    for message in messages:
        total += count_message_tokens(message)
    return total

    

def threshold_compress(
    messages: list[dict],
    budget: int = 128_000,
    threshold: float = 0.7,
    keep_recent: int = 10,
    client=None,
) -> list[dict]:
    """ Compress older messages when token usage exceeds threshold."""
    
    
    total_tokens = count_all_tokens(messages)
    threshold_tokens = budget * threshold
    
    print(f"[Token Info] Used: {total_tokens} / Budget: {budget} (Threshold: {int(threshold_tokens)})")
    
    if total_tokens < threshold_tokens:
        print("[Token Info] Under threshold: no compression needed")
        return messages
    
    print("[Token Info] Over threshold: compressing old messages...")
    
    system = [m for m in messages if m["role"] == "system"]
    conversation = [m for m in messages if m["role"] != "system"]
    
    if len(conversation) <= keep_recent:
        print(f"[Token Info] Only {len(conversation)} messages total; keeping all")
        return messages
    
    # Find a safe split point: never split in the middle of a tool-call group.
    # Walk backward from the ideal split until we land on a user/assistant message
    # that is NOT a tool response (i.e., not orphaned from its tool_calls parent).
    split = len(conversation) - keep_recent
    while split > 0 and conversation[split]["role"] == "tool":
        split -= 1
    # Also step back past the assistant message that owns those tool calls
    while split > 0 and conversation[split].get("tool_calls"):
        split -= 1

    old = conversation[:split]
    recent = conversation[split:]
    
    if not old:
        print("[Token Info] Cannot safely compress without orphaning tool calls; keeping all")
        return messages
    
    summary = _summarize_messages(old, client)
    compressed = system + [{
        "role": "system",
        "content": f"Conversation summary\n {summary}"
    }] + recent
    
    return compressed


def _summarize_messages(old_messages:list[dict], client) -> str:   
    """ Use LLM to summarize messages"""
    transcript = "\n".join([
        f"[{msg['role'].upper()}]: {msg['content'][:200]}..."
        if len(msg.get('content', '')) > 200
        else f"[{msg['role'].upper()}]: {msg.get('content', '')}"
        for msg in old_messages
    ])
    
    SUMMARIZE_PROMPT = """Summarize the key points, decisions, and important context from this conversation.
Include: main topics discussed, data queries run, findings, and any important state.
Be concise — under 300 words. Focus on what the assistant needs to remember."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"{SUMMARIZE_PROMPT}\n\nConversation:\n{transcript}"
        }],
            temperature=0.3,
            max_tokens=512,
    )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Token Error] Failed to summarize messages: {e}")
        return "Failed to summarize messages."


def get_token_usage_report(messages:list[dict]) -> dict:
    """generate detailed token usage report"""
    
    system_tokens = sum(estimate_tokens(m['content']) for m in messages if m['role'] == 'system')
    user_tokens = sum(estimate_tokens(m['content']) for m in messages if m['role'] == 'user')
    assistant_tokens = sum(estimate_tokens(m['content']) for m in messages if m['role'] == 'assistant')
    tool_tokens = sum(estimate_tokens(m['content']) for m in messages if m['role'] == 'tool')
    
    total = system_tokens + user_tokens + assistant_tokens + tool_tokens
    
    return {
        "total": total,
        "system": system_tokens,
        "user": user_tokens,
        "assistant": assistant_tokens,
        "tool": tool_tokens,
        "message_count": len(messages),
    }