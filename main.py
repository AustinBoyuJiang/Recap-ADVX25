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
    return merge_pairs([((x, 1), 1) for x in re.findall(r'\b[a-zA-Z]+\b', sentence.lower())])


def split_word(word):
    common_prefixes = ['un', 're', 'in', 'im', 'il', 'ir', 'dis', 'en', 'em', 'non', 'over', 'mis', 'sub', 'pre',
                       'inter', 'fore', 'de', 'trans', 'super', 'semi', 'anti', 'mid', 'under']
    common_suffixes = ['able', 'ible', 'al', 'ial', 'ed', 'en', 'er', 'est', 'ful', 'ic', 'ing', 'ion', 'tion', 'ation',
                       'ition', 'ity', 'ty', 'ive', 'ative', 'itive', 'less', 'ly', 'ment', 'ness', 'ous', 'eous',
                       'ious', 's', 'es', 'y']
    prefixes = []
    suffixes = []
    root = word
    done = False
    while not done:
        done = True
        for p in sorted(common_prefixes, key=lambda x: -len(x)):
            if root.startswith(p):
                prefixes.append(p)
                root = root[len(p):]
                done = False
                break
    done = False
    while not done:
        done = True
        for s in sorted(common_suffixes, key=lambda x: -len(x)):
            if root.endswith(s):
                suffixes.insert(0, s)  # insert at front to preserve order
                root = root[:-len(s)]
                done = False
                break
    return [((x, 2), len(x) / len(word)) for x in (prefixes + suffixes)] + [((x, 3), 1 / len(word)) for x in root]


def split_morpheme(morpheme):
    return merge_pairs([((x, 3), 1 / len(morpheme)) for x in morpheme])


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
    decay_factor = math.log(2) / 3  # half-life time of 3 seconds
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
    for (item_next, depth_next), w in nodes[depth][item]["next"]:
        update(item_next, grade, depth_next, weight * w)


def update_all():
    for depth in range(4):
        for item in nodes[depth].keys():
            update_retention(item, depth)


update("i like eating apple", 5)
time.sleep(2)
update("apple are good to eat", 5)
time.sleep(2)
update("apple is my favourite fruit", 5)
time.sleep(1)
update("I am eating, singing, and dancing because I like eating and it's good to eat when you are enjoying it.", 0)


t = time.time()
retention_queue = [(round((x[0]-t), 2), x[1]) for x in retention_queue if x[1][1] in {1, 2}]
pprint.pprint(retention_queue)
