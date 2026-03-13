from services.model_detector import detect_models
from services.hybrid_extractor import hybrid_extract
from core.llm_router import llm_router


class DocumentAgent:

    async def run(self, text):

        models = detect_models(text)

        specs = await hybrid_extract(text, llm_router)

        return {
            "models": models,
            "specs": specs
        }