# Surrounding Area Module - Update Roadmap

## 1. Mục tiêu nâng cấp

Module `surrounding_area` cần trở thành một công cụ thẩm định vị trí kinh doanh có thể:

- Quét nhanh khu vực từ địa chỉ hoặc tọa độ.
- Hiển thị bản đồ, ảnh vệ tinh, POI, đối thủ, khu dân cư và các điểm kéo nhu cầu một cách trực quan.
- Đánh giá độ phù hợp của vị trí theo ngành, mô hình kinh doanh và bán kính khách hàng mục tiêu.
- Kiểm chứng các tuyên bố của startup về vị trí bằng dữ liệu có nguồn gốc rõ ràng.
- Chỉ ra điểm còn thiếu, giới hạn dữ liệu và hành động khảo sát tiếp theo.
- Tránh tạo cảm giác "AI đoán mò"; mọi nhận định phải có evidence, metric hoặc warning đi kèm.

Nguyên tắc thiết kế: module không chỉ trả một điểm số, mà phải giúp người dùng nhìn vào khu vực và hiểu nhanh điều gì đang xảy ra.

## 2. Trạng thái hiện tại

Module hiện đã có các nền tảng quan trọng:

- Geocode địa chỉ và yêu cầu người dùng xác nhận tọa độ.
- Dữ liệu POI local từ OpenStreetMap.
- Phân loại ngành để xác định mức phụ thuộc vào vị trí.
- Tính toán competitor density, demand proxy, supply/demand, chain ratio, nearest competitor.
- Tích hợp satellite context từ Copernicus Sentinel-2.
- Optional Google Places enrichment khi có API key.
- Cache/rate limit/harden cho một số luồng.
- UI wizard có bản đồ, POI preview, metrics, claims và verdict.
- Test suite tương đối đầy đủ cho analyzer, geo, routes, POI store, satellite, places, verdict.

Điểm cần nâng tiếp:

- Trực quan hóa chưa đủ "ra quyết định nhanh".
- Chưa có data quality score rõ ràng.
- Chưa có so sánh nhiều vị trí.
- Chưa tự rút claims từ hồ sơ/tài liệu.
- Rating/price vẫn phụ thuộc API optional hoặc khảo sát thủ công.
- Map marker chưa có detail panel/cluster/layer UX mạnh.

## 3. Cải tiến theo cấp ưu tiên

### P0 - Module Quality, Accuracy, and Trust

#### 3.1. Chuẩn chất lượng cần đạt

Module cần được cải tiến theo 5 trụ cột:

1. Độ chính xác:
   - Tọa độ phải được xác nhận.
   - POI phải có source rõ ràng.
   - Đối thủ phải được xác định theo ngành, sản phẩm và category, không chỉ theo tên gần đúng.
   - Rating/price không được tự bịa; chỉ hiển thị khi có nguồn hoặc nhập thủ công.

2. Uy tín:
   - Mọi kết luận phải có evidence.
   - Mọi dữ liệu yếu phải có warning.
   - Report phải ghi rõ nguồn: OpenStreetMap, Copernicus, Google Places, user input hoặc manual survey.
   - Tách rõ "dữ liệu quan sát được" và "suy luận phân tích".

3. Hiệu quả:
   - Quét nhanh trong bán kính phổ biến 250m/500m/1km.
   - Cache geocode, POI query, satellite, places enrichment.
   - Không gọi API ngoài nếu không cần.
   - Analyzer trả kết quả đủ dùng ngay cả khi thiếu Places/rating.

4. Đầy đủ:
   - Có đủ dữ liệu về tọa độ, bán kính, đối thủ, demand drivers, residential, office/school/transport, satellite, claims, missing data.
   - Có mode F&B, retail, logistics/warehouse, office/SaaS.
   - Có workflow khảo sát rating/price thủ công khi API không có.

5. Trực quan và chuyên nghiệp:
   - Map đẹp, dễ đọc, có layer, legend, radius ring.
   - Metrics được gom thành insight cards.
   - POI/đối thủ có bảng top-N, marker detail, source badge.
   - Người dùng nhìn 30 giây là hiểu khu vực đang mạnh/yếu ở đâu.

#### 3.2. Đảm bảo dữ liệu POI luôn sẵn sàng

Việc cần làm:

