import os
from dotenv import load_dotenv

load_dotenv()

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, START, StateGraph

# psycopg is optional for the UI use-case; if it's missing we still allow non-checkpoint runs
try:
    import psycopg
    from langgraph.checkpoint.postgres import PostgresSaver
except ModuleNotFoundError:  # pragma: no cover
    psycopg = None
    PostgresSaver = None

from rich import print

from tools.flight_tool import search_flight
from tools.tavily_tool import tavily_search


llm = ChatMistralAI(model="mistral-large-latest", temperature=0.7)

tools = [search_flight, tavily_search]

database_url = os.getenv("DATABASE_URL")


class TravelPlan(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_info: str
    itinerary_info: str
    hotel_info: str
    llm_calls: int


def flight_agent(state: TravelPlan) -> TravelPlan:
    query = state["user_query"]
    flight_info = search_flight(query)
    return {
        "flight_info": flight_info,
        "messages": [AIMessage(content=f"Flight info retrieved: {flight_info}")],
    }


def hotel_agent(state: TravelPlan) -> TravelPlan:
    query = f"Find hotels in {state['user_query']} and provide details."
    hotel_results = tavily_search(query)
    return {
        "hotel_info": hotel_results,
        "messages": [AIMessage(content=f"Hotel info retrieved: {hotel_results}")],
    }


def itinerary_agent(state: TravelPlan) -> TravelPlan:
    query = (
        "Create a travel itinerary based on the following flight and hotel information:\n"
        f"Flight Info: {state['flight_info']}\n"
        f"Hotel Info: {state['hotel_info']} and user query: {state['user_query']}"
    )
    itinerary_response = llm.invoke(
        [
            SystemMessage(
                content="You are a travel assistant that creates itineraries based on flight and hotel information based on user query."
            ),
            HumanMessage(content=query),
        ]
    )
    return {
        "itinerary_info": itinerary_response.content,
        "messages": [itinerary_response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def final_agent(state: TravelPlan) -> TravelPlan:
    final_prompt = (
        "Generate final travel response:\n"
        f"Flight Info: {state['flight_info']}\n"
        f"Hotel Info: {state['hotel_info']}\n"
        f"Itinerary: {state['itinerary_info']}"
    )
    response = llm.invoke([HumanMessage(content=final_prompt)])
    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


builder = StateGraph(TravelPlan)

builder.add_node("flight_agent", flight_agent)
builder.add_node("hotel_agent", hotel_agent)
builder.add_node("itinerary_agent", itinerary_agent)
builder.add_node("final_agent", final_agent)

builder.add_edge(START, "flight_agent")
builder.add_edge("flight_agent", "hotel_agent")
builder.add_edge("hotel_agent", "itinerary_agent")
builder.add_edge("itinerary_agent", "final_agent")
builder.add_edge("final_agent", END)

# if psycopg is None or PostgresSaver is None or not database_url:
#     # fallback: no postgres checkpointing
#     graph = builder.compile()
# else:
#     conn = psycopg.connect(database_url, autocommit=True)
#     checkpointer = PostgresSaver(conn)
#     checkpointer.setup()
#     graph = builder.compile(checkpointer=checkpointer)

graph = builder.compile()

print(graph)



def run_travel_planner(user_input: str, thread_id: str = "1"):
    """Run the full multi-agent travel planner and return LangGraph output."""

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    result = graph.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
        },
        config=config,
    )
    return result


if __name__ == "__main__":
    user_input = input("Enter the travel request: \n")
    result = run_travel_planner(user_input)

    print("\n Final response: \n")
    for i in result["messages"]:
        print(i.content)

    print(result)

