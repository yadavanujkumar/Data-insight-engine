from typing import Any, Callable, Dict


def _fallback_graph(registry):
    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        quality_service = registry.get("quality")
        recommendation_service = registry.get("recommendation")
        dataset = state.get("dataset")
        if dataset is None:
            return {"error": "dataset is required"}
        quality = quality_service.execute({"dataset": dataset}) if quality_service else {}
        recommendations = (
            recommendation_service.execute({"dataset": dataset}) if recommendation_service else {}
        )
        return {"quality": quality, "recommendations": recommendations}

    return run


def build_quality_recommendation_graph(registry) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    try:
        from langgraph.graph import END, START, StateGraph

        class State(dict):
            pass

        graph = StateGraph(State)

        def quality_node(state: Dict[str, Any]) -> Dict[str, Any]:
            quality_service = registry.get("quality")
            dataset = state.get("dataset")
            if quality_service and dataset is not None:
                state["quality"] = quality_service.execute({"dataset": dataset})
            return state

        def recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
            recommendation_service = registry.get("recommendation")
            dataset = state.get("dataset")
            if recommendation_service and dataset is not None:
                state["recommendations"] = recommendation_service.execute({"dataset": dataset})
            return state

        graph.add_node("quality", quality_node)
        graph.add_node("recommendation", recommendation_node)
        graph.add_edge(START, "quality")
        graph.add_edge("quality", "recommendation")
        graph.add_edge("recommendation", END)
        compiled = graph.compile()
        return lambda state: compiled.invoke(state)
    except ImportError:
        return _fallback_graph(registry)
