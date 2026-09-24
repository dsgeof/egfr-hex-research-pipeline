import asyncio

from agents import Agent, Runner, function_tool
from egfr_discovery.application.agents.schemas import CandidateReview, CandidateConcern


CANDIDATES = {
    "CMP-101": {
        "predicted_probability": 0.91,
        "uncertainty": 0.08,
        "nearest_training_similarity": 0.95,
        "structural_alerts": [],
    },
    "CMP-102": {
        "predicted_probability": 0.84,
        "uncertainty": 0.31,
        "nearest_training_similarity": 0.43,
        "structural_alerts": ["reactive electrophile"],
    },
}


@function_tool
def get_candidate_details(compound_id: str) -> dict[str, object]:
    """Return model and quality information for one candidate compound."""
    candidate = CANDIDATES.get(compound_id)

    if candidate is None:
        return {
            "found": False,
            "compound_id": compound_id,
        }

    return {
        "found": True,
        "compound_id": compound_id,
        **candidate,
    }


review_agent = Agent(
    name="Candidate Review Agent",
    instructions=(
        "You review computationally predicted compounds. "
        "Always call get_candidate_details before evaluating a candidate. "
        "Flag high similarity to training data as possible analogue recovery. "
        "Flag structural alerts. "
        "State uncertainty. "
        "Do not claim a compound is a drug or experimentally active."
    ),
    tools=[get_candidate_details],
    output_type=CandidateReview,
)


async def main() -> None:
    result = await Runner.run(
        review_agent,
        "Review CMP-102",
    )

    review = result.final_output
    print("\n\n")
    print("******Candidate Review******")
    print(review.compound_id)
    print("\n")
    print("Recommendation:")
    print(review.recommendation)
    print("\n")
    print("Concerns:")
    print(review.concerns)
    print("\n")
    print("Rationale:")
    print(review.rationale)



if __name__ == "__main__":
    asyncio.run(main())