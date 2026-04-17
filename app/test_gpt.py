from app.orchestration import gpt 
from app.orchestration.util import instruction_loader


def translate(text: str):
        translator = gpt.GPT(
        name="Translator",
        role="You are a helpful assistant that translates text.",
        instructions=instruction_loader("translator"),
        model="gpt-4.1-mini",
        output_type=gpt.GPTResponse
        )
        prompt = f"Translate the following text: {text}"
        result = translator.run_sync(prompt)
        return result

if __name__ == "__main__":
        text = "Hello, world!"

        result = translate(text)
        print(result)

