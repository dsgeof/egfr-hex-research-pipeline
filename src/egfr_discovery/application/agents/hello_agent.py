import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Scientific Assistant",
    instructions=(
        "You are a cautious computational drug-discovery assistant. "
        "Explain concepts clearly. Never describe computational predictions "
        "as experimentally validated drug candidates."
    ),
)

async def run_agent() -> None:
    result = await Runner.run(
        agent,
        "Explain the difference between a predicted active compound "
        "and an experimentally validated active compound.",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(run_agent())