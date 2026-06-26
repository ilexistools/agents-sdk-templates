from app.orchestration import gpt


def translate(text: str):
    translator = gpt.GPT(
        agent_id="translator",
        output_type=gpt.GPTResponse,
    )
    prompt = f"Translate the following text: {text}"
    result = translator.run_sync(prompt)
    return result


if __name__ == "__main__":
    text = "Hello, world!"

    result = translate(text)
    print(result)