- Thêm healthcheck cho `poi.db`.
- Khi thiếu `poi.db`, API trả lỗi có hướng dẫn setup cụ thể.
- Docker entrypoint kiểm tra data trước khi start app.
- Compose mount `backend/data` và không commit DB/PBF lớn.
- Script `setup_data` cần idempotent:
  - Nếu có DB hợp lệ thì bỏ qua.
  - Nếu thiếu PBF thì tải.
  - Nếu thiếu DB thì extract.
  - Nếu file hỏng thì báo rõ.

Acceptance criteria:

- Fresh clone chạy Docker không fail im lặng.
- `/surrounding/map` báo lỗi dễ hiểu khi thiếu DB.
- Không có file `.db`, `.pbf`, `.part` bị commit.

#### 3.3. Chuẩn hóa đầu vào location

Việc cần làm:

- Map toàn bộ field profile sang analyzer:
  - `exact_location`.
  - `location_type`.
  - `area_m2`.
  - `tenure`.
  - `rent_cost`.
  - `operating_hours`.
  - `location_dependency`.
  - `target_customer_radius_m`.
  - `logistics_requirements`.
  - `known_nearby_competitors`.
- Ưu tiên dữ liệu theo thứ tự:
  1. Input wizard hiện tại.
  2. Facts đã lưu trong startup profile.
  3. Analysis result gần nhất.
  4. Default theo ngành.
- Khi thiếu input quan trọng, UI hiển thị action rõ ràng thay vì chỉ báo lỗi chung.

Acceptance criteria:

- Người dùng nhập ở profile thì wizard tự nhận lại.
- Analyzer không bỏ sót bán kính khách hàng mục tiêu.
- Known competitors từ profile xuất hiện trong report/matching.
- Không còn trường hợp cùng một dữ liệu nhưng nhiều key khác nhau gây mất ngữ cảnh.

#### 3.4. Regression checklist cho module và luồng liên quan

Việc cần làm:

- Tạo checklist chất lượng trước khi coi module là xong:
  - Geocode hoạt động.
  - Confirm tọa độ hoạt động.
  - Map load được POI.
  - Satellite context trả response hoặc warning rõ.
  - Analysis trả verdict theo claim.
  - Profile facts được đọc lại đúng.
  - Report không khẳng định quá mức khi thiếu dữ liệu.
  - Business model, cash flow, upload document và copilot không bị ảnh hưởng.

Acceptance criteria:

- Checklist có thể chạy thủ công trong 5-10 phút.
- Có test tự động cho phần analyzer/route quan trọng.
- Không mất chức năng cũ khi nâng UX.

## 4. Cải tiến dữ liệu và độ tin cậy

### 4.1. Data Quality Score

Thêm một điểm chất lượng dữ liệu riêng, tách khỏi score đánh giá vị trí.

Các thành phần đề xuất:

- Geocode confidence.
- POI coverage tier.
- POI density trong bán kính 1km.
- Tỷ lệ POI có tên.
- Tỷ lệ POI là point thật so với polygon centroid.
- Satellite scene availability.
- Satellite cloud cover.
- Places/rating availability.
- Dữ liệu profile có đủ location type, radius, rent, known competitors hay không.

Output đề xuất:

```json
{
  "data_quality": {
    "score": 78,
    "tier": "good",
    "signals": [
      "Geocode confidence high",
      "POI density sufficient",
      "Satellite scene usable but cloudy"
    ],
    "warnings": [
      "Google Maps match not verified",
      "No rating data configured"
    ]
  }
}
```

UI cần hiển thị:

- Card "Độ tin cậy dữ liệu".
- Danh sách warning ngắn.
- Tooltip giải thích vì sao score thấp/cao.

### 4.2. Source Confidence Per POI

Mỗi POI cần có trạng thái tin cậy:

- `source`: `openstreetmap`, `google_places`, `manual_survey`, `user_provided`.
- `source_id`.
- `position_quality`: `point`, `polygon_centroid`, `address_geocode`, `unknown`.
- `maps_match_status`: `unverified_google_maps`, `candidate_match`, `verified_google_maps`.
- `last_seen_at` nếu có.

UI cần:

- Badge cho từng POI.
- Filter "Chỉ xem POI đã verify".
- Cảnh báo khi top competitor chỉ là centroid.

### 4.3. Data Freshness

Việc cần làm:

- Lưu ngày build `poi.db`.
- Lưu bbox/region của DB.
- API `/surrounding/map` trả metadata:

```json
{
  "data_metadata": {
    "poi_db_built_at": "2026-07-18",
    "region": "vietnam",
    "provider": "openstreetmap",
    "coverage": "local_extract"
  }
}
```

UI cần:

