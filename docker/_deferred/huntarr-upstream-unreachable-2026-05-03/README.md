# Deferred Huntarr Scaffold (D-17-49)

Date: 2026-05-03
Reason: upstream image `huntarr/huntarr` unreachable during deployment (no pullable tag from this host).

These files were staged for Vault sidecar integration but intentionally removed from active deployment when component 3 was consolidated to Cleanuparr-only (Seeker module covers missing-content hunting role).

Re-activation preconditions:
1. Verify a pullable, trusted Huntarr image/tag and digest.
2. Re-validate supply-chain provenance posture for the selected image.
3. Re-introduce service + sidecar in arr-stack compose only after operator gate.
