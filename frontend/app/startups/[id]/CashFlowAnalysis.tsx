"use client";

import { useState } from "react";
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
  const breakEven = details.break_even ?? {};
  const warnings = details.warnings ?? [];
  const hasBaseRunway = metrics.base_runway_months !== null && metrics.base_runway_months !== undefined;
  const hasLatestRunway = metrics.latest_runway_months !== null && metrics.latest_runway_months !== undefined;

  const [activeScenario, setActiveScenario] = useState<string>("base");

  if (analysis.status === "insufficient_data") {
    return (
      <section className="cashFlowDashboard">
        <div className="cashFlowAlert warning">
          <span>💡</span>
          <div>
            <strong>Chưa đủ dữ liệu để phân tích dòng tiền.</strong>
            {(analysis.report.missing_data ?? []).length > 0 && (
              <p>Cần bổ sung: {(analysis.report.missing_data ?? []).join(", ")}.</p>
            )}
            {(analysis.report.recommended_questions ?? []).length > 0 && (
              <p>{analysis.report.recommended_questions?.[0]}</p>
            )}
          </div>
        </div>
      </section>
    );
  }

  // Xử lý dữ liệu biểu đồ SVG cho kịch bản đang chọn
  const projection = scenarios[activeScenario]?.monthly_projection ?? [];
  let minCash = 0;
  let maxCash = Number(reconciliation.opening_cash ?? 0);
  projection.forEach((p: any) => {
    const ending = Number(p.ending_cash);
    if (ending < minCash) minCash = ending;
    if (ending > maxCash) maxCash = ending;
  });

  const cashDiff = maxCash - minCash || 1;
  const padding = { top: 12, bottom: 20, left: 80, right: 15 };
  const chartW = 600 - padding.left - padding.right;
  const chartH = 150 - padding.top - padding.bottom;

  const points: Array<{ x: number; y: number; month: string; cash: unknown }> = projection.map((p: any, index: number) => {
    const x = padding.left + (index / (projection.length - 1 || 1)) * chartW;
    const y = padding.top + chartH - ((Number(p.ending_cash) - minCash) / cashDiff) * chartH;
    return { x, y, month: p.month, cash: p.ending_cash };
  });

  const pathD = points.length > 0
    ? `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ')
    : '';

  const areaD = points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${padding.top + chartH} L ${points[0].x} ${padding.top + chartH} Z`
    : '';

  const getScenarioColor = (name: string) => {
    if (name === "severe") return "var(--red)";
    if (name === "downside") return "var(--amber)";
    return "var(--blue)";
  };

  const activeColor = getScenarioColor(activeScenario);
  const activeAssumptions = scenarios[activeScenario]?.assumptions;
  const percent = (value: unknown, prefix = "") => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? `${prefix}${(parsed * 100).toFixed(0)}%` : "—";
  };
  const reconciliationLabel: Record<string, string> = {
    matched: "ĐÃ KHỚP",
    warning: "LỆCH NHẸ",
    critical_mismatch: "SAI LỆCH CẦN RÀ SOÁT",
    not_available: "CHƯA ĐỦ DỮ LIỆU ĐỐI SOÁT",
  };

  return (
    <section className="cashFlowDashboard">
      {/* 1. Hệ thống Cảnh báo (Alerts) */}
      {reconciliation.status === "critical_mismatch" && (
        <div className="cashFlowAlert error">
          <span>⚠️</span>
          <div>
            <strong>Sai lệch đối soát tiền mặt:</strong> Số dư thực tế khai báo lệch <strong>{money(Math.abs(reconciliation.difference))}</strong> so với tính toán lý thuyết từ lịch sử thu chi. Vui lòng kiểm tra lại tính chính xác của sổ sách giao dịch.
          </div>
        </div>
      )}
      {warnings.map((warningText: string, idx: number) => (
        <div key={idx} className="cashFlowAlert warning">
          <span>💡</span>
          <div>
            <strong>Cảnh báo hệ thống:</strong> {warningText}
          </div>
        </div>
      ))}

      {/* 2. Thẻ KPI (KPI Command Center) */}
      <div className="kpiGridPremium">
        {/* KPI 1: Số dư tiền mặt */}
        <div className="kpiCardPremium">
          <div>
            <div className="kpiCardLabel">Tiền mặt hiện dụng</div>
            <div className="kpiCardValue">
              {money(reconciliation.reported_ending_cash ?? reconciliation.expected_ending_cash)}
            </div>
          </div>
          <div className="kpiCardSubtext">
            Trạng thái:{" "}
            {reconciliation.status === "matched" ? (
              <span className="badgeCF success">Đã khớp sổ</span>
            ) : reconciliation.status === "warning" ? (
              <span className="badgeCF warning">Lệch nhẹ</span>
            ) : reconciliation.status === "critical_mismatch" ? (
              <span className="badgeCF danger">Lệch đối soát</span>
            ) : (
              <span className="badgeCF neutral">Chưa đối soát</span>
            )}
          </div>
        </div>

        {/* KPI 2: Tốc độ tiêu tiền */}
        <div className="kpiCardPremium">
          <div>
            <div className="kpiCardLabel">Operating Burn / Tháng</div>
            <div className="kpiCardValue">{money(metrics.net_burn)}</div>
          </div>
          <div className="kpiCardSubtext">
            <span>Tiêu gộp: {money(metrics.gross_burn)}</span>
            {metrics.burn_trend === "improving" ? (
              <span className="badgeCF success">Cải thiện</span>
            ) : metrics.burn_trend === "deteriorating" ? (
              <span className="badgeCF danger">Xấu đi</span>
            ) : (
              <span className="badgeCF neutral">Ổn định</span>
            )}
          </div>
        </div>

        {/* KPI 3: Số tháng sống sót */}
        <div className="kpiCardPremium">
          <div>
            <div className="kpiCardLabel">Runway Cơ sở</div>
            <div className="kpiCardValue">
              {metrics.cash_generating ? (
                <span style={{ color: "var(--green-dark)" }}>Tự chủ dòng tiền</span>
              ) : metrics.cash_flow_state === "break_even" ? (
                <span style={{ color: "var(--green-dark)" }}>Hòa vốn dòng tiền</span>
              ) : hasBaseRunway ? (
                `${number(metrics.base_runway_months)} Tháng`
              ) : (
                "—"
              )}
            </div>
          </div>
          <div className="kpiCardSubtext">
            {metrics.cash_generating ? (
              <span className="badgeCF success">Tạo tiền dương</span>
            ) : metrics.cash_flow_state === "break_even" ? (
              <span className="badgeCF success">Không đốt tiền</span>
            ) : (
              <span>Kỳ gần nhất: {hasLatestRunway ? `${number(metrics.latest_runway_months)} thg` : "—"}</span>
            )}
          </div>
        </div>

        {/* KPI 4: Doanh thu hòa vốn */}
        <div className="kpiCardPremium">
          <div>
            <div className="kpiCardLabel">Hòa vốn đích (Tháng)</div>
            <div className="kpiCardValue">
              {breakEven.available ? money(breakEven.break_even_revenue) : "Chưa có định phí"}
            </div>
          </div>
          <div className="kpiCardSubtext">
            {breakEven.available ? (
              <span>Định phí: {money(breakEven.fixed_monthly_costs)}</span>
            ) : (
              <span>Cần thêm định phí và tỷ lệ biến phí</span>
            )}
          </div>
        </div>
      </div>

      {/* 3. Stress-Test Scenarios & Interactive Timeline Chart */}
      <div className="cashFlowPanel">
        <h4>
          <span>Dự báo kịch bản & Stress Test (Scenario outlook)</span>
          <span style={{ fontSize: "11px", fontWeight: "normal", color: "var(--muted)" }}>
            Chọn kịch bản bên dưới để xem đường đi dòng tiền
          </span>
        </h4>

        {/* Tabs chọn kịch bản */}
        <div className="scenarioTabs">
          {["base", "downside", "severe"].map((name) => {
            const label = name === "base" ? "Cơ sở (Base)" : name === "downside" ? "Suy thoái (Downside)" : "Nghiêm trọng (Severe)";
            return (
              <button
                key={name}
                className={`scenarioTab ${activeScenario === name ? "active" : ""}`}
                onClick={() => setActiveScenario(name)}
              >
                {label}
              </button>
            );
          })}
        </div>

        {/* Thông tin nhanh về kịch bản */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "20px", fontSize: "12px", marginBottom: "12px" }}>
          <div>
            Giả định Inflow:{" "}
            <strong>
              {percent(activeAssumptions?.operating_inflow_change)}
            </strong>
          </div>
          <div>
            Giả định Outflow:{" "}
            <strong>
              {percent(activeAssumptions?.operating_outflow_change, "+")}
            </strong>
          </div>
          <div>
            Tháng cạn tiền dự báo:{" "}
            <span style={{ color: activeColor, fontWeight: 700 }}>
              {scenarios[activeScenario]?.runway_months
                ? `Tháng ${scenarios[activeScenario]?.runway_months}`
                : "Không cạn tiền (>12 thg)"}
            </span>
          </div>
          <div>
            Thiếu hụt vốn (Funding Gap):{" "}
            <strong style={{ color: scenarios[activeScenario]?.funding_gap > 0 ? "var(--red)" : "inherit" }}>
              {money(scenarios[activeScenario]?.funding_gap)}
            </strong>
          </div>
        </div>

        {/* Biểu đồ SVG tự vẽ trực quan */}
        <div className="cashFlowChartContainer">
          <svg viewBox="0 0 600 150" width="100%" height="100%">
            <defs>
              <linearGradient id={`grad-${activeScenario}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={activeColor} stopOpacity="0.3" />
                <stop offset="100%" stopColor={activeColor} stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            <line x1={padding.left} y1={padding.top} x2={padding.left + chartW} y2={padding.top} className="chartGridLine" />
            <line x1={padding.left} y1={padding.top + chartH / 2} x2={padding.left + chartW} y2={padding.top + chartH / 2} className="chartGridLine" />
            <line x1={padding.left} y1={padding.top + chartH} x2={padding.left + chartW} y2={padding.top + chartH} className="chartGridLine" />

            {/* Y axis labels */}
            <text x={padding.left - 8} y={padding.top + 3} textAnchor="end" className="chartAxisText">
              {money(maxCash).replace(" VND", "")}
            </text>
            <text x={padding.left - 8} y={padding.top + chartH / 2 + 3} textAnchor="end" className="chartAxisText">
              {money((maxCash + minCash) / 2).replace(" VND", "")}
            </text>
            <text x={padding.left - 8} y={padding.top + chartH + 3} textAnchor="end" className="chartAxisText">
              {money(minCash).replace(" VND", "")}
            </text>

            {/* X and Y Axis lines */}
            <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + chartH} className="chartAxis" />
            <line x1={padding.left} y1={padding.top + chartH} x2={padding.left + chartW} y2={padding.top + chartH} className="chartAxis" />

            {/* Plotting area & path */}
            {points.length > 0 && (
              <>
                <path d={areaD} fill={`url(#grad-${activeScenario})`} className="chartArea" />
                <path d={pathD} stroke={activeColor} className="chartLine" />

                {/* Draw points & labels */}
                {points.map((pt, idx) => {
                  const isNegative = Number(pt.cash) < 0;
                  const showLabel = idx === 0 || idx === points.length - 1 || idx === scenarios[activeScenario]?.runway_months - 1;
                  return (
                    <g key={idx}>
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={isNegative ? 4 : 3}
                        fill={isNegative ? "var(--red)" : activeColor}
                        stroke="#fff"
                        strokeWidth="1.5"
                      />
                      {showLabel && (
                        <text
                          x={pt.x}
                          y={pt.y - 8}
                          textAnchor="middle"
                          fill={isNegative ? "var(--red)" : "var(--ink)"}
                          fontSize="8px"
                          fontWeight="700"
                        >
                          {money(pt.cash).replace(" VND", "")}
                        </text>
                      )}
                      {idx % 2 === 0 && (
                        <text
                          x={pt.x}
                          y={padding.top + chartH + 12}
                          textAnchor="middle"
                          className="chartAxisText"
                        >
                          {pt.month}
                        </text>
                      )}
                    </g>
                  );
                })}
              </>
            )}
          </svg>
        </div>

        {/* Bảng dự báo kịch bản chi tiết */}
        <div className="ledgerTableContainer">
          <table className="ledgerTable">
            <thead>
              <tr>
                <th>Tháng dự báo</th>
                <th className="numCell">Số dư đầu kỳ</th>
                <th className="numCell">Thu Hoạt động dự phóng</th>
                <th className="numCell">Chi Hoạt động dự phóng</th>
                <th className="numCell">Thay đổi ròng</th>
                <th className="numCell">Số dư cuối kỳ</th>
              </tr>
            </thead>
            <tbody>
              {projection.map((row: any) => {
                const isNegative = Number(row.ending_cash) < 0;
                return (
                  <tr key={row.month}>
                    <td><strong>{row.month}</strong></td>
                    <td className="numCell">{money(row.starting_cash)}</td>
                    <td className="numCell" style={{ color: "var(--green)" }}>+{money(row.operating_inflow)}</td>
                    <td className="numCell" style={{ color: "var(--red)" }}>-{money(row.operating_outflow)}</td>
                    <td className={`numCell ${Number(row.net_cash_flow) < 0 ? "negativeNum" : ""}`}>
                      {Number(row.net_cash_flow) >= 0 ? "+" : ""}{money(row.net_cash_flow)}
                    </td>
                    <td className={`numCell ${isNegative ? "negativeNum" : ""}`} style={{ fontWeight: 700 }}>
                      {money(row.ending_cash)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Bảng dòng tiền lịch sử chi tiết (Historical Period Cash Flow Table) */}
      <div className="cashFlowPanel">
        <h4>Lịch sử Dòng tiền theo kỳ (Historical cash flow)</h4>
        <div className="ledgerTableContainer">
          <table className="ledgerTable">
            <thead>
              <tr>
                <th>Kỳ báo cáo</th>
                <th className="numCell">Thu Hoạt động</th>
                <th className="numCell">Chi Hoạt động</th>
                <th className="numCell">Ròng Hoạt động</th>
                <th className="numCell">Ròng Đầu tư (CAPEX)</th>
                <th className="numCell">Ròng Tài chính</th>
                <th className="numCell">Thay đổi Ròng</th>
              </tr>
            </thead>
            <tbody>
              {periods.map((item: any) => {
                const isNetOpNeg = Number(item.net_operating_cash_flow) < 0;
                const isNetInvNeg = Number(item.net_investing_cash_flow) < 0;
                const isNetFinNeg = Number(item.net_financing_cash_flow) < 0;
                const isNetCashNeg = Number(item.net_cash_flow) < 0;
                return (
                  <tr key={item.period}>
                    <td><strong>{item.period}</strong></td>
                    <td className="numCell">{money(item.operating_inflow)}</td>
                    <td className="numCell">{money(item.operating_outflow)}</td>
                    <td className={`numCell ${isNetOpNeg ? "negativeNum" : ""}`}>
                      {money(item.net_operating_cash_flow)}
                    </td>
                    <td className={`numCell ${isNetInvNeg ? "negativeNum" : ""}`}>
                      {money(item.net_investing_cash_flow)}
                    </td>
                    <td className={`numCell ${isNetFinNeg ? "negativeNum" : ""}`}>
                      {money(item.net_financing_cash_flow)}
                    </td>
                    <td className={`numCell ${isNetCashNeg ? "negativeNum" : ""}`} style={{ fontWeight: 700 }}>
                      {money(item.net_cash_flow)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Đối soát số dư tiền mặt (Reconciliation) */}
      <div className="cashFlowPanel">
        <h4>Đối soát số dư tiền mặt (Reconciliation)</h4>
        <p style={{ marginBottom: "14px" }}>
          Hệ thống đối chiếu dòng tiền thu/chi lịch sử với số dư tiền mặt khai báo của Startup:
        </p>
        <div className="reconciliationLedger">
          {reconciliation.status === "not_available" ? (
            <p className="muted">Chưa có số dư đầu kỳ nên hệ thống chưa thể đối soát lịch sử thu chi với số dư cuối kỳ.</p>
          ) : (
          <div className="reconciliationFormula">
            <div>
              <span style={{ fontSize: "10px", display: "block", color: "var(--muted)" }}>Số dư đầu kỳ</span>
              <span className="reconciliationTerm">{money(reconciliation.opening_cash)}</span>
            </div>
            <span className="reconciliationOperator">+</span>
            <div>
              <span style={{ fontSize: "10px", display: "block", color: "var(--muted)" }}>Tổng Thu</span>
              <span className="reconciliationTerm" style={{ color: "var(--green)" }}>
                +{money(reconciliation.total_inflows)}
              </span>
            </div>
            <span className="reconciliationOperator">-</span>
            <div>
              <span style={{ fontSize: "10px", display: "block", color: "var(--muted)" }}>Tổng Chi</span>
              <span className="reconciliationTerm" style={{ color: "var(--red)" }}>
                -{money(reconciliation.total_outflows)}
              </span>
            </div>
            <span className="reconciliationOperator">=</span>
            <div>
              <span style={{ fontSize: "10px", display: "block", color: "var(--muted)" }}>Số dư lý thuyết</span>
              <span className="reconciliationTerm" style={{ borderStyle: "dashed" }}>
                {money(reconciliation.expected_ending_cash)}
              </span>
            </div>
            <span className="reconciliationOperator" style={{ fontSize: "12px", color: "var(--muted)", fontWeight: "normal" }}>vs</span>
            <div>
              <span style={{ fontSize: "10px", display: "block", color: "var(--muted)" }}>Số dư thực tế</span>
              <span className="reconciliationTerm" style={{ borderColor: reconciliation.status === "critical_mismatch" ? "var(--red)" : "var(--green)" }}>
                {money(reconciliation.reported_ending_cash)}
              </span>
            </div>
          </div>
          )}

          <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid var(--line)", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
            <div>
              Chênh lệch đối soát:{" "}
              <strong style={{ color: reconciliation.status === "critical_mismatch" ? "var(--red)" : "inherit" }}>
                {reconciliation.difference !== null ? money(reconciliation.difference) : "—"}
              </strong>
            </div>
            <div>
              Trạng thái: <strong>{reconciliationLabel[reconciliation.status] ?? "CHƯA ĐỦ DỮ LIỆU ĐỐI SOÁT"}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Tín hiệu Phù hợp Vốn (Matching Signals) */}
      <div className="cashFlowPanel">
        <h4>Đề xuất Gọi vốn & Tín hiệu Đối tác (Matching signals)</h4>
        <div className="matchingGrid">
          <div className="matchingItem">
            <span style={{ color: "var(--muted)" }}>Mức độ khẩn cấp gọi vốn</span>
            <strong style={{ color: matching.capital_urgency === "high" ? "var(--red)" : "inherit", fontSize: "14px" }}>
              {matching.capital_urgency?.toUpperCase() ?? "—"}
            </strong>
          </div>
          <div className="matchingItem">
            <span style={{ color: "var(--muted)" }}>Loại hình vốn khuyến nghị</span>
            <strong>{(matching.recommended_capital_types ?? []).join(", ") || "—"}</strong>
          </div>
          <div className="matchingItem">
            <span style={{ color: "var(--muted)" }}>Nhóm đối tác phù hợp</span>
            <strong>{(matching.recommended_partner_types ?? []).join(", ") || "—"}</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
