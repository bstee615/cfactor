def join_str(*args):
    return ''.join(str(s) if s is not None else '' for s in args)