"use client";

import { useMemo, useState } from "react";

import { api } from "@/lib/api";
import type {
  Analysis,
  CashFlowAutofillProposal,
  CashFlowIngestionDetails,
  DocumentItem,
  Startup,
} from "@/types";

const FIELD_LABELS: Record<string, string> = {
  cash_flow_dataset: "Dữ liệu dòng tiền đã chuẩn hóa",
  current_cash: "Tiền mặt hiện có",
  minimum_cash_buffer: "Mức đệm tiền mặt tối thiểu",
  fixed_monthly_costs: "Chi phí cố định hàng tháng",
  variable_cost_ratio: "Tỷ lệ chi phí biến đổi",
  accounts_receivable: "Khoản phải thu",
  accounts_payable: "Khoản phải trả",
  inventory: "Giá trị tồn kho",
  working_capital_period_revenue: "Doanh thu kỳ vốn lưu động",
  working_capital_period_cogs: "Giá vốn kỳ vốn lưu động",
  working_capital_period_days: "Số ngày trong kỳ vốn lưu động",
  cash_flow_period_start: "Ngày bắt đầu kỳ dòng tiền",
  cash_flow_period_end: "Ngày kết thúc kỳ dòng tiền",
  cash_as_of: "Ngày chốt số dư tiền",
  currency: "Đơn vị tiền tệ",
  opening_cash: "Số dư đầu kỳ",
  reported_ending_cash: "Số dư cuối kỳ báo cáo",
  sales_support_metrics: "Chỉ số hỗ trợ bán hàng",
  purchase_cost_metrics: "Chỉ số chi phí mua hàng",
  monthly_rent: "Tiền thuê hàng tháng",
  lease_deposit: "Tiền đặt cọc thuê mặt bằng",
  employee_count: "Số nhân viên",
};

const CASH_FLOW_FIELDS = new Set(Object.keys(FIELD_LABELS));

function formatValue(value: unknown): string {
  if (typeof value === "number") return new Intl.NumberFormat("vi-VN").format(value);
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return `${value.length} bản ghi`;
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const periods = Array.isArray(record.periods) ? record.periods.length : null;
    const transactions = Array.isArray(record.transactions) ? record.transactions.length : null;
    if (transactions !== null) return `${transactions} giao dịch`;
    if (periods !== null) return `${periods} kỳ`;
    return `${Object.keys(record).length} chỉ số`;
  }
  return String(value);
}

type Props = {
  startup: Startup;
  documents: DocumentItem[];
  analysis?: Analysis;
  onAnalysisComplete: (analysis: Analysis) => void;
  onStartupUpdated: (startup: Startup) => void;
};

