# Document Chatbot

Module sở hữu retrieval và quy tắc grounded Q&A. Gemini chỉ nhận các đoạn đã retrieval trong phạm vi một `startup_id`; nội dung tài liệu được xem là dữ liệu, không phải instruction.

Baseline hiện tại dùng lexical retrieval. Vector store, embedding và reranker sẽ được thay phía sau interface `retrieve` mà không đổi API chat.

