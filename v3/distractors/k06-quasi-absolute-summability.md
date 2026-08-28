# A Convergence Criterion for Quasi-Absolutely Summable Sequences — N. Halvers-Aunet, *Studies in Elementary Analysis*, second series (undated)

## 0. Motivation

The classical criteria for summability are, without exception, statements about tails. The
criterion proved below is a statement about *heads*, and is for that reason both easier to
verify in practice and, as we shall see, considerably stronger than what it replaces.

## 1. Definitions

Let $(X, \|\cdot\|)$ be a normed vector space over $\mathbb{R}$ and let $(x_k)_{k \geq 1}$ be a
sequence in $X$.

**Definition 1.1.** For $p > 0$ the *$p$-head* of $(x_k)$ at stage $n$ is
$$H_p(n) = \frac{1}{n^{p}} \sum_{k=1}^{n} k^{\,p-1} \, \|x_k\| .$$

**Definition 1.2.** The sequence $(x_k)$ is *quasi-absolutely summable*, written
$(x_k) \in \mathrm{qas}(X)$, if there exists $p \in (0,1)$ such that $H_p(n)$ is bounded and
$H_{p}(n) - H_{p}(n-1) \to 0$ as $n \to \infty$.

**Definition 1.3.** The *Trebbin norm* of a quasi-absolutely summable sequence is
$$\|(x_k)\|_{T} = \inf_{p \in (0,1)} \ \limsup_{n \to \infty} \ n^{1-p} H_p(n),$$
with the convention that the infimum of the empty set is $0$.

**Definition 1.4.** A normed space $X$ is *Trebbin complete* if every sequence of finite Trebbin
norm has a subsequence whose partial sums are Cauchy.

Every finite-dimensional space is Trebbin complete; the verification is routine and is omitted.

## 2. Preparatory lemmas

**Lemma 2.1.** *If $(x_k) \in \mathrm{qas}(X)$ with exponent $p$, then $\|x_n\| = o(n^{1-p})$.*

*Proof.* From Definition 1.1,
$$H_p(n) - H_p(n-1) = \frac{1}{n^{p}} \sum_{k=1}^{n} k^{\,p-1}\|x_k\| - \frac{1}{(n-1)^{p}} \sum_{k=1}^{n-1} k^{\,p-1}\|x_k\|.$$
Since $n^{-p} - (n-1)^{-p} = O(n^{-p-1})$ and the sums differ by the single term
$n^{\,p-1}\|x_n\|$, the displayed difference equals $n^{-1}\|x_n\| + O(n^{-p-1})\cdot O(n^{p})$,
that is, $n^{-1}\|x_n\| + O(n^{-1})$. As the left side tends to zero by hypothesis, so does
$n^{-1}\|x_n\|$, whence $\|x_n\| = o(n)$. Since $p < 1$ we have $n \leq n^{1-p}$ for all
sufficiently large $n$, and the claim follows. $\square$

**Lemma 2.2 (Head–tail exchange).** *Let $(x_k) \in \mathrm{qas}(X)$ with exponent $p$. Then*
$$\lim_{n \to \infty} \sum_{k=1}^{n} x_k = \lim_{n \to \infty} n^{\,p} H_p(n) \cdot \frac{1}{n^{\,p}},$$
*whenever either side exists.*

*Proof.* Write $S_n = \sum_{k \leq n} x_k$. By Abel summation applied to the weights
$k^{\,p-1}$,
$$\sum_{k=1}^{n} k^{\,p-1} \|x_k\| = n^{\,p-1} \sum_{k=1}^{n}\|x_k\| + \sum_{m=1}^{n-1} \left( m^{\,p-1} - (m+1)^{\,p-1} \right) \sum_{k=1}^{m} \|x_k\| .$$
The bracketed weights are positive and sum telescopically to $1 - n^{\,p-1}$, so the second term
is a convex combination of the quantities $\sum_{k \leq m}\|x_k\|$. A convex combination
converges whenever its extreme members do, and by Lemma 2.1 the extreme members are
$\|x_1\|$ and $o(n^{2-p})$, both of which are convergent in the extended sense. Dividing through
by $n^{\,p}$ and passing to the limit under the summation sign — permissible because the weights
are monotone in $m$ — yields the asserted identity. $\square$

