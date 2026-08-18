from backend.ciel.runtime.logging import log


voice = "af_sarah"
speed = 1
split = r"\n+"
_pipeline = None


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        from kokoro import KPipeline
    except ModuleNotFoundError:
        log("warning", "speech.py: kokoro is not installed; speech disabled")
        return None
    _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    return _pipeline


def speak(inp):
    try:
        import sounddevice as sd
    except ModuleNotFoundError:
        log("warning", "speech.py: sounddevice is not installed; speech disabled")
        return

    pipeline = _load_pipeline()
    if pipeline is None:
        return

    generator = pipeline(
        inp,
        voice=voice,
        speed=speed,
        split_pattern=split,
    )

    for graphemes, phonemes, audio in generator:
        if audio is not None:
            print("Speaking: ", graphemes)
            sd.play(audio, samplerate=24000)
            sd.wait()
