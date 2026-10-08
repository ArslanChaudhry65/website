---
title: Modernising an editor without a cutover day
description: I inherited a technical migration and helped reframe it around configurable pages, customer continuity and a reversible transition.
number: "02"
category: Platform modernisation
kind: Case study
role: Product Owner, imc Learning Suite
period: From 2024; migration waves through 2025
status: Released capabilities; migration outcome partly evidenced
decision: Reframed the goal, translated customer feedback into scope, and coordinated coexistence requirements and migration sequencing.
result: Six migration waves were completed. Legacy deep-link resolution was observed in a running demo system; customer adoption and business impact are not quantified here.
order: 2
diagram: migration
reviewRequired: true
---

## The inherited brief

The Page Editor sat inside a wider migration of the imc Learning Suite towards React. The initial scope had been written before I took over the team. I did not originate that programme.

A technology migration can sound complete when the new interface matches the old one. For customers, the relevant question is whether their pages, links, permissions and configuration continue to work while something underneath changes.

The opportunity was to turn the editor into a clearer product capability: administrators should be able to configure pages while the migration remained manageable for existing customers.

## The constraint: customers do not move together

A mature enterprise product carries different configurations, customised behaviour and dependencies across clients. A single cutover date would ask all of those contexts to be ready at the same time.

Coexistence offered a different path, but it was not free. The product would need to understand which editor was active, where old links should lead and how access rules applied across the transition.

The real decision was how much migration risk to absorb inside the product rather than pass to customers as a deadline.

## My role

I helped reframe the inherited scope around the administrator's capability, analysed customer feedback and carried the coexistence requirements into the product work.

I worked on the sequencing of the migration waves and the split between backend foundations and visible interface changes. My contribution was product framing, requirements and coordination with engineering. The technical implementation remained a team effort.

Where this case describes a design choice, it describes the product approach I worked on. It does not imply that I independently authored every architecture decision.

## The central choice: a switch per client

A client-level switch made adoption reversible. The product could expose the configuration before the new capability was fully released, with the control initially unavailable.

The alternative was a single replacement event. That would have simplified the end-state sooner, but concentrated customer readiness and compatibility risk into one moment.

A per-client transition preserved choice. It also committed the team to operating two paths and explaining their relationship for longer. The switch was therefore a product capability with an ongoing maintenance cost.

## What coexistence actually required

### Links had to keep their meaning

Existing dashboard links were part of how people reached the product. They could live in bookmarks, internal pages or other workflows.

The new route structure needed to resolve those entry points. A migration that preserves screen functionality but breaks access to it has moved a technical boundary at the customer's expense.

### Permissions had to apply at the right level

Pages and individual panels needed access rules. Treating a page as one undifferentiated object would miss the reality that not every user should see every component inside it.

Permissions were therefore part of the migration contract, not a finishing task after the new editor existed.

### Editing needed an ownership rule

An editing lock made concurrent changes explicit. Configurable products need a clear answer to what happens when two administrators try to change the same surface.

The lock was not the largest decision in the case, but it illustrates the wider point: the product behaviour around the editor matters as much as the editor's controls.

## Execution across migration waves

The work moved through six numbered waves, completed between September 2024 and December 2025. Sequencing allowed parts of the product to move while the broader programme continued.

A backend-first split supported the foundations before the corresponding visible controls were complete. It also meant that progress could not be judged only by what changed on the screen.

Customer variants and panel-level differences made the work uneven. Delivering panels at different times created configuration inconsistencies that remained product debt after a wave had shipped.

## What is evidenced

The six migration waves were completed. In September 2026, a read-only check of a demo system confirmed that an old dashboard URL resolved to the new dashboard route.

The same system showed old and new page types together in the manager. That supports the coexistence story. It does not, by itself, establish how many customers have migrated or how much operating cost has been removed.

I do not report a customer adoption percentage, a support reduction or a completed retirement of the legacy editor here. Those would require separate evidence.

The business rationale was customer continuity and a more configurable administration experience. The observed routing behaviour is a product result; the broader business outcome remains unquantified in this account.

## What the approach cost

Coexistence prolonged the period in which both paths needed attention. Configuration drift and customer-specific variants did not disappear because the frontend technology changed.

The programme also retained a backlog of improvements. A delivered wave was not the same as a completely consistent editing model.

The trade-off was deliberate but substantial: reduce the concentration of migration risk for customers by accepting more complexity and a longer transition inside the product.

## The lesson I would reuse

Reversibility deserves to be discussed as a product requirement. In enterprise migrations, it can be the mechanism that makes adoption possible.

It also needs an exit question. How will the team know that maintaining the old path costs more than the remaining customer benefit? Without that question, a safe transition can turn into permanent duplication.

*The diagram is a conceptual reconstruction. No customer screenshots, branding, course content or internal identifiers are reproduced.*
