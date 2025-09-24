from enum import StrEnum


def durable_from_subject(subject: StrEnum | str, prefix: str) -> str:
    if isinstance(subject, StrEnum):
        value = subject.value
    else:
        value = subject

    return f"{prefix}_{value.replace('.', '_')}"
