# Retry Policies in Distributed Systems

A network request can fail even when both services are healthy. Short outages, overloaded gateways, and packet loss make immediate retries useful, but retries can also amplify load. A client should retry only transient failures and should stop after a bounded number of attempts.

Exponential backoff increases the delay after every failed attempt. A simple delay is `base * 2^attempt`. If many clients retry on the same schedule, they synchronize and create another traffic spike. Jitter adds randomness to spread their requests over time.

Idempotency matters because a timed-out request may have succeeded on the server. Retrying a payment without an idempotency key could charge a customer twice. A safe retry design combines error classification, a retry limit, exponential backoff, jitter, and idempotent operations.
