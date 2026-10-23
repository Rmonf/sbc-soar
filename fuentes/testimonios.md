# People In and Around an Agrivoltaic Facility

**Expectations, Interaction, Acceptance Criteria and Design Constraints**

> Markdown transcription of `testimonios.pdf`, with no changes to the content. The portrait photographs are omitted. The roadmap (§1.2) maps these testimonies to requirements.

## Contents

- **Part I. Field and Agronomy**
  1. The Farmer
  2. The Agronomist
  3. The UPC Agronomy Researcher
- **Part II. Energy and Operations**
  4. The Energy Engineer
  5. The Plant Operator
  6. The Supervisor
- **Part III. Business and Market**
  7. The Agricultural Business Owner
  8. The Electricity Distribution Business Executive
- **Part IV. Legal and Accountability**
  9. The Lawyer

---

# Part I. Field and Agronomy

## 1. The Farmer

> *"I need it to help, not to give me another job"*

**Martí Soler, 56.** Runs a 42-hectare family farm with seasonal workers. He knows the plots through long observation and keeps essential notes on paper and WhatsApp. He uses digital tools when they solve an immediate problem, but has little patience for configuration.

- **Goals:** protect crop quality, control water costs, keep machinery access and reduce unpleasant surprises.
- **Frustrations:** false alarms, weak mobile coverage, consultants who disappear after installation, and systems that require duplicate data entry.
- **Technology attitude:** pragmatic and selectively sceptical. He trusts a tool after seeing it survive unusual weather and ordinary field work.
- **Representative phrase:** "Show me what it does on a difficult Tuesday, not what it promises in a presentation."

Look, I do not really care whether you call it AI, optimisation, or a digital twin. I care whether the crop comes through the summer in good condition and whether I can still get the tractor where it needs to go. If the panels can give us shade when it is useful and electricity the rest of the time, that sounds sensible. But I have heard many promises about systems that save time and then you spend half the morning entering data or calling support.

What I would like is quite simple, although perhaps it is not simple to build. I want to look at something and understand what the installation is doing today. If the system wants to move the panels, I want a short reason: heat, wind, irrigation, expected sun, or a fault. I do not want a page of numbers. At the same time, if I think the recommendation is wrong, I want to see enough detail to argue with it. That is a contradiction, I know: keep it simple, but tell me everything when I ask.

I would probably use it on my phone, unless my hands are dirty, the screen is impossible to see in sunlight, or there is no signal. In that case I want a physical control or at least something in the farm office. Do not assume I will carry a tablet around. A warning should be obvious, but not every change deserves an alarm. If it sends too many messages, I will mute it. If it sends too few, I will say it cannot be trusted.

I would judge success by the crop, water use and the amount of trouble the system causes. I would like the yield to stay the same or improve, but one season proves very little. A dry year and a wet year are not comparable. I also care about quality, not only kilograms. If the panels protect the plants in a heatwave, that may matter more than average annual figures. Still, if energy revenue pays for improvements to the farm, I will not complain.

My restrictions are practical. Panel positions must leave room for machinery and workers. Movements must not happen while someone is underneath without a clear warning. The system must work when connectivity fails. It must not require a technician for every sensor problem. I want manual control, but I do not want people changing settings without leaving a record. I want it to learn from what we do, but I do not want it experimenting with the crop.

I would accept it gradually. First, let it observe and advise. Then, perhaps, let it move panels automatically in obvious cases such as strong wind. Later we can discuss irrigation or crop protection. The people building it will probably want a clear list of requirements. I cannot give them one now. Show me what it does in a real week, especially when something goes wrong, and then I will tell you what is missing.

## 2. The Agronomist

> *"The plant response cannot be reduced to one threshold"*

**Laia Ferrer, 39.** Independent agronomist advising several farms and cooperatives. She moves between field visits, laboratory results and meetings with people who expect direct recommendations. She is comfortable with models but remains wary of indicators detached from crop physiology.

