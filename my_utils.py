from typing import Optional, Tuple, Union, List, Callable, Dict, Any


# 计算字符串的token数目
def calc_token_num(tokenizer, text):
    tokens = tokenizer.tokenize(text)
    return len(tokens)


# 限制输入的token数在max_length范围内，如果超出，删减history。如果连query都过长，则报错
def inputs_length_fixer(
    tokenizer,
    query: str,
    answer_prefix: str,
    history: List[Tuple[str, str]],
    max_length: int,
):
    tokenUsed = 0
    tokenQueries = calc_token_num(tokenizer, query + answer_prefix)
    # 如果query过长，报错
    if tokenQueries > max_length:
        raise ValueError("query too large.")
    else:
        tokenUsed += tokenQueries
    # 从后往前逐个检查token使用是否超限，略过超限的history
    newHistory = []
    for i in range(len(history) - 1, -1, -1):
        tokenItem = calc_token_num(tokenizer, history[i][0] + history[i][1])
        if tokenItem + tokenUsed < max_length:
            newHistory.insert(0, history[i])
            tokenUsed += tokenItem
        else:
            break

    return newHistory
