from harnesslab.skills import inject_skills, load_skill


def test_load_skill():
    body = load_skill("csv-data-ops")
    assert "csv.DictReader" in body


def test_inject_skills():
    prompt = inject_skills("base", ["file-organization"])
    assert prompt.startswith("base")
    assert '<skill name="file-organization">' in prompt