- **Goals:** prevent avoidable stress, preserve quality, and make agronomic assumptions traceable.
- **Frustrations:** universal thresholds, missing calibration records, short pilots presented as biological proof, and dashboards that hide spatial variability.
- **Technology attitude:** engaged but demanding. She accepts automation when evidence, limits and exceptions remain visible.
- **Representative phrase:** "A number can be precise and still be agronomically wrong."

My first concern is that the project pitch makes the biological side sound cleaner than it is. It speaks about biological thresholds as if there were a single temperature or radiation value that tells us what the crop needs. In practice, response depends on cultivar, phenological stage, soil, water status, previous stress, vapour pressure deficit and the duration of exposure. A threshold can be useful operationally, but it must not be mistaken for biological truth.

I expect the system to represent uncertainty and time. A hot afternoon after adequate irrigation is different from a multi-day heat episode with depleted soil moisture. Instantaneous sensor values are not enough. I would want accumulated indicators, trends and a record of recent actions. If a model predicts crop stress, I need to know the horizon, calibration data and conditions under which the prediction becomes unreliable.

For interaction, I would like an agronomic view rather than the same dashboard shown to everyone. I want plots of canopy temperature, radiation distribution, soil-water indicators and the relationship between panel position and microclimate. I also want to annotate episodes: flowering, disease symptoms, irrigation problems, pruning, harvest operations. However, I do not want the system to depend on constant manual annotation. It should remain useful when the record is incomplete, while making the uncertainty visible.

I would accept the system if it protects the crop without generating hidden agronomic costs. Yield is necessary but insufficient. We should examine quality, water productivity, stress episodes, spatial variability and possibly disease pressure. The relevant outcome may appear weeks after the decision. I therefore resist claims based only on immediate energy gain or a short pilot. At the same time, I understand that the project cannot wait several years before producing anything useful.

My design constraints include calibrated sensors, documented units, traceable transformations and a clear separation between measured and estimated variables. Recommendations must indicate the evidence and the agronomic assumption behind them. If the model was trained on another crop or region, the interface must say so. Missing data must not be silently imputed and presented as observations.

I am not necessarily against automatic control. For reversible, bounded adjustments it may be appropriate. But the system should distinguish a recommendation supported by strong local evidence from one based on a general model. I also want the ability to set hard protective constraints, although I know fixed constraints can become outdated. Someone must review them, and that responsibility cannot be left vague.

Success, for me, means that the system becomes a credible agronomic instrument, not merely an energy optimiser with a crop variable added to the objective function. Yet I do not want a research platform so complicated that farm staff cannot operate it. The difficult part is preserving biological meaning while supporting decisions in time.

## 3. The UPC Agronomy Researcher

> *"If we cannot learn from it, we are wasting a rare experimental setting"*

**Dr Pau Vidal, 47.** UPC researcher specialising in crop microclimate and experimental methods. He coordinates field studies, supervises doctoral work and collaborates with farms. He values reproducibility and publication, but knows that operational partners cannot subordinate a season to a perfect experiment.

- **Goals:** produce reusable evidence, preserve provenance and separate correlation from causal claims.
- **Frustrations:** undocumented controller changes, inaccessible raw data, experiments without controls, and commercial claims stronger than the evidence.
- **Technology attitude:** highly capable and curious, sometimes tempted to collect more data than operations can maintain.
- **Representative phrase:** "A negative result is useful if we know exactly how it was produced."

I see the installation both as an operational system and as a field experiment. That creates an immediate tension. Operations need stable behaviour; research needs variation, comparison and carefully designed interventions. I would like the platform to help answer questions about microclimate, crop response and the interaction between energy and agricultural production, but I cannot ask a working farm to behave like a laboratory all the time.

The system should preserve raw data, metadata and provenance. I need sensor models, calibration history, sampling frequency, missingness, firmware changes and the exact version of every model or policy. If the panel controller changes in the middle of a season, the dataset may become difficult to interpret. On the other hand, freezing the system for methodological purity would prevent useful improvement.

I would interact through a research workspace or API rather than only a dashboard. I want access to time series, experimental labels and reproducible exports. I also want the ability to define a study area, compare sectors and register hypotheses before looking at results. That said, I would not expect operators or farmers to use this interface. The system needs several views, but those views must still refer to the same underlying events.

