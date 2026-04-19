from collections.abc import Hashable, Iterable
from typing import overload

from normaldb._internal.closure_membership_solver import ClosureMembershipSolver


class SchemaBuilder:
    """
    Builder for a 3NF database schema. The schema is created from a set of
    attributes, a set of candidate keys, and a set of functional dependencies.

    Algorithm 2 from [1] is used to synthesise the schema.

    References
    ----------
    1. Philip A. Bernstein. “Synthesizing third normal form relations from
       functional dependencies”. In: _ACM Trans. Database Syst._ 1.4 (Dec.
       1976), pp. 277-298. ISSN: 0362-5915.
       doi: [10.1145/320493.320489](https://doi.org/10.1145/320493.320489).
    """

    def __init__(
        self,
        attributes: Iterable[Hashable] = set(),
        keys: Iterable[Iterable[Hashable]] = set(),
        functional_deps: Iterable[
            tuple[Iterable[Hashable], Iterable[Hashable]]
        ] = set(),
    ):
        """
        Initialise the schema builder with the given attributes and
        functional dependencies.

        :param attributes:
            A set of hashable objects representing the attributes in the
            schema. Duplicate attributes will be ignored.

        :param keys:
            A set of sets of attributes representing the candidate keys
            in the schema. A candidate key is a minimal set of attributes
            that functionally determines all other attributes in the schema.

        :param functional_deps:
            A set of tuples where each tuple represents a functional
            dependency (FD). Each tuple should be of the form ``(lhs, rhs)``,
            where ``lhs`` and ``rhs`` are iterables of attributes on the
            left-hand and right-hand sides of the FD, respectively.

            The FDs will be understood to follow Armstrong's axioms.

            Duplicate FDs (FDs with the same left-hand and right-hand sides)
            will be ignored. Thus, for any two sets of attributes *X* and
            *Y*, there will be at most one FD of the form *X* → *Y*.

        :raises ValueError:
            If any FD contains attributes that are not in the schema.
        """

        # FDs with the same left-hand and right-hand sides are considered
        # duplicates as per the assumption in section 2.2 of
        # https://dl.acm.org/doi/pdf/10.1145/320493.320489. In practice,
        # this assumption has little impact on FDs, for which it is an
        # esoterism based on syntax versus semantics.

        self.attributes = tuple(set(attributes))
        """A tuple of the attributes in the schema."""

        self.attribute_map = {
            attribute: index for index, attribute in enumerate(self.attributes)
        }
        """A mapping of attributes to their indices in the attributes tuple."""

        self.keys = set[frozenset[int]]()
        """The set of candidate keys in the schema."""

        self.functional_deps = dict[frozenset[int], set[int]]()
        """The set of functional dependencies in the schema."""

        # Step 1: Check that keys are valid and express them as sets of indices.
        # O(n) time complexity for n attributes in the set of keys given.
        for key in keys:
            try:
                self.keys.add(
                    frozenset(self.attribute_map[attr] for attr in key)
                )
            except KeyError as e:
                raise ValueError(
                    f"Attribute {e.args[0]} of key {key} is not in the schema."
                )

        # O(n²) time complexity for n attributes in the set of keys given.
        # Step 2: Remove superkeys.
        for key in self.keys.copy():
            if any(existing_key < key for existing_key in self.keys):
                self.keys.remove(key)

        # O(n) time complexity for n attributes (across the domains and
        # codomains of all FDs).
        for lhs, rhs in functional_deps:
            try:
                lhs_set = frozenset(self.attribute_map[attr] for attr in lhs)
                rhs_set = set(self.attribute_map[attr] for attr in rhs)
            except KeyError as e:
                raise ValueError(
                    f"Functional dependency {lhs} → {rhs} has attribute "
                    f"{e.args[0]} that is not in the schema."
                )

            if lhs_set not in self.functional_deps:
                self.functional_deps[lhs_set] = rhs_set
            else:
                self.functional_deps[lhs_set] |= rhs_set

    def synthesised_schema(self) -> set[set[Hashable]]:
        """
        Synthesise a 3NF schema from the attributes, candidate keys, and
        functional dependencies in the builder. The synthesised schema is a set
        of sets of attributes representing the relations in the schema.
        """

        self.eliminate_extraneous_attributes()
        self.find_covering()
        self.partition()
        self.merge_equivalent_keys()
        self.eliminate_transitive_dependencies()
        self.construct_relations()
        return self.relations  # Or something like that.

    def eliminate_extraneous_attributes(self) -> None:
        r"""
        Eliminate extraneous attributes from the left side of each functional
        dependency in the schema. An attribute *A* ∈ *X* is extraneous in an FD
        *X* → *Y* if *X* \ {*A*} → *Y* is in the closure of the set of FDs.¹

        References
        ----------
        1. Philip A. Bernstein. “Synthesizing third normal form relations from
           functional dependencies”. In: _ACM Trans. Database Syst._ 1.4 (Dec.
           1976), pp. 277-298. ISSN: 0362-5915.
           doi: [10.1145/320493.320489](https://doi.org/10.1145/320493.320489).
        """

        # Trivial implementation:
        new_fds = dict[frozenset[int], set[int]]()
        for lhs, rhs in self.functional_deps.items():
            for rhs_attr in rhs:
                # Checking FD of the form lhs → {rhs_attr}.
                new_lhs = set(lhs)
                for lhs_attr in lhs:
                    if self.in_closure(
                        (new_lhs - {lhs_attr}, rhs_attr),
                        self.functional_deps,
                    ):
                        # lhs_attr is extraneous in lhs.
                        new_lhs.remove(lhs_attr)

                new_fds.setdefault(frozenset(new_lhs), set[int]()).add(rhs_attr)

        del new_fds[frozenset()]
        self.functional_deps = new_fds

    def find_covering(self) -> None:
        """
        Find a nonredundant cover of the functional dependencies in the schema.
        An FD *f* is redundant if it is in the closure of the remaining FDs.¹

        References
        ----------
        1. Philip A. Bernstein. “Synthesizing third normal form relations from
           functional dependencies”. In: _ACM Trans. Database Syst._ 1.4 (Dec.
           1976), pp. 277-298. ISSN: 0362-5915.
           doi: [10.1145/320493.320489](https://doi.org/10.1145/320493.320489).
        """

        new_fds = self.functional_deps.copy()
        for lhs, rhs in self.functional_deps.items():
            for rhs_attr in rhs:
                # Checking FD of the form lhs → {rhs_attr}.
                new_fds[lhs].remove(rhs_attr)
                if not new_fds[lhs]:
                    del new_fds[lhs]
                if self.in_closure((lhs, rhs_attr), new_fds):
                    # FD is redundant.
                    pass
                else:
                    # FD is not redundant.
                    new_fds.setdefault(lhs, set()).add(rhs_attr)

        self.functional_deps = new_fds

    def partition(self) -> None:
        """
        Condense FDs with the same left-hand side into a single FD. For any
        two FDs *X* → *Y* and *X* → *Z*, we can replace them with a single
        FD *X* → *Y* ∪ *Z*.
        """

        # The FDs are already
        # stored in a dictionary mapping LHS sets to sets of
        # RHS attributes. We just need to map them neatly to facilitate mergers.

        # i: Group number, lhs: LHS of the FD. Look up the RHS of the FD
        # using self.functional_deps[lhs].
        self.fd_groups = {
            i: [lhs] for i, (lhs, _) in enumerate(self.functional_deps.items())
        }

    def merge_equivalent_keys(self) -> None:
        """
        Merge FDs with equivalent LHSs. Two FDs *X* → *A* and *Y* → *B* are said
        to have equivalent LHSs if *X* → *Y* and *Y* → *X* are in the closure of
        the set of FDs, _i.e._, if the bijection *X* ↔ *Y* exists in the
        closure.
        """

        self.equiv_keys = dict[frozenset[int], set[int]]()
        new_groups = tuple({i} for i in range(len(self.fd_groups)))

        # fd_copies = tuple(self.functional_deps.copy().items())
        for i in range(len(self.fd_groups)):
            lhs1 = self.fd_groups[i][0]
            for j in range(i + 1, len(self.fd_groups)):
                lhs2 = self.fd_groups[j][0]

                if self.in_closure(
                    (lhs1, lhs2), self.functional_deps
                ) and self.in_closure((lhs2, lhs1), self.functional_deps):
                    # From the paper: Add X → Y and Y → X to J.
                    self.equiv_keys.setdefault(lhs1, set()).update(lhs2)
                    self.equiv_keys.setdefault(lhs2, set()).update(lhs1)

                    new_groups[j].add(i)
                    new_groups[i].add(j)

        for lhs, rhs in self.equiv_keys.items():
            # From the paper: For each A ∈ Y, if X → A is in H, delete
            # it. Likewise, for each B ∈ X, if Y → B is in H, delete it.
            self.functional_deps[lhs] -= rhs

        # Clean up.
        for lhs, rhs in self.functional_deps.items():
            if not rhs:
                del self.functional_deps[lhs]

        # Update the FD groups to reflect the mergers.
        visited = list(False for _ in range(len(self.fd_groups)))
        for i, group in enumerate(new_groups):
            if not visited[i]:
                for j in group:
                    visited[j] = True
                    self.fd_groups[i].extend(self.fd_groups[j])
                    if j != i:
                        del self.fd_groups[j]
        
    def eliminate_transitive_dependencies(self):
        """
        Eliminates transitive dependencies.
        Finds a minimal subset H' of the FD's such that (H' U J)+ = (H U J)+
        i.e. no proper subset of H' has this property
        
        dependency in the schema. An attribute *A* ∈ *X* is extraneous in an FD
        For each FD X->Y , check if the X->A is implied by the rest FD's, where A ∈ Y
        """
        new_fds = self.functional_deps.copy()
        for lhs, rhs in list(self.functional_deps.items()):
            for rhs_attr in list(rhs):
                # Temporarily remove 
                new_fds[lhs].remove(rhs_attr)
                if not new_fds[lhs]:
                    del new_fds[lhs]
                
                # check if the FD is implied by remaining FD's
                if self.in_closure((lhs, rhs_attr), new_fds):
                    # FD is transitive/redundant, so let it be removed
                    pass
                else:
                    new_fds.setdefault(lhs, set()).add(rhs_attr)
        self.functional_deps = new_fds
            

    @overload
    @staticmethod
    def in_closure(
        fd: tuple[Iterable[int], Iterable[int]],
        fds: dict[frozenset[int], set[int]],
    ) -> bool:
        """
        Check if the given functional dependency is in the closure of the
        functional dependencies in the schema.

        :param fd:
            A tuple of the form ``(lhs, rhs)``, where ``lhs`` and ``rhs`` are
            iterables of attribute indices representing the LHS and RHS of the
            FD, respectively.

        :return bool:
            ``True`` if the FD is in the closure of the functional dependencies
            in the schema, and ``False`` otherwise.
        """
        ...

    @overload
    @staticmethod
    def in_closure(
        fd: tuple[Iterable[int], int], fds: dict[frozenset[int], set[int]]
    ) -> bool:
        """
        Check if the given functional dependency is in the closure of the
        functional dependencies in the schema.

        :param fd:
            A tuple of the form ``(lhs, rhs)``, where ``lhs`` is an iterable of
            attribute indices representing the left-hand side of the FD, and
            ``rhs`` is an attribute index representing the right-hand side of
            the FD. Note that the RHS is a single attribute index, not a set of
            attribute indices.

        :return bool:
            ``True`` if the FD is in the closure of the functional dependencies
            in the schema, and ``False`` otherwise.
        """
        ...

    @staticmethod
    def in_closure(
        fd: tuple[Iterable[int], int] | tuple[Iterable[int], Iterable[int]],
        fds: dict[frozenset[int], set[int]],
    ) -> bool:
        solver = ClosureMembershipSolver(
            (lhs, frozenset(rhs)) for lhs, rhs in fds.items()
        )
        solver.lhs = fd[0]

        if isinstance(fd[1], int):
            solver.rhs = fd[1]
            return solver.is_member()
        else:
            return all(solver.is_member() for solver.rhs in fd[1])