- Hiển thị "Dữ liệu OSM build ngày...".
- Warning nếu DB quá 30/60/90 ngày.

### 4.4. Trust Label cho từng kết luận

Mỗi finding/verdict cần có trust label:

- `high_trust`: Có tọa độ xác nhận, POI đủ dày, source rõ, metric trực tiếp.
- `medium_trust`: Có dữ liệu đủ để suy luận nhưng còn thiếu rating/price hoặc một phần POI chưa verify.
- `low_trust`: Thiếu POI DB, geocode yếu, satellite mây nhiều, claim không có evidence trực tiếp.

UI cần:

- Badge "Tin cậy cao/vừa/thấp".
- Tooltip nêu lý do.
- Không để người dùng nhầm score cao với dữ liệu chắc chắn.

Output đề xuất:

```json
{
  "trust": {
    "level": "medium_trust",
    "reasons": [
      "Confirmed coordinates",
      "Sufficient POI density",
      "Google Maps matching not verified"
    ]
  }
}
```

### 4.5. Evidence Traceability

Mỗi metric quan trọng cần truy ngược được:

- Metric lấy từ tool nào.
- Input radius/lat/lon nào.
- POI nào đóng góp vào kết quả.
- Provider/source nào.
- Thời điểm truy xuất.

Ví dụ:

```json
{
  "evidence_trace": {
    "metric": "competitor_density_500m",
    "value": 12,
    "source": "openstreetmap_poi_db",
    "input": {"radius_m": 500},
    "poi_ids": ["n123", "w456"]
  }
}
```

Điều này giúp report có uy tín hơn và dễ debug khi người dùng hỏi "vì sao hệ thống nói khu này cạnh tranh cao?".

## 5. Cải tiến thuật toán phân tích

### 5.1. Industry-Specific Scoring

Không dùng một công thức chung cho mọi ngành. Cần profile theo ngành:

F&B:

- Demand drivers: dân cư, văn phòng, trường học, giao thông.
- Competition: số đối thủ 250m/500m/1km.
- Chain pressure: tỷ lệ chuỗi lớn.
- Visibility proxy: POI density, road/amenity density.
- Risk: bão hòa, nhiều chuỗi, thiếu dân cư.

Retail:

- Dân cư và foot traffic proxy.
- Đối thủ cùng category.
- Gần trường học/văn phòng/điểm giao thông.
- Parking/logistics nếu có dữ liệu.

Logistics/warehouse:

- Gần đường lớn.
- Gần khu công nghiệp/kho.
- Xa khu dân cư nếu cần giảm noise/risk.
- Không dùng F&B density làm demand chính.

SaaS/online:

- Mặc định `not_applicable` hoặc `supporting`.
- Chỉ đánh giá vị trí như yếu tố tuyển dụng/vận hành nếu có văn phòng.

Acceptance criteria:

- Analyzer trả `scoring_profile`.
- Report giải thích vì sao ngành này dùng các tín hiệu đó.

### 5.2. Better Competitor Detection

Hiện đối thủ dựa theo mapping ngành sang OSM tags. Cần nâng:

- Taxonomy nhiều tầng:
  - `industry`.
  - `business_model`.
  - `core_products`.
  - `price_segment` nếu có.
- Competitor không chỉ cùng category, mà có thể là substitute.
- Known competitors từ profile cần được cross-check với POI gần đó.
- Nếu không match được, report rõ "user-provided competitor not found in OSM".

Output đề xuất:

```json
{
  "competitor_detection": {
    "strategy": "industry_taxonomy_v2",
    "direct_categories": ["restaurant", "cafe", "fast_food"],
    "substitute_categories": ["food_court", "bar"],
    "known_competitor_matches": [
      {
        "name": "Highlands Coffee",
        "status": "matched",
        "distance_m": 198,
        "confidence": "medium"
      }
    ]
  }
}
```

### 5.3. Saturation Index

Thêm chỉ số bão hòa khu vực:

- Competitor count weighted by distance.
- Chain competitor weight cao hơn.
- Demand proxy offset.
- Nếu demand cao và competition cao: "high-demand/high-competition".
- Nếu demand thấp và competition cao: "weak location".
- Nếu demand cao và competition thấp: "opportunity zone".

Output:

```json
{
  "saturation": {
    "index": 0.72,
    "tier": "high",
    "quadrant": "high_demand_high_competition",
    "explanation": "Demand proxy high but direct competitors are dense within 500m"
  }
}
```

### 5.4. Rent Reasonableness

Nếu user nhập `rent_cost` và `area_m2`, module cần đánh giá sơ bộ:

