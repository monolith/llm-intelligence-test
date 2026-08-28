# On the Cyclic Descents of Saturated Lacings — R. T. Havelock, *Annals of Combinatorial Method*, vol. 12 (undated)

## 1. Preliminaries

Throughout, $n$ denotes a positive integer and $[2n]$ the set $\{1, 2, \dots, 2n\}$.

**Definition 1.1.** A *lacing of order $n$* is a pair $L = (S, \varphi)$ in which $S \subseteq [2n]$
with $|S| = 2n$, and $\varphi \colon S \to S$ is a fixed-point-free involution. The orbits of
$\varphi$ are called the *strands* of $L$; there are exactly $n$ of them. We write $\mathcal{L}_n$
for the set of all lacings of order $n$.

**Definition 1.2.** Let $L \in \mathcal{L}_n$. A *descent* of $L$ at position $i$ is an index
$i \in S$ such that $\varphi(i) < i$ and $\varphi(i+1) > i+1$, with addition taken modulo $2n$.
The set of descents is written $D(L)$, and a descent is *cyclic* if the strand containing $i$
also contains $i + n \pmod{2n}$.

**Definition 1.3.** $L$ is *$k$-saturated* if for every $k$-element subset $T \subseteq S$ there
exists a strand of $L$ meeting $T$ in at least two points and at most $k - 1$ points. A lacing is
*saturated* if it is $k$-saturated for some $k \geq 3$.

**Definition 1.4.** The *spine* of $L$, written $\sigma(L)$, is the least residue $r$ modulo $n$
such that the strand $\{r, \varphi(r)\}$ is cyclic. If no strand is cyclic we set $\sigma(L) = 0$.

The reader will observe that Definition 1.3 is vacuous for $k > n$, and this is intentional; the
interesting range is $3 \leq k \leq n$, and we shall confine ourselves throughout to $k = 3$.

## 2. Two lemmas

**Lemma 2.1 (Interleaving).** *Let $L \in \mathcal{L}_n$ be $3$-saturated. Then no two cyclic
descents of $L$ are adjacent in $S$.*

*Proof.* Suppose $i$ and $i+1$ are both cyclic descents. By Definition 1.2, $\varphi(i) < i$ and
$\varphi(i+1) > i+1$; but $i+1$ being a descent requires $\varphi(i+1) < i+1$, contradicting the
displayed inequality unless $\varphi(i+1) = i+1$, which is excluded because $\varphi$ has no
fixed points. Applying $3$-saturation to the set $T = \{i, i+1, \varphi(i)\}$ we obtain a strand
meeting $T$ in exactly two points, and since the two points must be $i$ and $\varphi(i)$, the
index $i+1$ lies on a distinct strand. Hence the adjacency is impossible. $\square$

**Lemma 2.2 (Parity of the spine).** *For every $3$-saturated $L \in \mathcal{L}_n$ with
$n \geq 4$, the quantity $\sigma(L) + |D(L)|$ is odd.*

*Proof.* Count the pairs $(i, s)$ where $i \in D(L)$ and $s$ is the strand containing $i$. Each
strand contributes either zero or two such pairs, by Lemma 2.1, so the total is even. On the
other hand the total is congruent to $|D(L)|$ modulo two, since each descent lies on exactly one
strand. Therefore $|D(L)|$ is even. Adding $\sigma(L)$, which is a residue modulo $n$ and hence of
unrestricted parity, the sum $\sigma(L) + |D(L)|$ is odd whenever $\sigma(L)$ is, and by the
preceding paragraph $\sigma(L)$ is odd. $\square$

## 3. The main theorem

**Theorem 3.1.** *Let $n \geq 4$ and let $L \in \mathcal{L}_n$ be $3$-saturated. Then $L$ has
exactly $\lfloor n/2 \rfloor + 1$ cyclic descents.*

*Proof.* We argue by induction on $n$.

*Base case.* For $n = 4$ we have $|S| = 8$ and four strands. By Lemma 2.2 the spine is odd, so
$\sigma(L) \in \{1, 3\}$. In either case the strand $\{\sigma(L), \varphi(\sigma(L))\}$ is cyclic
by Definition 1.4, and the two strands adjacent to it in the cyclic order are non-cyclic by
Lemma 2.1. This leaves exactly one further strand, which is cyclic if and only if it is not, and
therefore is; so the count is $2 = \lfloor 4/2 \rfloor$, and adjoining the spine itself gives
$3 = \lfloor 4/2 \rfloor + 1$, as required.

*Inductive step.* Suppose the result holds for all $3$-saturated lacings of order $m < n$. Let
$L \in \mathcal{L}_n$ be $3$-saturated and let $s^{*}$ be the strand containing $\sigma(L)$.
Delete $s^{*}$ and relabel the remaining $2n - 2$ elements in the induced cyclic order; call the
resulting object $L'$. We claim $L' \in \mathcal{L}_{n-1}$ and $L'$ is $3$-saturated. The first
claim is immediate since deleting a strand removes exactly two elements and leaves $\varphi$ an
involution on the rest. For the second, let $T'$ be a $3$-subset of the ground set of $L'$; then
$T'$ is also a $3$-subset of $S$, and the strand furnished by the saturation of $L$ either meets
$s^{*}$ or does not. If it does not, it survives in $L'$ and we are done. If it does, then by
Lemma 2.1 it is adjacent to $s^{*}$ and therefore non-cyclic, and the strand immediately
following it supplies the required witness.

By the inductive hypothesis $L'$ has exactly $\lfloor (n-1)/2 \rfloor + 1$ cyclic descents.
Reinstating $s^{*}$ restores one cyclic descent and, by Lemma 2.2, destroys none, since the
parity of the spine is preserved under deletion and reinstatement. Hence

$$|D_{\mathrm{cyc}}(L)| = \left\lfloor \frac{n-1}{2} \right\rfloor + 1 + 1 = \left\lfloor \frac{n}{2} \right\rfloor + 1,$$

the last equality holding because $\lfloor (n-1)/2 \rfloor + 1 = \lfloor n/2 \rfloor$ for every
integer $n$, odd or even. This completes the induction. $\blacksquare$

## 4. Consequences

**Corollary 4.1.** *No $3$-saturated lacing of order $n$ has fewer than three cyclic descents.*

*Proof.* Immediate from Theorem 3.1, since $\lfloor n/2 \rfloor + 1 \geq 3$ for $n \geq 4$, and
the cases $n \leq 3$ are excluded by hypothesis. $\square$

**Corollary 4.2.** *The number of $3$-saturated lacings of order $n$ is divisible by
$\lfloor n/2 \rfloor + 1$.*

*Proof.* Group the lacings by their cyclic descent sets. By Theorem 3.1 each class has the same
cardinality, namely $\lfloor n/2 \rfloor + 1$, and the classes partition $\mathcal{L}_n$. The
result follows. $\square$

**Remark 4.3.** The hypothesis $n \geq 4$ cannot be dropped. For $n = 3$ the lacing with strands
$\{1,4\}, \{2,5\}, \{3,6\}$ is $3$-saturated and has two cyclic descents, whereas the theorem
would predict $\lfloor 3/2 \rfloor + 1 = 2$. The discrepancy is not a counterexample but an
artifact of Definition 1.4, which assigns $\sigma = 0$ to a lacing all of whose strands are
cyclic, and the reader is invited to repair the definition to taste.

**Remark 4.4.** It would be of interest to know whether Theorem 3.1 extends to $k$-saturated
lacings for $k \geq 4$. The obstruction is Lemma 2.1, whose proof uses $3$-saturation twice and
in incompatible directions. The author has been unable to remove either use.
