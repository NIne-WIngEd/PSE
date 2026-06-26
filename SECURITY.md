# Security Policy

## Supported Versions

Security updates are applied to the latest version of the `main` branch and to the most recent published release.

| Version | Supported |
|---|---|
| Latest `main` branch | Yes |
| Most recent release | Yes |
| Older releases | Best effort only |
| Historical experimental snapshots | No |

## Reporting a Vulnerability

Please do **not** report security vulnerabilities through a public GitHub issue, discussion, pull request, or social-media post.

Use one of the following private reporting channels:

1. GitHub's **Private vulnerability reporting** feature for this repository, when available.
2. A private message to the repository maintainer through the contact method listed on the maintainer's GitHub profile.

Maintainer:

**Mostakim Khan Rayan**  
GitHub: [NIne-WIngEd](https://github.com/NIne-WIngEd)

A useful report should include:

- a concise description of the vulnerability;
- the affected file, endpoint, component, or commit;
- the environment in which it was observed;
- reproducible steps or a minimal proof of concept;
- the expected and actual behavior;
- the potential impact;
- any suggested mitigation;
- whether the report or reporter's identity should remain confidential.

Do not include restricted AFM images, credentials, access tokens, personal information, unpublished reviewer material, or proprietary data unless a secure transfer method has been agreed upon.

## Response Process

The maintainer will make a reasonable effort to:

- acknowledge a complete report within 7 calendar days;
- assess severity and reproducibility;
- request additional information when necessary;
- prepare and test a correction;
- coordinate disclosure with the reporter;
- publish a security advisory or release note when appropriate.

Response times may vary because this is an academic research-software project maintained on a limited-resource basis.

## Responsible Disclosure

Reporters are asked to:

- avoid accessing, modifying, or deleting data that they do not own;
- avoid disrupting public or private deployments;
- avoid publishing exploit details before a reasonable remediation period;
- minimize collection of sensitive information;
- provide enough time for validation and release of a fix.

Good-faith security research that follows this policy will not be treated as malicious project participation.

## Security Scope

Examples of in-scope concerns include:

- arbitrary file access or path traversal;
- unsafe file upload or output serving;
- remote code execution;
- command injection;
- cross-site scripting;
- cross-site request forgery;
- insecure deserialization;
- exposure of credentials or private files;
- dependency vulnerabilities with a practical impact on this project;
- model-file replacement or integrity bypass;
- unauthorized access to generated analysis results;
- denial-of-service behavior caused by malformed input;
- unsafe handling of uploaded images or archive files.

The following are generally out of scope unless they create a concrete security impact:

- scientific disagreements about model accuracy;
- expected model misclassification;
- unsupported operating systems or dependency combinations;
- vulnerabilities that require a user to deliberately replace trusted local model files;
- rate-limit findings without demonstrated impact;
- automated scanner output without reproduction steps;
- issues already fixed in the latest supported version.

## Sensitive Data

The public repository does not redistribute the original AFM dataset images. Users are responsible for ensuring that uploaded images and derived outputs can be processed and stored lawfully.

Do not use the public issue tracker to share:

- proprietary or embargoed AFM data;
- personally identifiable information;
- passwords, API keys, access tokens, or private URLs;
- confidential journal-review content;
- unpublished institutional data.

## Security Updates and Attribution

Confirmed reporters may be credited in a security advisory or release note unless they request anonymity.

Security fixes must preserve the project's AGPL-3.0-or-later licensing, authorship, attribution, and provenance requirements.