- Rent per m2.
- So với input tự khai hoặc benchmark nếu có nguồn.
- Nếu không có benchmark, chỉ flag:
  - missing benchmark.
  - unusually high burden relative to revenue.

Kết hợp với finance facts:

- `monthly_revenue`.
- `monthly_expense`.
- `rent_cost`.
- Rent/revenue ratio.

Không được khẳng định "rẻ" hoặc "đắt" nếu không có benchmark.

### 5.5. Location Fit Score v2

Tạo score mới có cấu trúc rõ ràng, không gộp mơ hồ:

```json
{
  "location_fit": {
    "score": 74,
    "label": "phu_hop_co_dieu_kien",
    "components": {
      "demand_strength": 82,
      "competition_pressure": 68,
      "accessibility": 61,
      "operational_fit": 70,
      "data_quality": 78
    },
    "top_strengths": [
      "Residential and amenity density are strong within 1km",
      "Demand proxy is above module threshold"
    ],
    "top_risks": [
      "Direct competitors are dense within 500m",
      "Rating/price data has not been verified"
    ]
  }
}
```

Nguyên tắc:

- `data_quality` không được cộng quá mạnh vào location fit, chỉ dùng để giảm độ tự tin.
- Nếu data quality thấp, location score vẫn có thể tính nhưng confidence phải thấp.
- Score phải giải thích được bằng component, không chỉ là một số.

### 5.6. Demand Driver Taxonomy

Tách các POI tạo nhu cầu:

- `residential`: chung cư, khu dân cư, apartment, housing estate.
- `office`: office, coworking, commercial building.
- `school`: school, university, kindergarten.
- `transport`: bus stop, station, parking, main road access.
- `tourism`: hotel, attraction, museum, landmark.
- `healthcare`: hospital, clinic, pharmacy.
- `retail_anchor`: mall, supermarket, market.

Tùy ngành, trọng số khác nhau:

- F&B: residential, office, school, tourism, retail_anchor.
- Retail: residential, retail_anchor, transport.
- Healthcare: residential, office, transport.
- Logistics: transport, warehouse, industrial.

### 5.7. Negative Signals

Không chỉ đếm điểm tốt. Cần có tín hiệu tiêu cực:

- Quá nhiều đối thủ gần.
- POI density quá thấp.
- Thiếu dân cư trong bán kính mục tiêu.
- Địa điểm chỉ là centroid, không phải point.
- Satellite scene mây nhiều.
- Không có rating/price cho top competitors.
- Known competitor do user nhập nhưng không tìm thấy.
- Location dependency là primary nhưng thiếu tọa độ xác nhận.

Report phải phân biệt:

- `risk`: ảnh hưởng trực tiếp tới quyết định.
- `limitation`: giới hạn dữ liệu.
- `next_action`: việc cần làm tiếp.

## 6. Cải tiến rating, price và dữ liệu bên thứ ba

### 6.1. Free Baseline

Luôn tạo Google Maps survey link cho top competitors:

- Search by name + lat/lon.
- Search by tọa độ nếu không có tên.
- UI có nút "Khảo sát rating/giá".
- Cho phép người dùng nhập rating/price thủ công sau khảo sát.

### 6.2. Optional Providers

Provider ưu tiên:

- Google Places API:
  - Rating.
  - User ratings total.
  - Price level.
  - Place ID.
- Foursquare Places:
  - Category.
  - Popularity/rating nếu available theo plan.
- Yelp Fusion:
  - Chỉ hữu ích ở một số thị trường, cần kiểm tra coverage Việt Nam.

Thiết kế provider:

- Không hard-code vào analyzer.
- Dùng interface chung:

```python
class PlaceEnrichmentProvider:
    def enrich(self, pois: list[Poi]) -> PlaceEnrichmentResult:
        ...
```

### 6.3. Cache and Cost Control

Việc cần làm:

- Cache theo `provider + source_id + rounded_lat + rounded_lon`.
- TTL 30 ngày.
- Chỉ enrich top 10-20 POI.
- Rate limit per IP/session.
- Không gọi provider nếu không có API key.

Acceptance criteria:

- Không cháy quota khi user refresh nhiều lần.
- Report luôn nói rõ rating/price đến từ đâu.

## 7. Cải tiến ảnh vệ tinh và bản đồ

### 7.1. Satellite Layer UX

Hiện có Copernicus context. Cần nâng UI:

