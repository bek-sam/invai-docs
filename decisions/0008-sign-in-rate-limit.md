# 0008: Sign-in rate limit is 20/min per IP

- Status: accepted (2026-09-24); supersedes the 10/min in security finding S-19
- Type: security

## Context
S-19 set sign-in to 10/min per IP. A shop office shares one IP, and the limit was too tight (v1-plan backlog #20).

## Decision
Sign-in is limited to 20/min per IP. Floor PIN lockout is unchanged.

## Consequences
The limiter is in memory, per process. At more than one API task it has to move to Valkey (see `research/11-platform-scale-playbook.md` §2.3).
