from pathlib import Path
import subprocess
import tempfile
import difflib


def lines_arg(line_nums):
    lines = []
    for r in line_nums:
        if len(r) == 0:
            break
        if len(r) == 1:
            r = [r[0], r[0]]
        lines.append(f'--lines={r[0]}:{r[-1]}')
    return lines

def count_diff(old_lines, new_lines):
    """Return the line numbers where there are additions, indexed in the new file."""
    differ = difflib.Differ()
    diffs = differ.compare(old_lines, new_lines)
    r = []
    line_nums = []
    lineno = 0
    for line in diffs:
        if line[0] in (' ', '+'):
            lineno += 1
        if line[0] == '+':
            if len(r) == 0 or r[-1] == lineno-1:
                r.append(lineno)
            else:
                line_nums.append(r)
                r = [lineno]
    line_nums.append(r)
    return line_nums

def reformat(old_lines, new_lines):
    line_nums = count_diff(old_lines, new_lines)

    # No differences
    if len(line_nums) == 0:
        return old_lines

    # Prepare clang command
    lines = lines_arg(line_nums)
    style = '-style="{BasedOnStyle: llvm, IndentWidth: 4}"'
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpfile = tmpdir / 'tmp.c'
        with open(tmpfile, 'w') as f:
            f.writelines(new_lines)
        subprocess.run(f'clang-format {" ".join(lines)} {f.name} -i {style}', shell=True, capture_output=True, check=True)
        with open(tmpfile, 'r') as f:
            return f.readlines()
