from busmora_ai_contracts import ACTIVITIES, ActivityName, TaskQueue


def test_every_activity_name_has_exactly_one_spec() -> None:
    names = [spec.name for spec in ACTIVITIES]
    assert sorted(names) == sorted(ActivityName)


def test_activity_owner_prefix_matches_its_task_queue() -> None:
    prefixes = {TaskQueue.AI_AGENT: "ai.", TaskQueue.AI_CRAWL: "crawl."}
    for spec in ACTIVITIES:
        assert spec.name.startswith(prefixes[spec.task_queue]), spec.name


def test_long_running_activities_heartbeat() -> None:
    for spec in ACTIVITIES:
        if spec.start_to_close_seconds > 60:
            assert spec.heartbeat_seconds is not None, spec.name