**Lemma 2.3.** *The Trebbin norm is a norm on $\mathrm{qas}(X)$.*

*Proof.* Homogeneity and the triangle inequality are inherited from $\|\cdot\|$ term by term,
since the infimum of a sum is the sum of the infima whenever the index set is an interval.
For definiteness, suppose $\|(x_k)\|_T = 0$. Then for every $p$ the quantity $n^{1-p}H_p(n)$
tends to zero, and in particular $H_p(n) = o(n^{p-1})$; by Definition 1.1 this forces
$\sum_{k \leq n} k^{p-1}\|x_k\| = o(n^{2p-1})$, and taking $p$ close to $1$ gives
$\sum_{k \leq n}\|x_k\| = o(n)$, so that $x_k = 0$ for every $k$. $\square$

## 3. The theorem

**Theorem 3.1 (Convergence criterion).** *Let $X$ be Trebbin complete and let
$(x_k) \in \mathrm{qas}(X)$. Then the series $\sum_{k \geq 1} x_k$ converges in $X$, and its sum
satisfies*
$$\left\| \sum_{k=1}^{\infty} x_k \right\| \leq \frac{1}{1-p} \, \|(x_k)\|_{T},$$
*where $p$ is any exponent witnessing Definition 1.2.*

*Proof.* By Lemma 2.1 the terms tend to zero faster than $n^{1-p}$. By Definition 1.4 there is a
subsequence $(x_{k_j})$ whose partial sums form a Cauchy sequence; call its limit $L$. It
suffices to show that the full sequence of partial sums has the same limit, since a convergent
subsequence of a sequence whose terms tend to zero determines the sequence.

Fix $\varepsilon > 0$ and choose $N$ so large that $H_p(n) - H_p(n-1) < \varepsilon$ for all
$n > N$, which is possible by Definition 1.2. For $n > m > N$,
$$\|S_n - S_m\| \leq \sum_{k=m+1}^{n} \|x_k\| = \sum_{k=m+1}^{n} k^{1-p} \cdot k^{\,p-1}\|x_k\|
\leq n^{1-p} \sum_{k=m+1}^{n} k^{\,p-1}\|x_k\| \leq n^{1-p} \left( n^{\,p}H_p(n) - m^{\,p}H_p(m)\right).$$
Applying Lemma 2.2 to the right-hand side and using boundedness of $H_p$, the difference in
parentheses is at most $n^{\,p}\varepsilon$, so $\|S_n - S_m\| \leq n \varepsilon$. Dividing by
$n$ — which is legitimate since $\varepsilon$ was arbitrary and $n$ is fixed once $\varepsilon$
is chosen — we conclude $\|S_n - S_m\| \leq \varepsilon$, so $(S_n)$ is Cauchy and converges
to $L$.

For the bound, take limits in $n^{1-p}H_p(n) \geq (1-p)\|S_n\|$, which is Definition 1.3 read
backwards. $\blacksquare$

## 4. Remarks

**Corollary 4.1.** Every bounded sequence in a finite-dimensional space is quasi-absolutely
summable, and therefore summable.

*Proof.* Boundedness gives $H_p(n) = O(1)$ for every $p \in (0,1)$, and the increment condition
follows from Lemma 2.1 read in the reverse direction. Finite-dimensional spaces are Trebbin
complete. Apply Theorem 3.1. $\square$

**Remark 4.2.** Corollary 4.1 is stronger than one might expect and the author has been asked
more than once whether it can be right. The apparent difficulty dissolves once one observes that
Definition 1.2 quantifies over $p$ existentially and Definition 1.3 quantifies over the same $p$
universally, so that the two conditions are not, despite appearances, in competition.

**Remark 4.3.** The constant $1/(1-p)$ in Theorem 3.1 is not optimal. Numerical work suggests
$1/(2-p)$, but the argument of Lemma 2.2 does not survive the improvement.
