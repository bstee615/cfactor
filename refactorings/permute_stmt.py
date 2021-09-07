"""Permute Statement: swap 2 independent statements in a basic block."""
import copy

from refactorings.base import SrcMLTransformation


class PermuteStmt(SrcMLTransformation):

    def is_permeable(self, node):
        return self.srcml.tag(node) in ('empty_stmt', 'label', 'break', 'continue', 'return')

    def get_basic_blocks(self):
        """
        Return a list of all basic blocks, where a block is a list of statements.
        Reference implementation: https://github.com/mdrafiqulrabin/tnpa-generalizability/blob/21c98e95f59dd602c78b38cec7dd436e1f2cb22e/JavaMethodTransformer/src/main/java/Common.java
        """
        blocks = []
        current_block = []
        q = [self.srcml.xml_root]
        while len(q) > 0:
            u = q.pop(0)
            # TODO: Handle function calls with ICFG.
            if self.srcml.tag(u) in ('expr_stmt', 'decl_stmt', 'for', 'do', 'while', 'switch') and len(
                    self.srcml.xp(u, './/src:call')) == 0 and not self.is_permeable(u):
                current_block.append(u)
            elif len(current_block) > 1:
                blocks.append(current_block)
                current_block = []
            for v in u:
                q.append(v)
        return blocks

    def independent_stmts(self, basic_block):
        """Return a list of pairs of independent statements in a given basic block"""
        independent = []

        def depends(u, v):
            """
            Return true iff u depends on v.
            TODO: Handle pointer dependencies with IPDG.
            """
            u_ids = set(n.text for n in self.srcml.xp(u, './/src:name[not(ancestor::src:type)]'))
            v_ids = set(n.text for n in self.srcml.xp(v, './/src:name[not(ancestor::src:type)]'))
            shared_ids = u_ids.intersection(v_ids)
            return len(shared_ids)

        # a --> i, b --> j, c --> k
        for i in range(len(basic_block)):
            a = basic_block[i]
            for j in range(i + 1, len(basic_block)):
                b = basic_block[j]

                if depends(a, b):
                    continue
                if depends(b, a):
                    continue

                # check statements in between
                skip = False
                for k in range(i + 1, j):
                    c = basic_block[k]
                    if depends(c, a):
                        skip = True
                        break
                    if depends(b, c):
                        skip = True
                        break
                if not skip:
                    independent.append((a, b))

        return independent

    def get_targets(self, **kwargs):
        basic_blocks = self.get_basic_blocks()
        candidate_blocks = [b for b in basic_blocks if len(b) > 1]
        independent_pairs = []
        for block in candidate_blocks:
            independent_pairs += self.independent_stmts(block)
        return independent_pairs

    def _apply(self, target):
        a, b = target
        try:
            a_parent = a.getparent()
            a_idx = a_parent.index(a)
            a_copy = copy.deepcopy(a)

            b_parent = b.getparent()
            b_idx = b_parent.index(b)
            b_copy = copy.deepcopy(b)

            a_parent.remove(a)
            a_parent.insert(a_idx, b_copy)

            b_parent.remove(b)
            b_parent.insert(b_idx, a_copy)

            self.srcml.apply_changes()
        except Exception:
            self.srcml.revert_changes()
            raise

        new_text = self.srcml.load_c_code()
        return new_text.splitlines(keepends=True)
