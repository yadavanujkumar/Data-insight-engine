from typing import Any, Callable, Dict, List


def _fallback_tool(name: str, description: str, func: Callable[..., Any]) -> Dict[str, Any]:
    return {"name": name, "description": description, "callable": func, "provider": "fallback"}


def get_langchain_tools(registry) -> List[Any]:
    quality_service = registry.get("quality")
    recommendation_service = registry.get("recommendation")

    tools: List[Any] = []

    try:
        from langchain_core.tools import tool

        if quality_service:
            @tool("compute_quality")
            def compute_quality(dataset):
                """Compute quality score for a dataset."""
                return quality_service.execute({"dataset": dataset})

            tools.append(compute_quality)

        if recommendation_service:
            @tool("generate_recommendations")
            def generate_recommendations(dataset):
                """Generate recommendations for a dataset."""
                return recommendation_service.execute({"dataset": dataset})

            tools.append(generate_recommendations)
        return tools
    except ImportError:
        if quality_service:
            tools.append(
                _fallback_tool(
                    "compute_quality",
                    "Compute quality score for a dataset.",
                    lambda dataset: quality_service.execute({"dataset": dataset}),
                )
            )
        if recommendation_service:
            tools.append(
                _fallback_tool(
                    "generate_recommendations",
                    "Generate recommendations for a dataset.",
                    lambda dataset: recommendation_service.execute({"dataset": dataset}),
                )
            )
        return tools