- Hiển thị quicklook/thumbnail nếu có.
- Hiển thị ngày chụp, cloud cover, GSD.
- Nút mở product/source.
- Warning nếu ảnh nhiều mây.
- Hiển thị bbox hoặc bán kính quét phủ trên map.

### 7.2. Map Layer Controls

Thêm layer/toggle:

- Site.
- Competitors.
- Eateries.
- Residential.
- Office/school/transport.
- Satellite.
- Street map.
- Radius rings: 250m, 500m, 1km, custom.

UX cần:

- Toggle không làm layout nhảy.
- Legend luôn nhìn thấy.
- Marker có màu nhất quán.
- Trên mobile, map cao tối thiểu 420px và control không che marker.

### 7.3. Marker Detail Panel

Khi click POI:

- Mở panel bên phải hoặc bottom sheet mobile.
- Hiển thị:
  - Tên.
  - Category.
  - Distance.
  - Source.
  - Position quality.
  - Google Maps survey link.
  - Rating/price nếu có.
  - "Đánh dấu là đối thủ" hoặc "Không phải đối thủ".

### 7.4. Clustering

Khi nhiều POI:

- Dùng marker clustering.
- Zoom thấp hiển thị cluster count.
- Zoom cao bung marker.
- Không render quá nhiều marker gây lag.

### 7.5. Professional Visual Design Goals

Giao diện map cần đạt cảm giác như công cụ phân tích chuyên nghiệp:

- Map chiếm vai trò trung tâm, không bị nhét trong card nhỏ.
- Sidebar chỉ chứa thông tin hỗ trợ: legend, layer, selected POI, data quality.
- Màu marker có ý nghĩa:
  - Site: xanh đậm.
  - Competitor: cam/đỏ đất.
  - Demand driver: xanh teal.
  - Residential: xanh nhạt.
  - Transport: xanh dương.
  - Warning/low confidence: viền đứt hoặc badge cảnh báo.
- Không dùng quá nhiều màu cùng lúc; layer toggle giúp giảm nhiễu.
- Typography nhỏ gọn, dễ quét.
- Các số lớn chỉ dùng cho metric quan trọng.
- Trạng thái loading/error/empty phải đẹp, không để map trắng.

### 7.6. Insight Cards Above Map

Trước bản đồ cần có 4-6 card đọc nhanh:

- Độ phù hợp vị trí.
- Mức cạnh tranh.
- Nguồn cầu xung quanh.
- Độ tin cậy dữ liệu.
- Đối thủ gần nhất.
- Việc cần khảo sát tiếp.

Card phải có:

- Label ngắn.
- Số hoặc verdict chính.
- Hint một dòng.
- Màu trạng thái vừa đủ, không biến thành dashboard lòe loẹt.

### 7.7. Smart Filters

Thêm filter:

- Radius: 250m, 500m, 1km, custom.
- Type: competitors, residential, office, school, transport, eateries.
- Confidence: verified, unverified, centroid.
- Chain: chain, independent.
- Distance sort.
- Rating/price availability nếu có.

Filter cần realtime nhưng không gây reload toàn trang.

### 7.8. User Correction Loop

Cho phép người dùng sửa dữ liệu quan sát:

- Đánh dấu POI là "đúng là đối thủ".
- Đánh dấu POI là "không phải đối thủ".
- Thêm đối thủ thủ công.
- Nhập rating/price khảo sát thủ công.
- Ghi chú khảo sát tại chỗ.

Dữ liệu user correction cần lưu vào startup facts hoặc analysis metadata để lần sau module học theo hồ sơ đó.

## 8. Cải tiến UX report

### 8.1. Executive Summary

Report nên mở đầu bằng 4 card:

- Vị trí có phù hợp không?
- Mức cạnh tranh.
- Nguồn cầu xung quanh.
- Độ tin cậy dữ liệu.

Ví dụ:

```text
Phù hợp có điều kiện
Khu vực có demand proxy tốt nhưng cạnh tranh F&B dày trong 500m.
Nên khảo sát giá thuê và rating top 10 đối thủ trước khi quyết định.
```

### 8.2. Evidence-First Verdict

Mỗi claim cần có:

- Claim.
- Verdict: xác nhận, bác bỏ, chưa đủ dữ liệu.
- Confidence.
- Evidence list.
- Metrics liên quan.
- Warning nếu data source yếu.

Không nên chỉ có text giải thích.

### 8.3. Missing Data as Action Items

Missing data cần chuyển thành hành động:

