from io import BytesIO

import torch
from loguru import logger
from numpy import ndarray
from PIL import Image
from transformers import CLIPProcessor, CLIPTokenizerFast

from src import config


class EmbdExtractionUtils:
    def __init__(self):
        # Load model and other processing utilities
        logger.info("Load jit model and associated utilities")

        self.loaded_model = torch.jit.load(config.EMBD_MODEL_PATH, map_location="cpu").to(
            dtype=config.DTYPE, device=config.DEVICE
        )
        self.loaded_model.eval()

        self.processor = CLIPProcessor.from_pretrained(config.EMBD_MODEL_NAME)
        self.tokenizer = CLIPTokenizerFast.from_pretrained(config.EMBD_MODEL_NAME)

    def get_embd_text(self, text: str | list[str]) -> list[ndarray]:
        token_ids = self.tokenizer(text, return_tensors="pt", padding="max_length", truncation=True)
        embd = (
            self.loaded_model
            .get_text_features(token_ids["input_ids"].to("mps"), token_ids["attention_mask"].to("mps"))
            .to("cpu")
            .detach()
            .numpy()
            .squeeze()
        )  # fmt: skip

        match len(embd.shape):
            case 2:
                output = [v for v in embd]
            case 1:
                output = [embd]
            case _:
                raise ValueError(f"Shape of embd must be less than or equal 2. Got: {embd.shape}")

        return output

    def get_embd_image(self, image_bytes: BytesIO) -> ndarray:
        """Extract embedding from input image

        Args:
            image_bytes (BytesIO): input image (already read into memory)

        Returns:
            ndarray: embedding vector
        """

        image = Image.open(image_bytes)
        out_sample_image = self.processor(images=image, return_tensors="pt")
        embd = (
            self.loaded_model
            .get_image_features(out_sample_image["pixel_values"].to(config.DEVICE))
            .to("cpu")
            .detach()
            .numpy()
            .squeeze()
        )  # fmt: skip

        return embd
