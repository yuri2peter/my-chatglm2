import torch
import types
from typing import Optional, Tuple, Union, List, Callable, Dict, Any
from transformers.generation.logits_process import LogitsProcessor
from transformers.generation.utils import (
    LogitsProcessorList,
)
from transformers import AutoTokenizer, AutoModel

DEVICE = "cuda"
DEVICE_ID = "0"
CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}" if DEVICE_ID else DEVICE


class InvalidScoreLogitsProcessor(LogitsProcessor):
    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor
    ) -> torch.FloatTensor:
        if torch.isnan(scores).any() or torch.isinf(scores).any():
            scores.zero_()
            scores[..., 5] = 5e4
        return scores


def my_decorator(func):
    @torch.no_grad(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


def my_build_inputs(
    self, tokenizer, query: str, history: List[Tuple[str, str]], answer_prefix=""
):
    prompt = ""
    for i, (old_query, response) in enumerate(history):
        prompt += f"[Round {i + 1}]\n\n问：{old_query}\n\n答：{response}\n\n"
    prompt += f"[Round {len(history) + 1}]\n\n问：{query}\n\n答：{answer_prefix}"
    inputs = tokenizer([prompt], return_tensors="pt")
    inputs = inputs.to(self.device)
    return inputs


@torch.no_grad()
def my_stream_chat(
    self,
    tokenizer,
    query: str,
    history: List[Tuple[str, str]] = None,
    max_length: int = 2048,
    do_sample=True,
    top_p=0.8,
    temperature=0.8,
    logits_processor=None,
    answer_prefix="",
    allow_generate=[1],
    **kwargs,
):
    allow_generate[0] = True
    if history is None:
        history = []
    if logits_processor is None:
        logits_processor = LogitsProcessorList()
    logits_processor.append(InvalidScoreLogitsProcessor())
    gen_kwargs = {
        "max_length": max_length,
        "do_sample": do_sample,
        "top_p": top_p,
        "temperature": temperature,
        "logits_processor": logits_processor,
        **kwargs,
    }
    inputs = self.my_build_inputs(
        tokenizer, query, history=history, answer_prefix=answer_prefix
    )
    for outputs in self.stream_generate(
        **inputs,
        past_key_values=None,
        return_past_key_values=False,
        **gen_kwargs,
    ):
        outputs = outputs.tolist()[0][len(inputs["input_ids"][0]) :]
        response = tokenizer.decode(outputs)
        response = answer_prefix + self.process_response(response)
        new_history = history + [(query, response)]
        yield response, new_history
        if not allow_generate[0]:
            break
    torch_gc()


# 获取 tokenizer 和 model
def get_tokenizer_and_model(bits=4):
    modelPath = "THUDM/chatglm2-6b"
    print(f"Using model: {modelPath}(bits {bits})")
    tokenizer = AutoTokenizer.from_pretrained(
        modelPath, trust_remote_code=True, revision="v1.0"
    )
    model = (
        AutoModel.from_pretrained(modelPath, trust_remote_code=True, revision="v1.0")
        .quantize(bits)
        .cuda()
    )
    model.eval()
    model.my_build_inputs = types.MethodType(my_build_inputs, model)
    model.my_stream_chat = types.MethodType(my_stream_chat, model)
    return tokenizer, model


# tokenizer, model = getTokenizerAndModel()
