# Scratch: LLMToolSelectorMiddleware usage sketch (CLAUDE.md C2a TODO(future)).
# Not runnable as-is — tool list and model names are placeholders.
#
# from langchain.agents import create_agent
# from langchain.agents.middleware import LLMToolSelectorMiddleware
#
# agent = create_agent(
#     model="<model-id>",
#     tools=[tool1, tool2, tool3, ...],
#     middleware=[
#         LLMToolSelectorMiddleware(
#             model="<fast-model-id>",
#             max_tools=3,
#             always_include=["search"],
#         ),
#     ],
# )
