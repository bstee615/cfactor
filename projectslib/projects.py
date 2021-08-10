import pandas as pd
from dataclasses import dataclass, field
from path import Path

code_root = Path('tests')

@dataclass(unsafe_hash=True)
class ProjectInfo:
    program: str = field(hash=True)
    buggy: str = field(hash=True)
    ok: str = field(hash=True)

    def __post_init__(self):
        if self.program == 'find':
            self.program = 'findutils'
        self.init_paths()
        self.replace_unicode()
    
    @property
    def versions(self):
        return self.buggy, self.ok
    
    @property
    def versions_with_paths(self):
        return zip((self.buggy, self.ok), (self.buggy_path, self.ok_path))

    def init_paths(self) -> str:
        self.program_path = code_root / self.program
        self.buggy_path = self.program_path / self.buggy
        self.ok_path = self.program_path / self.buggy
        if self.program in ['coreutils', 'findutils', 'grep', 'make']:
            self.buggy_path = self.buggy_path / self.program
            self.ok_path = self.ok_path / self.program
        assert self.buggy_path.exists(), self.buggy_path
        assert self.ok_path.exists(), self.ok_path

    def replace_unicode(self):
        files = list(self.buggy_path.glob('**/*.c') + self.buggy_path.glob('*.c') + self.ok_path.glob('**/*.c') + self.ok_path.glob('*.c'))
        for fname in files:
            with open(fname, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(text)

def get_iter(project_filter):
    df = pd.read_csv('nb/all.csv')
    
    for _, row in df.iterrows():
        if row["Program"] in project_filter:
            yield ProjectInfo(row["Program"], row["Intro Commit ID"], row["Fixed Commit ID"])

def get(project_filter):
    projects = list(get_iter(project_filter))
    from projectslib.groundtruth import get_all
    projects = get_all(projects)
    projects = sorted(projects, key=lambda p: str(p.program_path))
    return projects
