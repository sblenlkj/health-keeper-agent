#!/usr/bin/env bash
cd /Users/dmitrijkanevskij/VS_CodeProjects/data_science/agents/courses/agents_hse1/hw_open_claw
exec uv run python -m health_agent.entrypoints.mcp
