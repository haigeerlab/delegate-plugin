# Redaction of public evidence

[简体中文](2026-10-08-public-redaction.md) | English

This page distinguishes public derivatives from local execution evidence. Redaction does not rerun models or establish historical approval. `<PROJECT_ROOT>` replaces the personal workspace, `<LOCAL_TMP>` replaces local temporary directories, and `<NATIVE_SESSION>` replaces the native session directory. These placeholders are not executable paths.

The [derivative manifest](2026-10-08-public-redaction.json) records original and public SHA-256 hashes for 22 artifacts. Original files and complete native logs remain local and are excluded from the public branch. The eight original pre-adoption `.md.txt` archives remain byte-identical.

Checker hashes, success flags, and command outputs in earlier batch JSON describe the original local execution snapshots. Redacted `.py.txt` files are reading copies; their bytes cannot be verified with the original hashes. Earlier checkerArchiveHashMatched flags do not establish verification of public derivatives. The current per-item evidence index updates only VAL to the public report hash; its other 32 references are unchanged. All 119 dispositions and historical completion and approval fields remain unchanged.

The conclusions remain 106 currently supported, 13 superseded, and zero unverified criteria. Historical completion and human approval remain unknown for all 119. Previously recorded limits on full product coverage, permanent regression, and failure/redelegation authorization remain applicable.
