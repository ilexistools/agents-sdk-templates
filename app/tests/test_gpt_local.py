from app.orchestration.gpt_local import GPTLocal, GPTLocalResponse


def translate(text: str):
    translator = GPTLocal(
        agent_id="translator",
        output_type=GPTLocalResponse,
    )
    prompt = f"Translate the following text: {text}"
    result = translator.run_sync(prompt)
    return result


if __name__ == "__main__":
    text = "Hello, world!"

    result = translate(text)
    print(result)