- "Nhập chi phí thuê để tính rent/revenue ratio".
- "Xác nhận top 5 đối thủ trên Google Maps".
- "Upload hợp đồng thuê để đối chiếu chi phí".
- "Nhập bán kính khách hàng mục tiêu".

UI nên có checkbox hoặc CTA gắn với từng missing item.

### 8.4. Exportable Report

Thêm xuất report:

- JSON cho hệ thống.
- Markdown/PDF cho investor.
- Include:
  - Map snapshot.
  - Metrics.
  - Top POIs.
  - Verdicts.
  - Assumptions and limitations.

### 8.5. Investor-Grade Narrative

Report cần viết theo kiểu thẩm định đầu tư:

- Không dùng ngôn ngữ chắc chắn khi dữ liệu chưa chắc.
- Mỗi kết luận có "because".
- Mỗi rủi ro có "impact" và "next action".
- Có phần "What would change our view?" để nói dữ liệu nào có thể làm đổi kết luận.

Cấu trúc đề xuất:

1. Verdict tổng quan.
2. Vì sao vị trí này có/không phù hợp.
3. Các bằng chứng chính.
4. Rủi ro vị trí.
5. Dữ liệu còn thiếu.
6. Việc cần khảo sát tiếp.
7. Phụ lục nguồn dữ liệu và giới hạn.

### 8.6. Decision Support, Not Just Analysis

Module cần trả lời trực tiếp các câu hỏi:

- Có nên mở/giữ địa điểm này không?
- Điều kiện nào cần xác minh trước khi quyết định?
- Đối thủ nào cần khảo sát ngay?
- Nếu gọi vốn, phần vị trí hỗ trợ hay làm yếu câu chuyện đầu tư?
- Có vị trí khác nên so sánh không?

Output nên có:

```json
{
  "decision_support": {
    "recommendation": "proceed_with_validation",
    "confidence": "medium",
    "must_verify": [
      "Manual survey top 10 competitors on Google Maps",
      "Confirm rent/revenue ratio",
      "Validate residential foot traffic during peak hours"
    ],
    "deal_questions": [
      "How much revenue comes from walk-in customers?",
      "What is the lease duration and renewal risk?"
    ]
  }
}
```

## 9. Claim Extraction

### 9.1. Tự rút claim từ profile

Nguồn:

- `location_dependency`.
- `known_nearby_competitors`.
- `target_customer_radius_m`.
- `logistics_requirements`.
- `problem/solution`.
- `traction`.
- `expansion_plan`.

Claim mẫu:

- "Startup phụ thuộc khách hàng xung quanh".
- "Khu vực có nhiều dân cư".
- "Ít đối thủ trực tiếp trong bán kính mục tiêu".
- "Vị trí thuận lợi cho giao hàng".

### 9.2. Tự rút claim từ tài liệu

Nguồn:

- Pitch deck.
- Business plan.
- Hợp đồng thuê.
- Hình ảnh địa điểm.
- Báo cáo bán hàng theo khu vực.

Yêu cầu:

- Claim extraction phải có citation.
- User được duyệt/sửa/xóa claim trước khi phân tích.
- Analyzer chỉ dùng claim đã duyệt.

### 9.3. Human-in-the-loop

Workflow đề xuất:

1. AI đề xuất claims.
2. User duyệt claims.
3. Module chạy verification.
4. User có thể thêm evidence thủ công.
5. Report final ghi rõ claim nào do user/AI tạo.

## 10. So sánh nhiều vị trí

### 10.1. Location Comparison Mode

Cho phép thêm nhiều địa điểm:

- Current location.
- Candidate A.
- Candidate B.
- Competitor location.

Metrics so sánh:

- Competitor count 500m/1km.
- Demand proxy.
- Saturation index.
- Data quality.
- Nearest competitor.
- Chain pressure.
- Satellite quality.
- Rent/revenue nếu có.

Output:

```json
{
  "comparison": [
    {
      "label": "Current",
      "score": 68,
      "strengths": ["high residential proxy"],
      "risks": ["high competition within 500m"]
    },
    {
      "label": "Candidate A",
      "score": 77,
      "strengths": ["lower direct competition"],
      "risks": ["weaker transport proxy"]
    }
  ]
}
```

UI:

- Bảng so sánh.
- Map hiển thị nhiều center.
- Ranking rõ ràng.
- Không dùng màu xanh/đỏ quá đơn giản; cần giải thích trade-off.

## 11. Backend architecture improvements

### 11.1. Clear Service Layers

Tách lớp:

