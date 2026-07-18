"use client";

import { ModuleFormPage } from "../_components/ModuleFormPage";
import { surroundingAreaGroups, surroundingAreaSections } from "./fields";

export default function SurroundingAreaProfilePage() {
  return (
    <ModuleFormPage
      eyebrow="MODULE 03"
      title="Surrounding Area Analysis"
      description="Địa chỉ, mức phụ thuộc vị trí và các tuyên bố cần kiểm chứng bằng dữ liệu bản đồ."
      sections={surroundingAreaSections}
      groupsBySection={surroundingAreaGroups}
      beforeSections={
        <section className="surface moduleOwnedSection">
          <div className="factSectionHeader">
            <div>
              <p className="eyebrow">ANALYSIS OUTPUT</p>
              <h2>Dữ liệu nhận được sau khi phân tích</h2>
            </div>
            <p>
              Đây là dữ liệu hệ thống tự lấy và tính từ Google Places API (New), không phải trường người dùng cần nhập.
            </p>
          </div>
          <div className="topicGroupList">
            <section className="topicGroup">
              <div className="topicGroupHeader">
                <strong>Vị trí và phạm vi</strong>
                <p>Tọa độ đã xác nhận, bán kính khảo sát, nhóm ngành và mức độ phụ thuộc vị trí.</p>
              </div>
            </section>
            <section className="topicGroup">
              <div className="topicGroupHeader">
                <strong>Đối thủ xung quanh</strong>
                <p>
                  Tên, loại hình, khoảng cách, rating, số lượt đánh giá, mức giá và link Google Maps; kèm số đối thủ
                  trong 250m, 500m và 1km.
                </p>
              </div>
            </section>
            <section className="topicGroup">
              <div className="topicGroupHeader">
                <strong>Tín hiệu nhu cầu</strong>
                <p>Văn phòng, trường học và trạm giao thông. Mật độ dân cư được đánh dấu thiếu vì Places không cung cấp.</p>
              </div>
            </section>
            <section className="topicGroup">
              <div className="topicGroupHeader">
                <strong>Chỉ số và kiểm chứng</strong>
                <p>
                  Đối thủ gần nhất, tỷ lệ chuỗi, tỷ lệ cung/cầu, điểm vị trí, kết luận từng tuyên bố và bằng chứng đi kèm.
                </p>
              </div>
            </section>
            <section className="topicGroup">
              <div className="topicGroupHeader">
                <strong>Chất lượng dữ liệu</strong>
                <p>
                  Trạng thái phân tích, nhóm truy vấn thành công, cảnh báo chạm trần 20 kết quả, dữ liệu thiếu, rủi ro và
                  phương pháp tính.
                </p>
              </div>
            </section>
          </div>
        </section>
      }
      previousHref="/startups/new/cash-flow"
      nextHref="/startups/new"
      nextLabel="Lưu và về tổng quan"
    />
  );
}
