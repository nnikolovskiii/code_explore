from typing import List, Dict


def _get_messages_template(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ] if history is None else [{"role": "user", "content": message}]

    all_messages = [] if history is None else history
    all_messages.extend(messages)
    return all_messages