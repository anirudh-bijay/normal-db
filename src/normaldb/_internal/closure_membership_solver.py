from collections.abc import Iterable


class ClosureMembershipSolver:
    """
    Check if a functional dependency *X* → *A* is in the closure of a set of
    functional dependencies *F*. Algorithm 2 from [1] is used.

    References
    ----------
    1. Catriel Beeri and Philip A. Bernstein. “Computational problems
       related to the design of normal form relational schemas”. In: _ACM
       Trans. Database Syst._ 4.1 (Mar. 1979), pp. 30-59. ISSN: 0362-5915.
       doi: [10.1145/320064.320066](https://doi.org/10.1145/320064.320066).
    """

    def __init__(
        self, functional_deps: Iterable[tuple[frozenset[int], frozenset[int]]]
    ):
        """
        Initialise the solver for the membership problem for functional
        dependencies as described in algorithm 2 of [1].

        :param functional_deps:
            An iterable of tuples where each tuple represents a functional
            dependency (FD). Each tuple should be of the form ``(lhs, rhs)``,
            where ``lhs`` and ``rhs`` are sets of attribute indices on the
            left-hand and right-hand sides of the FD, respectively.

            Attribute indices should be non-negative integers. The
            indices should be in the range [0, *n*) where *n* is the number of
            attributes in the schema. While larger indices will work, the
            memory usage of the solver will be proportional to the largest index
            in the FDs.
        """

        self.functional_deps = tuple(functional_deps)

        self.counter = [0] * len(self.functional_deps)
        self.attrlist = list[set[int]]()
        self._lhs = frozenset[int]()
        self.rhs: int
        """
        The RHS of the FD whose membership in the closure to check. This is a
        non-negative attribute index.
        """

        for i, (lhs, _) in enumerate(self.functional_deps):
            for j in lhs:
                if len(self.attrlist) <= j:
                    self.attrlist.extend(
                        set[int]() for _ in range(j - len(self.attrlist) + 1)
                    )
                self.attrlist[j].add(i)
                self.counter[i] += 1

    @property
    def lhs(self) -> frozenset[int]:
        """
        The LHS of the FD whose membership in the closure to check. This
        is a set of non-negative attribute indices.
        """

        return self._lhs

    @lhs.setter
    def lhs(self, value: Iterable[int]) -> None:
        """
        :param value:
            The LHS of the FD, a set of non-negative attribute indices.
        """

        self._lhs = frozenset(value)

        self._depend = set(self.lhs)
        newdepend = self._depend.copy()
        counter = self.counter.copy()

        while newdepend:
            next_to_check = newdepend.pop()
            if next_to_check >= len(self.attrlist):
                continue
            for i in self.attrlist[next_to_check]:
                counter[i] -= 1
                if counter[i] == 0:
                    for j in self.functional_deps[i][1]:
                        if j not in self._depend:
                            self._depend.add(j)
                            newdepend.add(j)

    def is_member(self) -> bool:
        """
        Return whether the FD with the current LHS and RHS is in the closure.
        """

        return self.rhs in self._depend
