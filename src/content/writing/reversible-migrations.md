---
title: Reversibility is a product capability
description: A client-level switch changes who carries migration risk. It also creates a maintenance obligation that needs an exit criterion.
topic: Enterprise modernisation
relatedWork: editor-migration
order: 1
reviewRequired: true
---

A migration is often described through the technology being replaced. That is useful for planning engineering work. It does not explain what customers need to survive the change.

In the Page Editor work at imc, the difficult part was the relationship between the old and new worlds: links, permissions, configuration and clients who would not all move at the same time.

A client-level switch made that relationship explicit. It let the product carry part of the migration risk instead of turning it into a single customer deadline.

## A switch changes the commitment

The familiar question is when the new system will be ready. A reversible transition adds another: can a customer adopt it without being trapped by the decision?

That is a product question because readiness is different across customers. One client may have a straightforward configuration. Another may have custom behaviour, embedded links or an internal rollout process that makes a single cutover expensive.

Offering both paths makes adoption possible under more conditions. The team accepts the cost of maintaining those conditions.

## Coexistence is more than two screens

The old and new interfaces can both exist while the migration still fails for a user.

A saved link might land in the wrong place. A permission might apply to the page but not to the panel. Two administrators might edit the same configuration with no clear rule for whose change survives.

These are not peripheral implementation details. They determine whether the product remains coherent while its internals change.

This is why I would write a migration brief around the contracts people rely on:

- how they enter the product,
- what they are permitted to see,
- what their configuration means,
- how they change it,
- what happens if the new path does not fit yet.

The technology is one part of satisfying those contracts.

## The cost moves inside the product

A reversible migration does not remove risk. It redistributes it.

Customers gain room to move at a different pace. The team gains routing logic, more combinations to test and a longer period in which the two systems must be understood together.

That cost becomes especially visible when capabilities arrive in waves. Panels delivered at different times can acquire different configuration behaviours. Each individual release can be defensible while the overall editor becomes less consistent.

It is tempting to count completed waves as proof that the migration is succeeding. They prove that work has shipped. Adoption and a shrinking legacy burden need their own evidence.

## Reversibility needs an exit question

The decision to keep an old path alive should come with a way to reconsider it.

Useful evidence would include the remaining customer dependencies, actual usage of each path, unresolved blockers and the operating cost of coexistence. The purpose is to make the next decision less dependent on whoever argues most strongly for keeping or removing the old system.

An exit criterion is not necessarily a fixed date. It can be a condition: customers with a specific dependency have an acceptable replacement, or the remaining exceptions can be handled without preserving the whole old product.

The important part is to make the condition discussable.

## When I would choose a different approach

A switch is less attractive when the product is small, the old behaviour has few dependencies or the cost of maintaining two paths exceeds the customer's cost of a coordinated change.

Reversibility should earn its place. It is valuable when it changes the feasibility of adoption, not simply because it sounds safer.

In a mature enterprise product, that feasibility can matter more than the apparent neatness of the migration plan. I want to know who carries the risk, what the alternative costs and what evidence will eventually let the old path disappear.
