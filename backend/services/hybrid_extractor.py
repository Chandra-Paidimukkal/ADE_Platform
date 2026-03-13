import re


def rule_extract(text):

    voltage = re.search(r"\d+\s?V", text)
    amps = re.search(r"\d+\.?\d*\s?A", text)

    return {
        "voltage": voltage.group() if voltage else None,
        "amperage": amps.group() if amps else None
    }


async def ai_extract(text, router):

    from core.llm_router import LLMRequest

    request = LLMRequest(
        messages=[
            {"role": "user", "content": text}
        ],
        system_prompt="Extract model, voltage, amperage"
    )

    response = await router.complete(request)

    return response.content


async def hybrid_extract(text, router):

    rules = rule_extract(text)

    if rules["voltage"]:

        return rules

    return await ai_extract(text, router)