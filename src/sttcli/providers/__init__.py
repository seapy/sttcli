from sttcli.providers.base import BaseProvider


def get_provider(name: str) -> type[BaseProvider]:
    if name == "whisper":
        from sttcli.providers.whisper_local import WhisperProvider
        return WhisperProvider
    elif name == "openai":
        from sttcli.providers.openai_api import OpenAIProvider
        return OpenAIProvider
    elif name == "gemini":
        from sttcli.providers.gemini import GeminiProvider
        return GeminiProvider
    elif name == "elevenlabs":
        from sttcli.providers.elevenlabs import ElevenLabsProvider
        return ElevenLabsProvider
    else:
        raise ValueError(f"Unknown provider: {name}")
