---
title: An AI beta built to inform a price
description: A working demo could show the assistant. The beta needed to show whether its permissions, quality and operating costs could support a real product.
number: "03"
category: AI product economics
kind: Decision note
role: Product Owner, learner-facing AI
period: Current product work
status: Beta specification; results pending
decision: Defined beta requirements for customer-specific systems, production permissions, cost attribution and answer feedback.
result: The measurement design is specified. Customer results, validated pricing and a launch outcome are not claimed.
order: 3
diagram: assistant
reviewRequired: true
---

## Where the prototype stopped

The Learner Assistant already had a prototype that could be demonstrated at events. It could show an interaction, but there was no dependable answer to what a customer response would cost.

That gap changes the job of a beta. Adding more demonstration features might make the product easier to present while leaving the commercial uncertainty untouched.

I treated the beta requirements as a way to produce evidence for the next product decision: quality under real access rules, cost under customer usage and a basis for discussing what could be sold.

## My contribution

I specified customer-specific systems, customer content and production-equivalent permissions as part of the beta scope.

I also specified cost measurement by model and customer system, filterable to the test period, with internal imc testing excluded. Answer ratings and a report pairing questions with responses were included so quality could be examined.

Purchase and configuration questions entered the backlog alongside the assistant behaviour. I do not claim sole ownership of a shared credit model or a final pricing decision.

## Three uncertainties to test

### Will it respect the customer's information boundaries?

A retrieval assistant can generate a plausible answer from information the user was never allowed to access. In an enterprise product, that is a product failure even if the answer is factually correct.

The beta therefore required the same permissions as production. Loosening them for convenience would leave the most consequential risk outside the experiment.

### What does real usage cost?

The cost requirements separated model and customer system and allowed a defined test period. Internal experimentation was excluded from the customer usage view.

The intention was a cost figure that could be interpreted. A blended average containing demos, retries, internal testing and customer activity would make it difficult to connect price to a recognisable unit of use.

### Is the answer useful enough?

A rating on each answer and a question-response report created a route to evidence. The feedback mechanism would not, by itself, prove quality, but it would make individual interactions inspectable.

The next step would be to connect those observations to explicit product decisions: improve retrieval, change scope, adjust the interaction or stop a particular use case.

## The system choice

Each beta customer would receive an isolated system with its own design and content database, populated through the data connector.

This supported a realistic customer context and a clear measurement boundary. It also added infrastructure and setup cost. Isolation was a choice with consequences, not a claim that a product is automatically safe.

Content scope remained important. The assistant's answer quality and cost would depend on what it could retrieve and how that content was made available.

## Why pricing belongs in the scope

A usage-based capability needs an account of the unit being purchased. A model request, a conversation and a successful learning interaction are not necessarily the same thing.

The beta requirements could help identify operating cost. They could not establish willingness to pay on their own. That needs customer evidence and a commercial decision.

The work therefore connected cost visibility with the purchase questions without pretending they were already resolved.

## Current status

This is a decision note about the beta specification. It is not a completed AI product success story.

The evidence in this account covers the requirements and measurement design. It does not include a validated cost per customer, a measured answer-quality improvement, willingness to pay or a final price.

The next useful update would report what the beta changed: which assumption held, which failed and what decision followed.

## What this approach costs

Customer-specific systems add operating work. Production-equivalent permissions make setup and evaluation harder. Cost attribution needs discipline about what traffic counts.

Those costs are accepted because the alternative would produce cleaner demonstrations with less reliable evidence for an enterprise release.

My working principle is simple: an AI beta should reduce the uncertainty that prevents the next decision. If it only produces positive reactions, it has not yet done enough.