- `providers`: geocode, satellite, places.
- `data_store`: POI DB access.
- `tools`: pure calculations.
- `verdict`: claim verification.
- `analyzer`: orchestration.
- `routes`: HTTP IO.

Rule:

- Tools không gọi network.
- Providers không chứa business scoring.
- Analyzer không query DB trực tiếp nếu đã có service.

### 11.2. Async Safety

Việc cần làm:

- SQLite access qua thread-local connections.
- DB queries chạy bằng `asyncio.to_thread` nếu route async.
- Không share connection global giữa event loop.
- Add tests cho concurrent map requests.

### 11.3. Error Taxonomy

Chuẩn hóa lỗi:

- `INSUFFICIENT_DATA`.
- `GEOCODE_UNAVAILABLE`.
- `POI_DB_MISSING`.
- `POI_DB_STALE`.
- `SATELLITE_PROVIDER_UNAVAILABLE`.
- `PLACES_PROVIDER_UNCONFIGURED`.
- `RATE_LIMITED`.

Mỗi lỗi cần:

- user-facing message.
- developer detail.
- recommended action.

## 12. Frontend architecture improvements

### 12.1. Component Split

Tách `SurroundingArea.tsx` thành:

- `SurroundingAreaWizard`.
- `LocationSearchStep`.
- `MapPanel`.
- `MetricCards`.
- `PoiList`.
- `SatellitePanel`.
- `ClaimComposer`.
- `VerdictReport`.
- `DataQualityPanel`.

Lợi ích:

- Dễ test.
- Dễ nâng UI.
- Không để một file quá lớn.

### 12.2. State Persistence

Lưu lại:

- Last selected radius.
- Last confirmed center.
- Last layer toggles.
- Last claims.
- Last analysis result.

Nguồn lưu:

- Backend `startup.facts` hoặc `analysis.details`.
- Local storage chỉ dùng cho UI preference, không dùng làm source of truth.

### 12.3. UX Interactions

Thêm:

- Loading skeleton cho map/POI/satellite.
- Toast copy coordinates.
- Disabled state rõ khi chưa confirm tọa độ.
- Keyboard accessible controls.
- Empty states theo ngữ cảnh.
- Mobile bottom sheet cho marker detail.

## 13. Security, compliance, and privacy

### 13.1. API Key Handling

- Không expose provider keys ra frontend.
- Places/geocode gọi qua backend.
- Log không in API key.
- `.env.example` chỉ có tên biến, không có secret.

### 13.2. Rate Limiting

Endpoint cần rate limit:

- `/surrounding/geocode`.
- `/surrounding/map`.
- `/surrounding/satellite`.
- `/analyses/surrounding_area`.

Mức đề xuất:

- Geocode: 30 requests/min/IP.
- Map: 60 requests/min/IP.
- Satellite: 20 requests/min/IP.
- Analysis: 10 requests/min/startup.

### 13.3. Data Attribution

UI/report phải ghi:

- OpenStreetMap attribution.
- Copernicus/Sentinel attribution.
- Google Places/Foursquare nếu dùng.
- Ngày truy cập provider.

## 14. Observability

### 14.1. Logs

Log structured:

- startup_id.
- module.
- lat/lon rounded.
- radius_m.
- provider used.
- poi_count.
- competitor_count.
- latency_ms.
- warnings.

Không log:

- API key.
- dữ liệu cá nhân không cần thiết.

### 14.2. Metrics

Nên đo:

- Geocode success rate.
- Map query latency.
- POI DB missing/stale count.
- Satellite provider failure rate.
- Places enrichment quota/error.
- Analysis status distribution.

### 14.3. Debug Panel

Trong dev mode:

- Hiển thị tool calls.
- Hiển thị raw metrics.
- Hiển thị cache hit/miss.
- Hiển thị provider warnings.

## 15. Test plan

### 15.1. Unit Tests

Cần test:

- Industry taxonomy.
- Competitor detection.
- Distance/radius filtering.
- Demand proxy.
- Saturation index.
- Data quality scoring.
- Claim verdict.
- Error taxonomy.

### 15.2. Integration Tests

Cần test:

- Geocode cache.
- Map route với POI DB fake.
- Satellite provider mocked.
- Places provider mocked.
- Analyzer full flow.
- Missing DB behavior.
- Rate limit behavior.

### 15.3. Frontend Tests

Nên thêm:

- Component render smoke.
- Radius input updates map query.
- Confirm coordinate unlocks analysis.
- POI click opens detail panel.
- Data quality warnings render.
- Mobile layout does not overflow.

### 15.4. E2E Smoke