My success criteria differ from purely operational criteria. A negative result can be valuable if the experiment is well designed. I care about effect sizes, uncertainty, confounding variables and external validity. I would like randomised or alternating control policies when feasible, although operations may refuse them. A model that predicts accurately but cannot support causal interpretation may still be useful operationally, yet insufficient for a scientific claim.

Design restrictions include research ethics, agreements about data ownership, publication rights and protection of commercially sensitive information. Data should follow FAIR principles where possible, but "open" cannot mean releasing everything. Location, production or operational records may reveal more than expected. Consent and governance need to be revisited when the research question changes.

I would consider the project successful if it produces both a useful decision system and a trustworthy body of evidence. I would also like transferability across crops and sites, while knowing that local calibration is essential. I may ask the team to collect more variables than the operational product needs. They should challenge me: each additional sensor has a cost, a maintenance burden and another way to create misleading data.

---

# Part II. Energy and Operations

## 4. The Energy Engineer

> *"Optimisation is useful only inside a technically valid operating envelope"*

**Marta Rius, 35.** Energy engineer responsible for photovoltaic performance and control integration. She works comfortably with forecasts, inverters, constraints and telemetry, but has limited direct experience of crop decisions.

- **Goals:** predictable production, bounded control, low mechanical wear and a clear safety architecture.
- **Frustrations:** vague priorities, commands without acknowledgement, black-box recommendations and agronomic exceptions introduced after commissioning.
- **Technology attitude:** confident and automation-friendly, provided that interfaces and operating envelopes are formalised.
- **Representative phrase:** "If the optimiser cannot explain the active constraints, it is not ready to command equipment."

The pitch talks about an optimal panel angle in real time. That is plausible as a high-level goal, but I would first ask what the actuator can actually do, how quickly it moves, how much energy movement consumes, how often it may cycle, and which mechanical loads are acceptable. A mathematically attractive trajectory can be a poor control policy if it increases fatigue, causes oscillation or ignores inverter and grid constraints.

I expect forecasts of irradiance, temperature, wind and production, but I do not want a black-box forecast passed directly into actuation. The system should expose confidence intervals or at least operational confidence classes. It should support model predictive control or another method that handles constraints and future conditions, while retaining deterministic local protection. Strong wind, communication failure or a limit-switch disagreement should trigger a known safe behaviour without waiting for an LLM or cloud optimiser.

My preferred interface is technical. I want a single-line view of the energy system, panel positions, actuator status, inverter power, curtailment, alarms and forecast deviation. I need trends and event logs. I also want to see why the optimiser selected a set-point, but not a long natural-language story every time. A compact decomposition of the objective and active constraints would be more useful. For unusual events, a generated explanation may help if it links directly to measurements and control rules.

I would measure success through energy yield, availability, forecast error, avoided curtailment, actuator cycles, parasitic consumption and constraint violations. However, this is agrivoltaics, so maximum energy is not the only objective. I accept reduced production when there is a documented crop benefit or safety reason. What I cannot accept is an undefined "agronomic preference" silently overriding grid or mechanical constraints.

The design must separate advisory logic, supervisory control and safety protection. Every command needs a timestamp, origin, version and acknowledgement. Manual commands require priority rules and timeout behaviour. Remote control needs authentication and cybersecurity. Offline operation must be defined. If two agents disagree, the system must not negotiate indefinitely while the physical plant waits.

I would initially accept shadow mode: calculate recommendations without executing them and compare with existing operation. Then supervised execution, then bounded autonomy. But I might accelerate this schedule if the commercial deadline is tight, which is precisely why the safety case must not depend on my optimism. Success means higher useful production and predictable behaviour, including predictable failure.

## 5. The Plant Operator

> *"At three in the morning, I need to know what to do next"*

**Jordi Pons, 46.** Shift operator with experience in photovoltaic plants and industrial alarms. He is calm during incidents and sceptical of interfaces designed by people who have never worked a night shift.

