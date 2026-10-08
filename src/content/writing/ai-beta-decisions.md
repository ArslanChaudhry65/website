---
title: An AI beta should produce a decision
description: A useful beta connects permissions, quality and operating cost. A convincing demonstration leaves those questions open.
topic: AI product economics
relatedWork: learner-assistant
order: 2
reviewRequired: true
---

A prototype can show that an assistant answers a question. It cannot, on that evidence alone, show that the product is reliable, commercially viable or useful in a customer's actual environment.

That distinction shaped the Learner Assistant beta requirements I worked on at imc. There was already a demonstrable interaction. The missing piece was a way to understand its behaviour and cost under conditions that resembled the product a customer would use.

The beta needed a decision to inform.

## Start with the uncertainty

"Get feedback" is too broad to tell a team what to measure.

If the uncertainty is whether an answer is useful, the beta needs inspectable questions and responses, a way to capture feedback and an account of what counts as useful.

If the uncertainty is cost, the team needs a defined unit of usage and a way to attribute costs to it.

If the uncertainty is whether access boundaries hold, the beta needs the real permissions. Removing them from the test makes the environment easier to run while preserving the uncertainty.

The experiment should follow the decision.

## Permissions belong inside quality

An answer can be factually correct and still be an unacceptable product result. That happens when it draws on content the user cannot access.

For an enterprise assistant, permission fidelity belongs alongside relevance and correctness. It is not a separate approval step that can wait until the answer looks good.

The beta requirements therefore used customer content and production-equivalent permissions. This creates more setup work, but it makes the evidence relevant to the system being considered for release.

It also changes how results should be read. A failure to retrieve something might be an access boundary working correctly, not simply poor retrieval.

## A cost average needs a definition

A single average can conceal several different activities: internal experimentation, demonstrations, customer usage, retries and evaluation runs.

Before using it in a price discussion, I want to know what it represents. Which customer system? Which model? Which time period? Which traffic was excluded?

The requirements for the Learner Assistant separated those dimensions and excluded internal testing from the customer usage view. That was a measurement choice. It was not yet proof of a sustainable cost or a suitable price.

Cost visibility tells you something about what the product costs to operate. Willingness to pay tells you something different.

## Feedback must lead somewhere

A rating on each answer is useful when it helps the team inspect why an interaction succeeded or failed.

It is less useful as a decorative dashboard number. A question-response report can provide the context needed to decide whether the next change belongs in retrieval, content, the interaction or the product's scope.

Before a beta starts, I would want the team to name the decisions that different results could trigger. Otherwise it is easy to keep collecting feedback without changing the product.

## Include the cost of realism

An isolated customer system makes some boundaries easier to reason about. It also costs infrastructure, setup time and attention.

Real permissions can complicate evaluation. Customer content can expose gaps that a curated demo never encounters. Defined measurement windows and traffic filters take work to maintain.

These are costs of obtaining useful evidence. They should be visible in the beta plan, just as model usage should be visible in the product economics.

## The update worth publishing

For the current Learner Assistant work, the beta results and final commercial decision are still outside this account.

The useful follow-up will not be that the beta happened. It will be which assumption changed and what the team chose as a result.

That is the standard I would use for an AI beta: does it make the next consequential product decision easier to defend?