export default function CashFlowDataWorkspace({
  startup,
  documents,
  analysis,
  onAnalysisComplete,
  onStartupUpdated,
}: Props) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState<"analyze" | "apply" | null>(null);
  const [progress, setProgress] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const ingestion = analysis?.report.details?.ingestion as CashFlowIngestionDetails | undefined;
  const proposals = useMemo(
    () => (ingestion?.autofill_proposals ?? []).filter((item) => CASH_FLOW_FIELDS.has(item.field)),
    [ingestion],
  );
  const selectableProposals = proposals.filter((item) => item.status !== "conflict");
  const xlsxDocuments = documents.filter((item) => item.filename.toLowerCase().endsWith(".xlsx"));

  async function analyzeSavedFiles() {
    if (!xlsxDocuments.length) {
      setError("Chưa có file Excel. Hãy tải file tại tab Bằng chứng trước khi phân tích.");
      return;
    }
    setBusy("analyze");
    setError("");
    setMessage("");
    try {
      setProgress("AI đang nhận diện bảng và gọi tool tính toán...");
      const result = await api.runAnalysis(startup.id, "cash_flow", {
        use_gemini: true,
        use_cash_flow_ingestion_agent: true,
        use_cash_flow_mapping_ai: true,
      });
      onAnalysisComplete(result);
      const nextIngestion = result.report.details?.ingestion as CashFlowIngestionDetails | undefined;
      const defaults = (nextIngestion?.autofill_proposals ?? [])
        .filter((item) => item.status !== "conflict" && CASH_FLOW_FIELDS.has(item.field))
        .map((item) => item.proposal_id);
      setSelectedIds(new Set(defaults));
      setMessage("Đã phân tích xong. Hãy kiểm tra các đề xuất trước khi áp dụng vào hồ sơ.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xử lý dữ liệu Cash Flow.");
    } finally {
      setBusy(null);
      setProgress("");
    }
  }

  function toggleProposal(proposalId: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(proposalId)) next.delete(proposalId);
      else next.add(proposalId);
      return next;
    });
  }

  function selectAll() {
    const allSelected = selectableProposals.length > 0 && selectableProposals.every((item) => selectedIds.has(item.proposal_id));
    setSelectedIds(allSelected ? new Set() : new Set(selectableProposals.map((item) => item.proposal_id)));
  }

  async function applySelected() {
    const accepted = proposals.filter(
      (item) => selectedIds.has(item.proposal_id) && item.status !== "conflict" && CASH_FLOW_FIELDS.has(item.field),
    );
    if (!accepted.length) {
      setError("Hãy chọn ít nhất một đề xuất để áp dụng.");
      return;
    }
    setBusy("apply");
    setError("");
    setMessage("");
    try {
      const facts = { ...startup.facts };
      accepted.forEach((item) => {
        facts[item.field] = item.value;
      });
      const updated = await api.updateStartup(startup.id, { facts });
      onStartupUpdated(updated);
      setMessage(`Đã áp dụng ${accepted.length} đề xuất Cash Flow vào hồ sơ.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể áp dụng dữ liệu vào hồ sơ.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="cashFlowIntake" aria-label="Nhập dữ liệu Excel cho Cash Flow">
      <div className="cashFlowIntakeHeader">
        <div>
          <span className="cashFlowStep">BƯỚC 1 · DỮ LIỆU ĐẦU VÀO</span>
          <h4>Phân tích file Excel đã tải</h4>
          <p>Dòng tiền sử dụng các file `.xlsx` đã tải tại tab Bằng chứng.</p>
        </div>
        <span className="badgeCF neutral">{xlsxDocuments.length} file đã lưu</span>
      </div>

      <div className="cashFlowIntakeActions">
        <button className="primaryButton" type="button" disabled={busy !== null} onClick={analyzeSavedFiles}>
          {busy ? "Đang xử lý..." : "Phân tích file Excel đã tải"}
        </button>
        <span>{progress || "Tải hoặc xóa tài liệu tại tab Bằng chứng; tab này không tạo bản sao upload."}</span>
      </div>

      {error && <div className="cashFlowAlert error">{error}</div>}
      {message && <div className="cashFlowAlert info">{message}</div>}

      {ingestion && (
        <div className="cashFlowMappingSummary">
          <div className="cashFlowIntakeHeader compact">
            <div>
              <span className="cashFlowStep">BƯỚC 2 · KIỂM TRA ÁNH XẠ</span>
              <h4>AI đã nhận diện {ingestion.plan?.calls?.length ?? 0} bảng dữ liệu</h4>
            </div>
            <span className={`badgeCF ${ingestion.plan_source === "ai" ? "success" : "warning"}`}>
              {ingestion.plan_source === "ai" ? "AI mapping" : "Fallback mapping"}
            </span>
          </div>
          {(ingestion.plan?.calls ?? []).length > 0 && (
            <div className="cashFlowMappingGrid">
              {(ingestion.plan?.calls ?? []).map((call, index) => (
                <div className="cashFlowMappingCard" key={`${call.document_id}-${call.sheet}-${index}`}>
                  <span>{call.tool.replaceAll("_", " ")}</span>
                  <strong>{call.sheet}</strong>
                  <small>Header dòng {call.header_row} · {Object.keys(call.columns ?? {}).length} cột đã nối</small>
                </div>
              ))}
            </div>
          )}
          {(ingestion.warnings ?? []).map((warning) => (
            <div className="cashFlowAlert warning" key={warning}>{warning}</div>
          ))}
        </div>
      )}

      {proposals.length > 0 && (
        <div className="cashFlowProposalSection">
          <div className="cashFlowIntakeHeader compact">
            <div>
              <span className="cashFlowStep">BƯỚC 3 · DUYỆT DỮ LIỆU</span>
              <h4>Chọn dữ liệu muốn điền vào hồ sơ</h4>
              <p>Mỗi giá trị đều hiển thị nguồn Excel. Đề xuất xung đột sẽ bị khóa.</p>
            </div>
            <button className="secondaryButton" type="button" onClick={selectAll}>Chọn/bỏ tất cả</button>
          </div>
          <div className="cashFlowProposalList">
            {proposals.map((proposal) => (
              <ProposalRow
                key={proposal.proposal_id}
                proposal={proposal}
                checked={selectedIds.has(proposal.proposal_id)}
                onToggle={() => toggleProposal(proposal.proposal_id)}
              />
            ))}
          </div>
          <div className="cashFlowApplyBar">
            <div>
              <strong>{selectedIds.size} đề xuất được chọn</strong>
              <span>Chỉ cập nhật trường thuộc Cash Flow; các module khác được giữ nguyên.</span>
            </div>
            <button className="primaryButton" type="button" disabled={busy !== null || selectedIds.size === 0} onClick={applySelected}>
              {busy === "apply" ? "Đang áp dụng..." : "Áp dụng vào hồ sơ"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function ProposalRow({
  proposal,
  checked,
  onToggle,
}: {
  proposal: CashFlowAutofillProposal;
  checked: boolean;
  onToggle: () => void;
}) {
  const disabled = proposal.status === "conflict";
  return (
    <label className={`cashFlowProposal ${disabled ? "conflict" : ""}`}>
      <input type="checkbox" checked={checked && !disabled} disabled={disabled} onChange={onToggle} />
      <div className="cashFlowProposalBody">
        <div className="cashFlowProposalTitle">
          <strong>{FIELD_LABELS[proposal.field] ?? proposal.field}</strong>
          <span className={`badgeCF ${disabled ? "danger" : proposal.confidence === "high" ? "success" : "warning"}`}>
            {disabled ? "Xung đột" : proposal.confidence}
          </span>
        </div>
        <span className="cashFlowProposalValue">{formatValue(proposal.value)}</span>
        <div className="cashFlowProposalSources">
          {proposal.sources.map((source, index) => (
            <small key={`${source.document_id}-${source.sheet}-${index}`}>
              {source.filename} · {source.sheet}{source.range ? ` · ${source.range}` : ""}
            </small>
          ))}
          {proposal.warnings.map((warning) => <small className="warningText" key={warning}>{warning}</small>)}
        </div>
      </div>
    </label>
  );
}