- **Goals:** understand incidents quickly, distinguish urgency, and restore a safe operating state.
- **Frustrations:** alarm floods, stale data without warning, inconsistent controls, and updates that silently change behaviour.
- **Technology attitude:** accepts automation that reduces cognitive load, rejects automation that makes accountability opaque.
- **Representative phrase:** "Do not send me twenty alarms for one failed sensor."

I am the person who will receive the alarm when everyone else is asleep. I do not need the system to impress me. I need it to tell me what happened, whether anyone or anything is in danger, what it has already done, and what I should do next. If the first screen makes me search through five menus, it has failed.

I expect a clear overview: normal, degraded, stopped or unsafe. I want alarms grouped into incidents, not twenty notifications caused by one broken sensor. The system should distinguish an urgent action from something that can wait until morning. But I also do not want it hiding detail because it has decided that an alarm is not important. Give me filtering and escalation, with sensible defaults.

I would interact mainly through the control-room interface and sometimes by phone. I want to acknowledge an alarm, add a note, call up the relevant procedure and contact the right person. If I override a recommendation, the system should ask for a reason, but it should not make me write an essay during an emergency. Later, during review, we can complete the record.

For me, success means fewer surprises, shorter incidents and less time spent deciding whether data are real. Availability matters, but so does graceful degradation. If a soil sensor fails, perhaps the plant can continue cautiously. If wind measurements disagree, perhaps it should move to a safe position. I need those rules agreed in advance. I do not want the AI improvising an emergency procedure.

The restrictions are operational. Controls must be consistent. Colours and alarm sounds must have stable meanings. Time must be synchronised. The interface must identify stale data. Manual and automatic modes must be unmistakable. Commands must be confirmed by the equipment, not merely sent. Maintenance bypasses must be visible and expire automatically.

I like the idea that the system learns from incidents, but I am suspicious of behaviour changing without notice. If an update changes alarm thresholds or recommended actions, we need release notes, training and a rollback plan. I want automation because there is too much to monitor, yet I also want control because I am accountable when something happens. You will have to design for both.

## 6. The Supervisor

> *"I need the whole operation to remain governable"*

**Núria Casals, 51.** Operations supervisor coordinating shifts, maintenance, specialists and management reporting. She understands technical operations but spends much of her time resolving gaps between formal procedures and actual work.

- **Goals:** stable coordination, visible ownership, manageable workload and evidence for operational decisions.
- **Frustrations:** shadow spreadsheets, repeated overrides, unclear escalation and performance summaries without fair baselines.
- **Technology attitude:** wants high-level visibility with reliable access to underlying evidence.
- **Representative phrase:** "A green indicator is useful only if I can find out what it is hiding."

My role is to balance daily performance, staff workload, safety, contractual commitments and management expectations. I do not need every sensor value, but I need confidence that the detailed work is under control. The dashboard in the pitch is attractive, although dashboards often show what is easy to count rather than what is important.

I expect a daily operational picture: production, crop-protection actions, incidents, unresolved maintenance, unusual overrides and forecast risks. I also want weekly and seasonal trends. If the system says performance improved, I need to know the baseline and whether the comparison is fair. A sunny week is not proof that the optimiser works.

Interaction should support delegation. Operators can acknowledge and respond; specialists can change domain parameters within defined limits; I can approve exceptional modes and review repeated overrides. Yet I do not want every decision escalated to me. The system should make authority visible and route decisions appropriately. It should also reveal when no one clearly owns a decision.

I would call the system successful if it improves coordination and reduces avoidable incidents without increasing hidden work. Staff should not maintain spreadsheets outside the system because the official interface is unusable. I would look at response times, repeated alarms, overrides, downtime, safety events, energy and crop outcomes, and complaints from the team. Some of these indicators conflict. Fewer alarms may mean better filtering or poorer detection.

My constraints are governance and change control. Roles and permissions must be explicit. Important parameter changes need approval and audit. We need a fallback plan, supplier support and clarity about liability. I want rapid improvements, but not weekly changes that operators cannot follow. I want local autonomy, but consistent procedures across shifts.

