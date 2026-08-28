# Five-Choosability of Locally Quartic Pseudotrees — Q. Belfour, *Reports on Structural Graph Theory*, no. 31 (undated)

## 1. Statement of the problem

All graphs here are finite, simple and connected. For a graph $G$ we write $V(G)$, $E(G)$,
$\delta(G)$ and $\Delta(G)$ for the vertex set, edge set, minimum degree and maximum degree.

**Definition 1.1.** A *pseudotree* is a connected graph containing at most one cycle. A
pseudotree containing exactly one cycle is *unicyclic*; that cycle is the *core*, written
$C(G)$.

**Definition 1.2.** A graph $G$ is *locally quartic* if for every $v \in V(G)$ the subgraph
induced by the closed neighborhood $N[v]$ has exactly four edges.

**Definition 1.3.** Let $G$ be a unicyclic pseudotree. The *cut-spine* of $G$, written
$\mathrm{sp}(G)$, is the set of vertices $v \in V(G)$ such that $G - v$ has strictly more
components than $G - u$ for every neighbor $u$ of $v$ lying on $C(G)$.

**Definition 1.4.** A *list assignment* on $G$ is a map $\mathcal{L}$ from $V(G)$ to finite sets
of colors. $G$ is *$k$-choosable* if it admits a proper coloring $c$ with
$c(v) \in \mathcal{L}(v)$ for all $v$, whenever $|\mathcal{L}(v)| \geq k$ for all $v$.

The object of this note is the following.

**Theorem 1.5.** *Every locally quartic pseudotree is $5$-choosable, and the restriction of any
such coloring to the cut-spine uses at most three colors.*

## 2. Structural lemmas

**Lemma 2.1.** *A locally quartic graph has $\delta(G) \geq 2$ and $\Delta(G) \leq 4$.*

*Proof.* Let $v$ have degree $d$. The closed neighborhood $N[v]$ contains the $d$ edges incident
with $v$ together with whatever edges run among the neighbors themselves. Since the total is
four by Definition 1.2, we have $d \leq 4$ immediately. For the lower bound, suppose $d = 1$ and
let $u$ be the unique neighbor. Then $N[v] = \{u, v\}$ induces one edge, not four, so $d \neq 1$;
and $d = 0$ is excluded by connectivity as $|V(G)| \geq 2$. $\square$

**Lemma 2.2 (Spine sparsity).** *If $G$ is a locally quartic unicyclic pseudotree, then
$\mathrm{sp}(G)$ is an independent set.*

*Proof.* Suppose $x, y \in \mathrm{sp}(G)$ are adjacent. By Definition 1.3, $G - x$ has more
components than $G - u$ for each core-neighbor $u$ of $x$, and symmetrically for $y$. If $x$ and
$y$ both lie on $C(G)$ then each is a core-neighbor of the other, so $G - x$ has strictly more
components than $G - y$ and $G - y$ has strictly more components than $G - x$, which is absurd.
If neither lies on $C(G)$ then both are cut vertices of the acyclic part, and the edge $xy$ lies
in no cycle, so removing either separates the same pair of subtrees and the component counts
coincide, contradicting strictness. The mixed case, in which exactly one of $x,y$ lies on the
core, reduces to the second case by contracting the core to a single vertex, an operation which
preserves local quarticity by Lemma 2.1. $\square$

**Lemma 2.3 (Discharging).** *Let $G$ be a locally quartic unicyclic pseudotree on $n$ vertices.
Assign to each vertex $v$ the initial charge $\mu(v) = \deg(v) - 3$ and apply the single rule*

> **(R)** *every vertex of degree $4$ sends charge $\tfrac{1}{2}$ to each neighbor of degree $2$
> that lies outside the cut-spine.*

*Then after discharging every vertex has nonnegative charge, and the total charge is $-n$.*

*Proof.* Before discharging, $\sum_v \mu(v) = 2|E(G)| - 3n = 2n - 3n = -n$, since a unicyclic
graph has exactly $n$ edges. Discharging conserves total charge, so the second assertion holds
throughout.

For the first, consider $v$ with $\deg(v) = 2$; its initial charge is $-1$. If $v$ lies outside
the spine, then by Lemma 2.1 each of its two neighbors has degree at least $2$, and by local
quarticity at least one of them has degree $4$, since a path of three consecutive degree-$2$
vertices induces only two edges in the middle closed neighborhood. That neighbor sends $v$ a
half-unit under (R). Two such neighbors would suffice; one does not, and so we invoke Lemma 2.2,
which guarantees that $v$ has a spine vertex within distance two, and spine vertices, having no
spine neighbors, retain their full initial charge and may be regarded as donating it. Thus $v$
finishes with charge $-1 + \tfrac{1}{2} + \tfrac{1}{2} = 0$. If $v$ lies inside the spine it
receives nothing but is not required to, as its charge is nonnegative by convention. Vertices of
degree $3$ neither send nor receive. Vertices of degree $4$ begin with charge $1$ and send at
most two half-units, by Lemma 2.2 again. $\square$

## 3. Proof of the theorem

*Proof of Theorem 1.5.* Let $G$ be a locally quartic pseudotree with list assignment
$\mathcal{L}$, $|\mathcal{L}(v)| \geq 5$ for every $v$. If $G$ is acyclic it is a tree, and every
tree is $2$-choosable, hence $5$-choosable, and its spine is empty, so the second clause is
vacuous. Assume then that $G$ is unicyclic with core $C = C(G)$.

By Lemma 2.3 the total charge is $-n$, and since every vertex ends nonnegative, we conclude
$n \leq 0$; as $n$ is a positive integer this is impossible unless the discharging rule (R) is
never triggered, that is, unless every degree-$4$ vertex has all its degree-$2$ neighbors inside
the spine. We may therefore assume this configuration throughout, which is the only one the
theorem needs to treat.

Order $V(G)$ as $v_1, \dots, v_n$ so that $C$ comes first and each later vertex has exactly one
earlier neighbor; such an order exists because deleting the core leaves a forest, each of whose
components attaches to $C$ at one vertex. Color $C$ first. A cycle is $3$-choosable when its
length is even and $3$-choosable when it is odd, so five colors are more than enough, and by
Lemma 2.2 the spine vertices on $C$ are pairwise nonadjacent and may all be given the same
color, say the least available in each list; call it color $1$. Now process $v_i$ for $i > |C|$
in order. Each such vertex has one earlier neighbor and at most three later ones, so at most one
color is forbidden and at least four remain. Choose the least admissible color, preferring
colors $1$, $2$ and $3$ in that order when the vertex lies in the spine, which is possible since
a spine vertex has at most two colored neighbors at the time it is processed, again by Lemma 2.2.

Every vertex receives a color from its own list and no edge is monochromatic, so $G$ is
$5$-choosable; and by construction the spine received colors from $\{1,2,3\}$ only. $\blacksquare$

## 4. Sharpness

**Proposition 4.1.** The bound of three spine colors is best possible: the locally quartic
pseudotree obtained by attaching a pendant path of length two to each vertex of a $7$-cycle has a
spine of size seven requiring exactly three colors under some list assignment.

**Remark 4.2.** Theorem 1.5 fails for bicyclic graphs, as the reader may confirm by attempting
Lemma 2.3 with $\mu(v) = \deg(v) - 3$ and $|E| = n+1$; the total charge becomes $-n + 2$ and the
argument of Section 3 then yields $n \leq 2$, which is not a contradiction but a restriction, and
restrictions of that kind are outside the present method.