Flow:

1. Tạo startup F&B.
2. Nhập địa điểm.
3. Geocode.
4. Confirm tọa độ.
5. Load map.
6. Xem POI/competitors.
7. Chạy analysis.
8. Kiểm verdict.
9. Mở report.
10. Hỏi copilot về vị trí.

## 16. Suggested milestones

### Milestone 1 - Trustworthy Core

Thời lượng: 1-2 ngày.

- POI DB healthcheck.
- Data quality score v1.
- Trust label cho verdict/finding.
- Source confidence per POI.
- Field mapping đầy đủ từ profile sang analyzer.
- Better error and limitation messages.

### Milestone 2 - Professional Map Experience

Thời lượng: 2-3 ngày.

- Layer toggles.
- Radius rings.
- Marker detail panel.
- POI filtering.
- Improved mobile map.
- Insight cards above map.
- Source/data quality sidebar.

### Milestone 3 - Accuracy and Intelligence

Thời lượng: 3-5 ngày.

- Saturation index.
- Industry-specific scoring.
- Known competitor matching.
- Claim extraction from profile.
- More transparent verdicts.
- Demand driver taxonomy.
- Negative signals and next actions.

### Milestone 4 - Rating, Price, and Manual Survey

Thời lượng: 2-4 ngày.

- Google Places/Foursquare provider interface.
- Cache and quota control.
- Manual survey input.
- Rating/price UI.
- User correction loop for POI and competitors.

### Milestone 5 - Compare, Decide, and Export

Thời lượng: 3-5 ngày.

- Multi-location comparison.
- Export report.
- Investor-ready summary.
- Map snapshot in report.
- Decision support recommendations.

## 17. Definition of Done

Một cải tiến của module chỉ được coi là xong khi:

- Có test phù hợp.
- Có UI state cho loading/error/empty.
- Có source attribution.
- Có warning nếu dữ liệu chưa đủ tin cậy.
- Không làm hỏng business model/cash flow/document/chat flows.
- Có kiểm thử hoặc smoke test tương ứng cho luồng quan trọng.
- Có ghi chú trong README hoặc docs nếu thay đổi behavior.
- UI không bị overflow trên mobile/desktop.
- Report không đưa ra kết luận mạnh khi data quality thấp.

## 18. Rủi ro cần quản lý

### Dữ liệu OSM không khớp Google Maps

Giải pháp:

- Gắn nhãn unverified.
- Link khảo sát Maps.
- Optional provider matching.

### Rating/price không miễn phí ổn định

Giải pháp:

- Free baseline là survey link/manual input.
- API enrichment là optional.
- Cache mạnh để giảm quota.

### Người dùng hiểu nhầm score là kết luận tuyệt đối

Giải pháp:

- Tách location score và data quality score.
- Luôn hiển thị assumptions/limitations.
- Dùng verdict theo claim thay vì một câu kết luận chung chung.

### Map quá nhiều marker gây rối

Giải pháp:

- Cluster.
- Filter.
- Top-N list.
- Layer toggles.

### Satellite ảnh mây hoặc không có ảnh

Giải pháp:

- Hiển thị cloud cover.
- Không dùng ảnh mây để kết luận mạnh.
- Cho phép fallback street map/OSM.

## 19. Quick wins đề xuất làm ngay

1. Thêm `data_quality` vào analyzer output.
2. Thêm panel "Độ tin cậy dữ liệu" trên UI.
3. Thêm marker detail panel.
4. Thêm radius selector 250m/500m/1km/custom.
5. Thêm source confidence badge cho POI.
6. Thêm known competitor matching.
7. Thêm saturation index v1.
8. Thêm auto-claim extraction từ profile facts.
9. Thêm manual rating/price input cho top competitors.
10. Thêm user correction loop: đánh dấu đúng/sai đối thủ.

## 20. Kết luận

Hướng cải tiến chính là chuyển module từ "chạy phân tích trả report" sang "không gian khảo sát vị trí có bằng chứng".

Trải nghiệm tốt nhất cần đạt:

- Người dùng nhập địa chỉ.
- Hệ thống xác nhận tọa độ.
- Bản đồ hiện rõ đối thủ, demand drivers, residential và ảnh vệ tinh.
- Các metric giải thích được vì sao vị trí tốt/xấu.
- Mọi claim đều có verdict và evidence.
- Những gì chưa chắc chắn được ghi rõ, không che giấu.
- Người dùng biết ngay cần khảo sát thêm gì trước khi ra quyết định.
