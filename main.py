import re
import time
import math
import pprint
from collections import defaultdict
from sortedcontainers import SortedSet


def merge_pairs(pairs):
    counter = defaultdict(int)
    for key, value in pairs:
        counter[key] += value
    return list(counter.items())


def split_sentence(sentence):
    return merge_pairs([(x, 1) for x in re.findall(r'\b[a-zA-Z]+\b', sentence)])


def split_word(word):  # can be improved using unsupervised learning
    prefixes = [
        "un", "re", "in", "im", "dis", "pre", "mis", "non", "over", "under", "inter", "sub", "trans"
    ]
    suffixes = [
        "able", "ible", "ing", "ed", "tion", "sion", "ment", "ness", "ly", "ous", "ive", "al", "est", "er", "less",
        "ful", "s"
    ]
    word = word.lower()
    prefix_match = None
    suffix_match = None
    for prefix in sorted(prefixes, key=len, reverse=True):
        if word.startswith(prefix):
            prefix_match = prefix
            word = word[len(prefix):]
            break
    for suffix in sorted(suffixes, key=len, reverse=True):
        if word.endswith(suffix):
            suffix_match = suffix
            word = word[:-len(suffix)]
            break
    return merge_pairs(
        [(x, len(x) / len(word)) for x in [prefix_match, word, suffix_match] if (x is not None) and (x is not word)])


def split_morpheme(morpheme):
    return merge_pairs([(x, 1 / len(morpheme)) for x in morpheme])


def split_letter(letter):
    return []


def update_ease_factor(ef, grade):
    ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    return max(ef, 1.3)


retention_threshold = 0.8
split_function = [split_sentence, split_word, split_morpheme, split_letter]
nodes = [{}, {}, {}, {}]
retention_queue = SortedSet()


def new_node(item, depth):
    time_ = time.time()
    retention = 1
    decay_factor = math.log(2)/3  # half-life time of 60 seconds
    ease_factor = 2.5
    time_last = time_ + math.log(retention) * ease_factor / decay_factor
    time_next = time_last - math.log(retention_threshold) * ease_factor / decay_factor
    retention_queue.add((time_next, (item, depth)))
    return {
        "retention": retention,
        "time": time_,
        "time_last": time_last,
        "time_next": time_next,
        "decay_factor": decay_factor,
        "ease_factor": ease_factor,
        "next": split_function[depth](item),
        "history": {
            time_: {
                "time_last": time_last,
                "ease_factor": ease_factor,
            }
        },
    }


def update_retention(item, depth):
    nodes[depth][item]["time"] = time.time()
    time_ = nodes[depth][item]["time"]
    time_last = nodes[depth][item]["time_last"]
    decay_factor = nodes[depth][item]["decay_factor"]
    ease_factor = nodes[depth][item]["ease_factor"]
    nodes[depth][item]["retention"] = math.exp(-decay_factor / ease_factor * (time_ - time_last))


def update_node(item, grade, weight, depth):
    if item not in nodes[depth]:
        nodes[depth][item] = new_node(item, depth)
    time_ = time.time()
    time_last = nodes[depth][item]["time_last"] + (time_ - nodes[depth][item]["time_last"]) * weight
    nodes[depth][item]["time_last"] = time_last
    ease_factor = update_ease_factor(nodes[depth][item]["ease_factor"], grade)
    nodes[depth][item]["ease_factor"] = ease_factor
    nodes[depth][item]["history"][time_] = {
        "time_last": time_last,
        "ease_factor": ease_factor,
    }
    decay_factor = nodes[depth][item]["decay_factor"]
    time_next = nodes[depth][item]["time_next"]
    retention_queue.discard((time_next, (item, depth)))
    time_next = time_last - math.log(retention_threshold) * ease_factor / decay_factor
    nodes[depth][item]["time_next"] = time_next
    retention_queue.add((time_next, (item, depth)))
    update_retention(item, depth)


def update(item, grade, depth=0, weight=1):
    update_node(item, grade, weight, depth)
    for item_next, w in nodes[depth][item]["next"]:
        update(item_next, grade, depth + 1, weight * w)

def update_all():
    for depth in range(4):
        for item in nodes[depth].keys():
            update_retention(item, depth)


# sentence = "The unsuccessful presentation caused considerable disappointment among international investors."
# sentence = sentence.lower()
update("i like eating apple", 5)
time.sleep(2)
update("apple are good to eat", 5)
time.sleep(2)
update("apple is my favourite fruit", 5)
time.sleep(1)

update_all()
t = time.time()
retention_queue = [(round((x[0]-t), 2), x[1]) for x in retention_queue if x[1][1] in {1, 2}]
pprint.pprint(retention_queue)
pprint.pprint(nodes)