I will probably ask for a traffic-light summary and then criticise it for oversimplifying. That is unavoidable. The system should let me move from a summary to the evidence. I do not need perfect certainty, but I do need uncertainty presented in a way that supports a decision rather than becoming an excuse.

---

# Part III. Business and Market

## 7. The Agricultural Business Owner

> *"I need a business case that survives a bad year"*

**Miquel Serra, 59.** Owner-manager of a medium-sized agricultural business. He negotiates with cooperatives, banks, insurers, suppliers and seasonal labour. He is interested in innovation but has seen pilots that never became maintainable operations.

- **Goals:** resilient margins, reduced climate exposure, predictable costs and freedom to change suppliers.
- **Frustrations:** unclear deliverables, hidden subscriptions, vendor lock-in and technical success without business value.
- **Technology attitude:** willing to invest after staged evidence, but expects one accountable party.
- **Representative phrase:** "Tell me what I own at the end of the thirteen weeks."

I like the idea of producing food and electricity on the same land, and I like the idea of using data rather than intuition alone. But the project pitch gives me a thirteen-week plan and a precise budget, while the biological and operational uncertainties remain large. I need to know what I am buying at the end: a prototype, a service, a control system, or a research result.

My first expectation is economic resilience. Extra electricity is useful, water savings are useful, and crop protection during heat may be extremely valuable. But revenue arrives through different channels and at different times. The system must not optimise a technical metric while worsening cash flow, insurance conditions or labour costs. I would like scenarios rather than one promised return: good year, bad year, equipment failure, low energy price and poor harvest.

I do not expect to operate the system every day. I want a concise monthly view and a notification when a decision affects budget, risk or contractual commitments. The people on site should handle routine operation. Still, I want the ability to see why money is being spent and why production departed from plan. If the system recommends new sensors or maintenance, it should show the expected consequence of postponing it.

I would accept the system if it demonstrates value on a limited area before requiring full investment. The pilot should measure energy, crop outcomes, water, labour and maintenance. Yet I know a small pilot may not represent the whole farm. I want rapid evidence and long-term confidence at the same time.

My restrictions include predictable operating cost, supplier continuity, ownership of data and the ability to change providers. I do not want the farm locked into one cloud platform or a model that only the original developer can maintain. At the same time, I prefer one accountable supplier rather than coordinating five technical companies.

Success means the installation supports the agricultural business rather than turning it into an energy experiment. It should improve margins, reduce exposure to extreme weather and remain understandable to the team. A beautiful dashboard is not success. Nor is a publication. But a project that produces no immediate profit may still be valuable if it reduces a serious future risk. I expect the team to help me distinguish those cases without pretending the forecast is certain.

## 8. The Electricity Distribution Business Executive

> *"Useful flexibility matters more than maximum generation"*

**Elena Costa, 44.** Executive responsible for distributed energy services and commercial partnerships. She works between grid constraints, market commitments, regulatory expectations and business development.

- **Goals:** forecastable output, reliable flexibility, standard integration and clear settlement rules.
- **Frustrations:** bespoke dashboards, unexplained deviations, ambitious flexibility claims and unclear imbalance responsibility.
- **Technology attitude:** strongly favours scalable automation, but wants commercial agency tightly bounded.
- **Representative phrase:** "A limitation declared in advance is more valuable than flexibility that disappears during an event."

From my perspective, the facility is not only a generator. It is a controllable resource connected to a network with limits, congestion and market conditions. Maximum instantaneous output is not always the most valuable behaviour. Predictability, controllability and compliance can be worth more than a few additional kilowatt-hours.

I expect production forecasts, ramp-rate control, clear availability and the ability to respond to grid or market signals where contracts permit. If the panels move for crop reasons, I need the effect on production to be visible in advance whenever possible. I am not asking agriculture to disappear, but I cannot manage unexplained deviations presented after the event.

Interaction should occur mainly through standard interfaces and scheduled data exchange, not through a bespoke dashboard that someone has to watch. I want telemetry, forecasts, set-point capabilities, event notifications and audit records. For commercial staff, a summary of delivered flexibility and settlement impact is useful. For technical integration, we need machine-readable APIs and agreed semantics.

