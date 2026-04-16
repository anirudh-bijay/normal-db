from collections.abc import Iterable, Hashable


class SchemaBuilder:
    def __init__(
        self,
        attributes: Iterable[Hashable] = set(),
        keys: Iterable[Iterable[Hashable]] = set(),
        functional_deps: Iterable[
            tuple[Iterable[Hashable], Iterable[Hashable]]
        ] = set(),
    ):
        """
        Initialises the schema builder with the given attributes and
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

        self.attributes = set(attributes)
        self.keys: set[frozenset[Hashable]] = set()
        self.functional_deps: set[
            tuple[frozenset[Hashable], frozenset[Hashable]]
        ] = set()

        # O(n²) time complexity for n keys.
        for key in sorted(
            (frozenset(key) for key in keys), key=lambda k: len(k)
        ):
            if not key <= self.attributes:
                raise ValueError(
                    f"Key {key} has attributes that are not in the schema."
                )

            # Remove superkeys.
            if not any(existing_key < key for existing_key in self.keys):
                self.keys.add(key)

        # O(n) time complexity for n fields (across the domains and codomains of
        # all FDs).
        for lhs, rhs in functional_deps:
            lhs_set = frozenset(lhs)
            rhs_set = frozenset(rhs)
            if not (lhs_set <= self.attributes and rhs_set <= self.attributes):
                raise ValueError(
                    f"Functional dependency {lhs} -> {rhs} has attributes that "
                    f"are not in the schema."
                )

            self.functional_deps.add((lhs_set, rhs_set))
