---
title: Mass enrolment that survives a launch day
description: A large customer launch exposed two structural bottlenecks. I reframed the request as a standard product problem and coordinated three connected workstreams.
number: "01"
category: Enterprise scale
kind: Case study
role: Product Owner, imc Learning Suite
period: Oct 2025 to Jun 2026
status: Implementation completed; throughput unverified here
decision: Reframed a customer commitment into a standard-product epic, defined acceptance criteria and coordinated the work across product, platform and QA.
result: The work addressed transactional email and repeated per-user processing. A verified post-change throughput figure is not available in this account.
order: 1
diagram: enrolment
reviewRequired: true
---

## The product problem

An enterprise customer needed to enrol tens of thousands of learners across a group of courses for a large launch. The requested throughput was in the six-figure-per-hour range. These are deliberately rounded requirements, not achieved performance figures.

The existing process could not support that use case reliably. The difficulty was more than a slow screen. A launch involving a large population would turn repeated work and blocking dependencies into an operational problem.

The product question was whether to treat the request as a customer-specific exception or address the underlying behaviour in the standard product. That distinction affected scope, ownership and which other customers would benefit.

## Two bottlenecks in one request

The first problem was the transaction boundary. Email was sent synchronously during enrolment. The database transaction could remain open while waiting for the mail server. A dependency outside the database could therefore delay or jeopardise the operation inside it.

The second problem was repeated work. The mass operation called a single-user routine many times. Course-level work was repeated for each learner, and some checks became more expensive as the data grew. A large request multiplied the wrong unit of work.

This distinction mattered. Optimising an individual query would not remove the external dependency from the transaction. Making email asynchronous would not, by itself, turn a repeated single-user loop into a batch operation.

> The requirement needed to describe a different processing model, not only a faster version of the existing one.

## My role

I reframed the commitment as a standard-product epic, wrote the conditions of satisfaction and split the work into three connected streams. I coordinated the dependencies with the platform team and QA.

My contribution was the product framing, acceptance criteria, scope and coordination. The architecture and implementation were engineering work; I worked through their product consequences rather than presenting the technical design as my sole decision.

I also reviewed an AI-generated use case that carried one customer's performance figures into standard product documentation. I corrected the description and kept open questions explicit instead of turning customer-specific requirements into general claims.

## Three choices that mattered

### 1. Fix the standard product

A custom implementation could have limited the immediate commercial scope. It would also have left a synchronous mail dependency in a database transaction for other customers.

The standard-product approach made sense because the failure mode was not unique to the requesting customer. The trade-off was broader regression exposure. A change used by more customers needs a wider understanding of existing behaviour.

### 2. Separate enrolment from notification delivery

The implementation used events to separate the enrolment operation from mail processing. This reduced the coupling between a successful enrolment and the availability of an external mail server.

The price was a new operating model. Event delivery, consumer behaviour and notification failures now had to be considered explicitly. An event that is not handled cannot be treated as though the whole transaction simply rolled back.

### 3. Use a real batch path

The mass operation needed to stop repeating avoidable work for each learner. A configurable threshold separated the batch path from smaller operations.

That made the feature more than a performance patch. Acceptance criteria had to cover course capacity, permissions, partial failure and the behaviour of the ordinary enrolment path. The batch path had to remain a valid product operation, not just a faster benchmark.

## Execution and regression work

The work crossed the enrolment process, notification infrastructure and the checks needed to make a batch safe. Splitting it into workstreams made the dependencies visible, but did not remove them.

Mail behaviour was a particularly important regression surface. Fifteen notification paths needed to be checked again after decoupling. Customer-specific notifications, placeholders and custom code could rely on assumptions that the original synchronous path had made possible.

The practical consequence was that a technically sensible boundary change still required careful product coverage. Existing notification behaviour was part of the contract customers experienced, even where it had never been described as such.

## Outcome and business relevance

The implementation epic was completed in June 2026. The documented work addressed the synchronous mail path and the repeated single-user processing model.

I do not have a verified post-change throughput figure for this account. The target above must therefore not be read as an achieved result. This case supports a claim about the problem framing and the changes made; it does not support a numerical speed-up claim.

The business rationale was to make large customer launches viable through the standard product and reduce exposure to a shared reliability problem. A quantified reduction in support effort, risk or operating cost would need additional evidence.

## What the solution cost

The event infrastructure became a hard dependency in the initial approach and needed further work. Notifications that had previously worked within the synchronous path did not all survive the change automatically.

That is the part of the case I would not remove. Decoupling shifted the failure modes. The team had to account for delayed or missing delivery and the compatibility expectations built around the earlier implementation.

There was also an editorial cost: the most precise customer figures were unsuitable for a general public performance promise. Keeping those figures out of release language was part of managing the product commitment.

## What I would carry forward

Before accepting a throughput requirement, I want to understand the transaction boundary and the unit of work. Both determine whether the right response is tuning, batching, decoupling or a different scope.

I would also make the measurement plan part of the acceptance criteria early enough that the final result is easy to retrieve. A clear target and a completed implementation are not substitutes for a verified after-state.

*Customer names, exact customer volumes and internal performance-test measurements are omitted. This account distinguishes the requirement from the evidence available for publication.*
