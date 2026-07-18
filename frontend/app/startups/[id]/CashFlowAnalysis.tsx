"use client";

import type { Analysis } from "@/types";

const money = (value: unknown) =>
  value === null || value === undefined ? "—" : `${new Intl.NumberFormat("vi-VN").format(Number(value))} VND`;

const number = (value: unknown) => (value === null || value === undefined ? "—" : Number(value).toFixed(1));

export default function CashFlowAnalysis({ analysis }: { analysis: Analysis }) {
  const details = (analysis.report.details ?? {}) as Record<string, any>;
  const metrics = details.metrics ?? {};
  const reconciliation = details.reconciliation ?? {};
  const scenarios = details.scenarios ?? {};
  const matching = details.matching_signals ?? {};
  const periods = details.periods ?? [];
  const cards = [
    ["Available cash", reconciliation.reported_ending_cash ?? reconciliation.expected_ending_cash, money],
    ["Operating burn/month", metrics.net_burn, money],
    ["Base runway", metrics.base_runway_months, number],
    ["Downside runway", scenarios.downside?.runway_months, number],
    ["Severe runway", scenarios.severe?.runway_months, number],
    ["Funding gap", scenarios.severe?.funding_gap, money],
  ];
  return <section className="cashFlowDashboard">
    <div className="cashFlowCards">{cards.map(([label, value, format]) => <div key={String(label)}><span>{label}</span><strong>{(format as any)(value)}{String(label).includes("runway") && value != null ? " months" : ""}</strong></div>)}</div>
    <div className="cashFlowPanel"><h4>Scenario outlook</h4><div className="scenarioRows">{["base", "downside", "severe"].map((name) => <div key={name}><strong>{name}</strong><span>Runway: {number(scenarios[name]?.runway_months)} months</span><span>Funding gap: {money(scenarios[name]?.funding_gap)}</span><span>Needed by: {scenarios[name]?.funding_needed_by ?? "—"}</span></div>)}</div></div>
    <div className="cashFlowPanel"><h4>Period cash flow</h4><div className="cashFlowTable"><div className="cashFlowHead">Period · Operating in · Operating out · Net operating · Financing · Net cash</div>{periods.map((item: any) => <div className="cashFlowRow" key={item.period}>{item.period} · {money(item.operating_inflow)} · {money(item.operating_outflow)} · {money(item.net_operating_cash_flow)} · {money(item.net_financing_cash_flow)} · {money(item.net_cash_flow)}</div>)}</div></div>
    <div className="cashFlowPanel"><h4>Reconciliation</h4><p>Opening: {money(reconciliation.opening_cash)} · Inflows: {money(reconciliation.total_inflows)} · Outflows: {money(reconciliation.total_outflows)}</p><p>Expected ending: {money(reconciliation.expected_ending_cash)} · Difference: {money(reconciliation.difference)} · <strong>{reconciliation.status ?? "—"}</strong></p></div>
    <div className="cashFlowPanel"><h4>Matching signals</h4><p>Capital urgency: <strong>{matching.capital_urgency ?? "—"}</strong></p><p>Recommended capital: {(matching.recommended_capital_types ?? []).join(", ") || "—"}</p><p>Partner types: {(matching.recommended_partner_types ?? []).join(", ") || "—"}</p></div>
  </section>;
}
