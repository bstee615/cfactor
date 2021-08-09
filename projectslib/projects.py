import pandas as pd
import dataclasses
from path import Path

code_root = Path('tests')

@dataclasses.dataclass
class ProjectInfo:
    program: str
    buggy: str
    ok: str

    def __post_init__(self):
        if self.program == 'find':
            self.program = 'findutils'
        self.init_paths()

    def init_paths(self) -> str:
        self.program_path = code_root / self.program
        self.buggy_path = self.program_path / self.buggy
        self.ok_path = self.program_path / self.buggy
        if self.program in ['coreutils', 'findutils', 'grep', 'make']:
            self.buggy_path = self.buggy_path / self.program
            self.ok_path = self.ok_path / self.program
        assert self.buggy_path.exists(), self.buggy_path
        assert self.ok_path.exists(), self.ok_path

def get_iter(project_filter):
    df = pd.read_csv('all.csv')
    
    for _, row in df.iterrows():
        if row["Program"] in project_filter:
            yield ProjectInfo(row["Program"], row["Intro Commit ID"], row["Fixed Commit ID"])

def get(project_filter):
    return list(get_iter(project_filter))
