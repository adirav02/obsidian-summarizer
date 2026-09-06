# Retry Policies in Distributed Systems

A retry looks like a small local decision: a request failed, so the client tries again. In a distributed system, that decision changes traffic across the whole system. A good retry policy therefore balances recovery from brief faults against the risk of creating more load or repeating an operation that already succeeded.

## Decide whether a failure is retryable

The first question is not how long to wait. It is whether another attempt makes sense. The source recommends retrying transient failures, such as a short outage or an overloaded gateway, while bounding the total number of attempts. A permanent error should not be turned into repeated traffic.

> [!warning] A retry consumes capacity
> When many clients retry during an outage, the extra requests can amplify the overload that caused the failures. A retry limit prevents one operation from contributing unbounded work.

## Backoff changes the timing

**Exponential backoff** increases the delay after each failed attempt. The source gives this simple schedule:

$$
d_a = b \cdot 2^a
$$

Here, $d_a$ is the delay for attempt $a$, and $b$ is the base delay. If the base delay is one second, successive delays are 1, 2, 4, and 8 seconds. Waiting progressively longer gives a struggling service time to recover.

Backoff alone can still synchronize clients. If thousands of clients fail together and calculate the same delay, they wake together and produce another spike. **Jitter** adds randomness to spread those attempts across time.

## A payment example

Imagine that a payment request times out after reaching the server. The client cannot tell whether the server rejected the request or completed the charge before the response was lost. Retrying the same operation without protection could charge the customer twice.

An **idempotency key** lets repeated submissions represent the same logical operation. Combined with error classification, a retry limit, backoff, and jitter, it makes the retry safer without pretending that every failure is harmless.

## Common mistakes

- **Retrying every error** - Permanent failures should stop rather than create repeated traffic.

- **Allowing unlimited attempts** - A retry limit prevents one operation from contributing unbounded work.

- **Using identical backoff schedules** - Add jitter so clients do not synchronize and create another traffic spike.

- **Retrying side-effecting operations without protection** - Use idempotency mechanisms so a lost response does not turn a retry into a duplicate effect.

## Glossary

- **Transient failure** - A temporary condition for which a later attempt may succeed.
- **Exponential backoff** - A schedule that increases the delay after each failure.
- **Jitter** - Random variation added to retry timing to reduce synchronization.
- **Idempotency key** - An identifier that lets a server recognize repeated submissions of one logical operation.

> [!summary] One-sentence takeaway
> **Safe retries combine selective error handling, bounded attempts, exponential backoff, jitter, and idempotent operations so recovery does not create a second failure.**
