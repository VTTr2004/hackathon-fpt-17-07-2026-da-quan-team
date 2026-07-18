"use client";

import { ChangeEvent, useRef } from "react";

import { useProfileDraft } from "../_components/ProfileDraftProvider";

function fileKey(file: File): string {
  return `${file.webkitRelativePath || file.name}:${file.size}:${file.lastModified}`;
}

export function CashFlowDraftFiles() {
  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const { cashFlowFiles, setCashFlowFiles } = useProfileDraft();

  function addFiles(event: ChangeEvent<HTMLInputElement>) {
    const incoming = Array.from(event.target.files ?? []).filter((file) => file.name.toLowerCase().endsWith(".xlsx"));
    const merged = new Map(cashFlowFiles.map((file) => [fileKey(file), file]));
    incoming.forEach((file) => merged.set(fileKey(file), file));
    setCashFlowFiles(Array.from(merged.values()));
    event.target.value = "";
  }

  function configureFolderInput(element: HTMLInputElement | null) {
    folderInputRef.current = element;
    if (element) {
      element.setAttribute("webkitdirectory", "");
      element.setAttribute("directory", "");
    }
  }

  return (
    <section className="surface moduleOwnedSection cashFlowDraftIntake">
      <div className="factSectionHeader">
        <div>
          <p className="eyebrow">EXCEL INPUT</p>
          <h2>Nhập dữ liệu Cash Flow từ Excel</h2>
        </div>
        <p>Chọn nhiều file hoặc cả folder. AI sẽ nhận diện cấu trúc và gọi tool tính toán sau khi hồ sơ được tạo.</p>
      </div>

      <div className="cashFlowDropzone">
        <input aria-label="Chọn các file Excel Cash Flow" type="file" accept=".xlsx" multiple onChange={addFiles} />
        <input ref={configureFolderInput} className="cashFlowHiddenInput" type="file" accept=".xlsx" multiple onChange={addFiles} />
        <div>
          <strong>Thả hoặc chọn các file `.xlsx`</strong>
          <span>Sổ quỹ, bán hàng, mua hàng và dữ liệu vận hành có thể nằm trong các file khác nhau.</span>
        </div>
        <button className="secondaryButton" type="button" onClick={() => folderInputRef.current?.click()}>
          Chọn folder
        </button>
      </div>

      {cashFlowFiles.length > 0 ? (
        <div className="cashFlowFileQueue">
          <div className="cashFlowQueueHeader">
            <strong>{cashFlowFiles.length} file sẽ được phân tích</strong>
            <button type="button" onClick={() => setCashFlowFiles([])}>Xóa danh sách</button>
          </div>
          {cashFlowFiles.map((file) => (
            <div className="cashFlowFileItem" key={fileKey(file)}>
              <span className="fileIcon">XLSX</span>
              <div>
                <strong>{file.webkitRelativePath || file.name}</strong>
                <small>{new Intl.NumberFormat("vi-VN").format(Math.ceil(file.size / 1024))} KB</small>
              </div>
              <button
                type="button"
                aria-label={`Bỏ ${file.name}`}
                onClick={() => setCashFlowFiles(cashFlowFiles.filter((item) => fileKey(item) !== fileKey(file)))}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="cashFlowDraftNotice">
          Bạn có thể bỏ qua Excel và nhập tay các trường bên dưới. File đã chọn chỉ được giữ trong tab hiện tại.
        </div>
      )}

      <div className="cashFlowDraftPipeline" aria-label="Luồng xử lý dữ liệu Excel">
        <span><strong>1</strong> Tạo hồ sơ</span>
        <span><strong>2</strong> Upload Excel</span>
        <span><strong>3</strong> AI mapping</span>
        <span><strong>4</strong> Tool tính toán</span>
        <span><strong>5</strong> Duyệt đề xuất</span>
      </div>
    </section>
  );
}
