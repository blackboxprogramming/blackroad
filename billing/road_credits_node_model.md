Road Credits / Node Contribution Model (design notes)

Purpose

Road Credits are a future mechanism to reward useful node contributions and reduce billing for verified, trustworthy nodes. They are NOT applied automatically in the initial billing system — this document explains required signals and verification flows for later automation.

Net Bill = Base + Atomic Usage - Verified Node Credits

Node credit requirements (minimum set):
- signed device identity: each node must produce a cryptographic identity (public key) and sign claims. CarKeys or an equivalent secure hardware-backed identity is recommended.
- uptime score: measure of availability (percent uptime over an observation window).
- useful work score: evidence of completed, verifiable work (e.g., blocks processed, requests served). Work must be auditable.
- quality/correctness score: sampling/validation of returned results for correctness.
- trust score: reputation aggregated from other nodes and operator attestations.
- privacy constraints: nodes must not send private user data to untrusted nodes; Road Credits must only be awarded for work that does not leak private data.

Operational notes
- IP addresses are NOT a valid identity; they are ephemeral and insufficient for credit.
- CarKeys or similar attestation can be used to prove hardware-backed identity and key provenance.
- RoadChain: record claim hashes for contributions (not raw data) to provide verifiable audit trails without storing private user data on-chain.

Verification and redemption
- A node submits signed claims describing the work performed plus proofs (hashes, merkle roots, attestations).
- The operator verifies claims (automatically or manually) against sampled evidence and assigns credits.
- Credits are tied to account identities and can reduce bills, increase quotas, or grant differentiated access.

Safety and anti-abuse
- Require cryptographic signatures and attestations to avoid forged claims.
- Apply slashing or credit revocation policies for proven misbehavior.
- Rate-limit credit creation and require periodic re-verification for large credits.

Future integration points
- Credits are modeled as integer units. When applying to billing, treat credits as a post-billing offset (applied to the invoice) after verification.
- Road Credits should be visible in the billing UI and ledger with provenance links to verification artifacts.

Privacy
- Never require nodes to share private user data to earn credits. Proofs must be non-sensitive (hashes, proofs of work, metrics).

This document is intentionally high-level. Implementations must define exact schemas for signed claims, scoring algorithms, and on-chain anchors (RoadChain claims) before credits are automatically applied to invoices.
