from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class TrackingTargetContext:
    """Short tracking target description for LLM context."""

    title: str
    code: str
    description: str | None = None


@dataclass(slots=True, kw_only=True)
class AgentContext:
    """Small LLM-facing context.

    This object is not a database read model.
    It is a compact context block injected into the agent prompt.
    """

    display_name: str | None
    language: str
    communication_style: str
    general_notes: str | None = None
    tracking_targets: list[TrackingTargetContext] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        lines: list[str] = []

        if self.display_name:
            lines.append(f"User name: {self.display_name}")

        lines.append(f"Language: {self.language}")
        lines.append(f"Communication style: {self.communication_style}")

        if self.general_notes:
            lines.append("")
            lines.append("User notes:")
            lines.append(self.general_notes)

        if self.tracking_targets:
            lines.append("")
            lines.append("Active tracking targets:")

            for target in self.tracking_targets:
                line = f"- {target.title} ({target.code})"
                if target.description:
                    line += f": {target.description}"
                lines.append(line)

        return "\n".join(lines)