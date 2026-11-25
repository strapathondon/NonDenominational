"""Validate question-set files. Run with Python 3.10+ and jsonschema 4.18+."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent


def read(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))


def check(ok, message):
    if not ok:
        raise ValueError(message)


def matches(condition, selections, *, asked=(), confirmed=(), variants=None):
    """Evaluate one guided or optional rule against the current eligible responses."""
    if isinstance(condition, bool):
        return condition
    operator, value = next(iter(condition.items()))
    if operator == "selectedAny":
        return any(option in selections.get(option.split("/")[0], ()) for option in value)
    if operator == "answered":
        return bool(selections.get(value))
    if operator == "unasked":
        return value not in asked and not selections.get(value)
    if operator == "confirmed":
        return value in confirmed
    if operator == "variant":
        return (variants or {}).get(value["groupId"]) == value["questionId"]
    results = (matches(child, selections, asked=asked, confirmed=confirmed, variants=variants)
               for child in value)
    if operator == "any":
        return any(results)
    if operator == "all":
        return all(results)
    raise ValueError(f"Unknown condition operator {operator}")


def check_rule(condition, preceding, choices, members):
    if isinstance(condition, bool):
        return
    key, value = next(iter(condition.items()))
    if key in ("all", "any"):
        for child in value:
            check_rule(child, preceding, choices, members)
    elif key in ("answered", "unasked"):
        check(value in preceding, f"Unknown or forward question {value}")
    elif key == "selectedAny":
        for option in value:
            check(option in choices and option.split("/")[0] in preceding,
                  f"Unknown or forward choice {option}")
    elif key == "variant":
        check(value["questionId"] in members.get(value["groupId"], ()), f"Unknown draft variant {value}")


def validate():
    catalog = read("index.json")["sets"]
    check(len({r['id'] for r in catalog}) == len(catalog), "Repeated set ID")
    sets = [read(r['file']) for r in catalog]
    schema = read("question-set.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    term_ids = [t['id'] for bank in sets for t in bank['vocabulary']]
    check(len(term_ids) == len(set(term_ids)), "Repeated vocabulary ID")
    source_ids = {r['id'] for r in read("vocabulary-sources.json")}
    seen, options, dims, related = set(), set(), set(), []
    questions, prior_answers = {}, []
    for bank, entry in zip(sets, catalog):
        validator.validate(bank)
        check(entry['id'] == bank['id'], "Catalog and file disagree")
        before = set()
        groups = bank.get("variantGroups", [])
        members = [mid for group in groups for mid in group['members']]
        check(len(members) == len(set(members)), "Overlapping variant groups")
        for group in groups:
            check(group["selected"] is None or group["selected"] in group["members"], "Invalid active variant")
        for section in bank['sections']:
            dimension = section["dimensionId"]
            if dimension is not None:
                check(dimension not in dims, f"Repeated dimension {dimension}")
                dims.add(dimension)
            for q in section["questions"]:
                qid = q["id"]
                check(qid not in seen, f"Repeated question {qid}")
                for rule in [*q["display"].values(), q.get("recommendWhen", True)]:
                    check_rule(rule, before, options, {g["id"]: g["members"] for g in groups})
                before.add(qid)
                seen.add(qid)
                questions[qid] = q
                labels = set()
                for c in q['choices']:
                    check(c['id'].startswith(qid + "/") and c['id'] not in options, f"Invalid ID {c['id']}")
                    check(c['label'] not in labels, f"Repeated label in {qid}")
                    check(not c.get('exclusive') or q['selection'] == 'multiple', f"Unexpected exclusive flag in {qid}")
                    labels.add(c['label'])
                    options.add(c['id'])
                prior_answers.extend(q.get("reviewPriorAnswers", []))
                glossary = set()
                for link in q.get("vocabularyLinks", []):
                    term = link["termId"]
                    check(term in term_ids and term not in glossary, f"Invalid vocabulary link {qid}/{term}")
                    if link["placement"] == "inline":
                        check(q["prompt"].count(link["anchor"]) == 1, f"Ambiguous inline anchor in {qid}")
                    glossary.add(term)
        for term in bank['vocabulary']:
            for citation in term['references']:
                check(any(citation == src or citation.startswith(src + " ") for src in source_ids),
                      f"Undefined vocabulary source {citation}")
        related.extend(bank.get("relatedSets", []))
        check(set(members) <= before, "Missing variant")
        check(before.isdisjoint(bank.get("retiredQuestionIds", [])), "Retired ID used")
        check(bank["featuredQuestionId"] is None or bank["featuredQuestionId"] in before, "Invalid featured ID")
    check(set(related) <= {b['id'] for b in sets}, "Missing related set")
    check(set(prior_answers) <= seen, "Missing reusable question")
    print(f"{len(sets)} sets, {len(dims)} taxonomy dimensions, {len(questions)} question entries, "
          f"{len(options)} choices, {len(term_ids)} vocabulary entries")
    return questions


if __name__ == "__main__":
    validate()
