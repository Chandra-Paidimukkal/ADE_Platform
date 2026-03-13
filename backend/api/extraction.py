from fastapi import APIRouter
from core.llm_router import get_llm_router, LLMRequest, LLMMessage, LLMRole

router = APIRouter()


@router.post("/run/{doc_id}")
async def run_extraction(doc_id: str):

    router_llm = get_llm_router()

    prompt = f"""
Extract product specifications from this document.

Fields to extract:
- model_number
- voltage
- amperage
- capacity
- dimensions
- weight
- refrigerant

Return JSON only.
"""

    request = LLMRequest(
        messages=[
            LLMMessage(role=LLMRole.USER, content=prompt)
        ]
    )

    response = await router_llm.complete(request)

    return {
        "doc_id": doc_id,
        "extracted": response.content
    }