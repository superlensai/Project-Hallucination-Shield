# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in HalWall, please **do not** open a public GitHub issue.

Instead, report it privately:

1. Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) feature on this repository
2. Or email: security@halwall.dev

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Fix/release**: Depends on severity; critical issues are patched within 7 days

## Scope

The following are in scope:
- Authentication/authorization bypasses
- SQL injection or other injection attacks
- Rate limiting circumvention
- Data exposure through API responses
- Supply chain attacks via the package trust system itself

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x.x   | Yes (current development) |
