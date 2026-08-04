# Security and Privacy

## Data Handling

- The primary ZIP-analysis flow never requests Instagram credentials or connects to Instagram.
- The optional `instagrapi` laboratory connector accepts credentials only for the duration of one request. It is disabled by default, does not persist sessions or passwords, verifies the authenticated identity, applies strict result limits and must not be enabled on a public deployment.
- The offensive repository under `lab/Instagram-` is never imported or executed. Its endpoint performs source parsing and hashing without granting that code network access.
- ZIP contents are read directly and are never extracted to an application directory.
- Starlette may temporarily spool a large upload in the container's `/tmp`; Compose mounts this path as temporary memory and the upload is closed immediately after parsing.
- Validated relationship maps remain in process memory for one hour or until the user deletes the session.
- Restarting the backend removes every active session.

## Archive Validation

The parser rejects:

- absolute paths and parent-directory traversal;
- symbolic links and encrypted archives;
- more than 10,000 archive members;
- archives over 1 GiB;
- relationship JSON members over 100 MiB;
- more than 200 MiB of uncompressed relationship JSON data;
- suspicious compression ratios;
- malformed, non-UTF-8, HTML-only, or structurally incomplete exports;
- invalid Instagram usernames.

## Operational Limits

Unrelated media entries are never decompressed and therefore do not count toward the relationship-data limit. The in-memory store accepts at most 25 concurrent sessions. When full, the oldest session is removed. This is a safety bound, not multi-user authentication.

For public or shared deployment, add identity-aware access control at the reverse proxy and rate limiting before accepting uploads. The current application is intended for a trusted local machine or controlled private network.

Keep `ENABLE_INSTAGRAPI_LAB=false` in public or shared environments. If it is temporarily enabled for an authorized local evaluation, use a dedicated test account, HTTPS, network-level access restrictions and stop the connector immediately after the evaluation.

## Reporting a Vulnerability

Do not include a real Instagram export, username list, token, password, or other personal data in an issue. Report the minimal reproduction privately to the repository maintainer.
