import base64
import json
import re

import torch
from loguru import logger
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

from src import config

pat = r"\s{2,}"


class KeywordExtractionUtils:
    def __init__(self) -> None:
        self.processor = AutoProcessor.from_pretrained(config.KEYWORD_MODEL_NAME)
        with open(config.PROMPTS_PATH) as file:
            self.prompts = json.load(file)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            config.KEYWORD_MODEL_NAME, torch_dtype=torch.float16, device_map="mps"
        )

    def extract_keyword(self, img: bytes) -> list[dict]:
        # output: [{'word': 'abc', 'category': 'def'}]

        # Prepare image and text as input
        img_base64 = base64.b64encode(img).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": f"data:image/jpeg;base64,{img_base64}",
                    },
                    {"type": "text", "text": self.prompts["characteristics"]},
                ],
            }
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, _ = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            padding=True,
            return_tensors="pt",
        ).to(config.DEVICE)

        # Feed into model to extract keywords
        generated_ids = self.model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        if not isinstance(output, list) and len(output) != 1:
            raise ValueError(f"Expect 'output' is list with len = 1. Got: {output}")

        text_gen = output[0]

        logger.debug(f"text_gen: {text_gen}")

        # Post-process text
        text_gen = re.sub(pat, "\n", text_gen).lower()

        suffixes = self.prompts["suffixes"]

        keywords = {}
        for suffix, v in suffixes.items():
            try:
                word = re.findall(v["pat"], text_gen)[0][0]
                word = word.replace(" ", "-")
                if v["filling_word"] is not None:
                    word = f"{word}-{v['filling_word']}"

                keywords[suffix] = word
            except IndexError:
                continue

        output = [{"word": word, "category": category} for category, word in keywords.items()]

        logger.debug(json.dumps(output, indent=2, ensure_ascii=False))

        return output