I would judge success by forecast accuracy, response to requested limits, availability, data quality, cybersecurity and contractual performance. However, I also value the ability to declare temporary unavailability honestly. A system that promises flexibility and then fails during a heat event is worse than one that states its crop-protection constraints in advance.

Design restrictions include grid-code compliance, secure communications, time synchronisation, authenticated commands and separation between commercial signals and safety control. An external signal must not override local mechanical or human safety. We also need clarity about who bears imbalance costs when an agronomic decision changes output.

I favour automation because manual coordination does not scale. Yet I do not want an autonomous agent renegotiating obligations without limits. Commercial rules, technical capabilities and agronomic constraints must be translated into a bounded service. I may describe the facility as flexible, while the farmer describes the same flexibility as unacceptable uncertainty. The system has to expose that tension rather than conceal it in an optimiser.

---

# Part IV. Legal and Accountability

## 9. The Lawyer

> *"Before asking whether it is intelligent, tell me what it actually does"*

**Marc Bellver, 42.** Lawyer advising technology, energy and agricultural clients. He regularly enters projects after technical decisions have already created contractual or regulatory consequences. He prefers concrete system descriptions to fashionable labels.

- **Goals:** make authority, evidence, data use, supplier duties and incident responsibility governable.
- **Frustrations:** legal review at the end, fictional human oversight, uncontrolled service changes and claims stronger than validation.
- **Technology attitude:** neither hostile nor enthusiastic; he tests whether the operating model remains defensible when something fails.
- **Representative phrase:** "An override button does not prove meaningful human control."

The first thing I would say is that the label "AI system" tells me very little. I need to know the intended purpose, the decisions it supports, whether it controls physical equipment, which people may be affected, which data it processes and how responsibilities are allocated. The pitch mentions a possible high-risk classification under the AI Act, but classification cannot be resolved from a project title. We need the actual use case and the relevant legal frameworks.

I expect the project team to maintain documentation while designing, not write a legal chapter at the end. For every major function, I want to know the input, output, human role, foreseeable misuse, failure consequence and evidence supporting the claimed performance. If the system only recommends a panel angle, that is different from directly commanding machinery. But calling something a recommendation does not remove responsibility if people are expected to follow it automatically.

I would interact through reviews at defined gates: initial purpose and data map, prototype architecture, pilot conditions, contracts and deployment readiness. I do not need access to every model parameter, but I need someone to explain the system in ordinary language and someone else to provide the technical record. If the explanations contradict each other, that is useful information.

Data raise several questions. Weather data, sensor data and crop measurements may appear non-personal, but operational logs can identify workers, routines or commercial performance. Drone or camera data may capture people or neighbouring property. We need purpose limitation, access controls, retention periods and agreements about ownership and reuse. Publicly accessible data are not automatically free to reuse.

I would consider the system acceptable if responsibilities are clear, safety obligations are integrated, claims are proportionate to evidence, and people can exercise the rights or authority relevant to them. We need incident procedures, change control, audit trails and supplier obligations. If a model or cloud service changes, the original assessment may no longer be valid.

My design constraints may sound conservative: minimise data, avoid unnecessary automation, preserve human override, log significant decisions, secure remote access and define safe fallback. Yet excessive logging can itself create privacy and security risk. Human oversight can also be fictitious if the person lacks time, information or authority. A button labelled "override" is not proof of meaningful control.

Success is not simply the absence of litigation. It is a system that can be operated, challenged and investigated fairly when events do not go as planned. I also understand that asking for complete certainty would stop the project. The legal task is to make uncertainty governable, not to pretend it can be eliminated.

**Questions I would keep open**

- Which actions are advisory, supervisory or automatic in each operating mode?
- Who has authority to change agronomic, energy and safety parameters?
- Which party is responsible when sensor error, model error and human approval combine?
- What data may be reused for research, product improvement or other farms?
- Which claims will be made to customers, workers, insurers and authorities?
- How will software, models and contractual obligations be versioned together?
