import os
from typing import Optional


def instruction_loader(
    instruction_id: str,
    instruction_folder: str = "app/assets/instructions",
    encoding: str = "utf-8",
    default: Optional[str] = None
) -> str:
    """
    Load instructions from a file.

    Args:
        instruction_id (str): The ID of the instruction to load.
        instruction_folder (str): Folder where instruction files are stored.
        encoding (str): File encoding.
        default (Optional[str]): Default value if file is not found.

    Returns:
        str: The instructions loaded from the file.

    Raises:
        FileNotFoundError: If file does not exist and no default is provided.
    """
    instruction_file = os.path.join(instruction_folder, f"{instruction_id}.md")

    if not os.path.exists(instruction_file):
        if default is not None:
            return default
        raise FileNotFoundError(f"Instruction file not found: {instruction_file}")

    with open(instruction_file, "r", encoding=encoding) as file:
        return file.read().strip()