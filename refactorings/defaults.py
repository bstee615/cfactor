def random_picker(targets, **kwargs):
    rng = kwargs.get("rng")
    assert len(targets) > 0, 'Collection is empty'
    return rng.choice(targets)


def first_picker(targets, **kwargs):
    assert len(targets) > 0, 'Collection is empty'
    return targets[0]
