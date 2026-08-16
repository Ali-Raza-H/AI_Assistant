import sounddevice as sd
from kokoro import KPipeline as kp

# -------- kokoro settings ---------

pipeline = kp(
    lang_code = "a",
    repo_id = "hexgrad/Kokoro-82M"
)
voice = "af_sarah"
speed = 1
split = r"\n+"


def speak(inp):

    generator = pipeline(
        inp,
        voice = voice,
        speed = speed,
        split_pattern = split
    )

    for graphemes, phonemes, audio in generator:

        if audio is not None:
            print("Speaking: ", graphemes)

            sd.play(audio, samplerate=24000)
            sd.wait()
