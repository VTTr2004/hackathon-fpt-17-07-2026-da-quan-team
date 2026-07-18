"use client";

import { FormEvent, useState } from "react";

import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/types";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [role, setRole] = useState<UserRole>("startup");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function switchMode(next: "login" | "register") {
    setMode(next);
    setError("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await login(email, password, remember);
      } else {
        await register({ email, password, full_name: String(form.get("full_name") ?? "").trim(), role }, remember);
      }
      window.location.href = "/";
    } catch (err) {
      let message = err instanceof Error ? err.message : "";
      if (!message || message.startsWith("API error")) {
        message = mode === "login"
          ? "Email hoặc mật khẩu không đúng."
          : "Không thể tạo tài khoản. Vui lòng kiểm tra lại thông tin.";
      }
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="authShell">
      <section className="authBrandPane" aria-hidden="true">
        <div className="authGlow" />
        <div className="authBrandTop">
          <p className="authEyebrow">Venture Due Diligence</p>
          <h1 className="authHeadline">Thắp sáng con đường khởi nghiệp của bạn.</h1>
          <p className="authSub">
            Hệ thống thẩm định chuyên sâu, dẫn chứng minh bạch dành cho nhà đầu tư và doanh nhân chiến lược.
          </p>
        </div>
        <div className="authBrandBottom">
          <div className="authStats">
            <div className="authStat">
              <strong>3 module</strong>
              <span>Phân tích độc lập</span>
            </div>
            <div className="authStat">
              <strong>Evidence-first</strong>
              <span>Mọi kết luận có nguồn</span>
            </div>
          </div>
          <div className="authBrandFoot">
            <span className="material-symbols-outlined">verified</span>
            Hải Đăng Khởi Nghiệp © 2026
          </div>
        </div>
      </section>

      <section className="authFormPane">
        <div className="authForm">
          <div className="authFormHead">
            <div className="authLogo" aria-hidden="true">
              <span className="authLogoImage" />
            </div>
            <h1>{mode === "login" ? "Chào mừng trở lại" : "Tạo tài khoản"}</h1>
            <p>
              {mode === "login"
                ? "Đăng nhập để tiếp tục với bàn thẩm định của bạn."
                : "Dữ liệu và chức năng được giới hạn theo đúng vai trò của bạn."}
            </p>
          </div>

          <div className="segmentedControl authMode">
            <button className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")} type="button">
              Đăng nhập
            </button>
            <button className={mode === "register" ? "active" : ""} onClick={() => switchMode("register")} type="button">
              Đăng ký
            </button>
          </div>

          {error && (
            <div className="authError" role="alert">
              <span className="material-symbols-outlined">error</span>
              <span>{error}</span>
            </div>
          )}

          <form className="authFields" onSubmit={submit}>
            {mode === "register" && (
              <>
                <div className="authField">
                  <label htmlFor="full_name">
                    <span className="material-symbols-outlined">badge</span>
                    Họ và tên
                  </label>
                  <div className="authInputWrap">
                    <span className="material-symbols-outlined lead">person</span>
                    <input id="full_name" name="full_name" minLength={2} required placeholder="Nguyễn Văn A" />
                  </div>
                </div>
                <div className="authField">
                  <label htmlFor="role">
                    <span className="material-symbols-outlined">workspace_premium</span>
                    Vai trò
                  </label>
                  <div className="authInputWrap">
                    <span className="material-symbols-outlined lead">groups</span>
                    <select id="role" value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                      <option value="startup">Startup</option>
                      <option value="investor">Nhà đầu tư</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            <div className="authField">
              <label htmlFor="email">
                <span className="material-symbols-outlined">alternate_email</span>
                Email
              </label>
              <div className="authInputWrap">
                <span className="material-symbols-outlined lead">mail</span>
                <input id="email" name="email" type="email" required placeholder="ban@congty.vn" autoComplete="email" />
              </div>
            </div>

            <div className="authField">
              <label htmlFor="password">
                <span className="material-symbols-outlined">lock</span>
                Mật khẩu
              </label>
              <div className="authInputWrap hasTrail">
                <span className="material-symbols-outlined lead">password</span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  minLength={8}
                  required
                  placeholder="••••••••"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  className="authReveal"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  title={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  <span className="material-symbols-outlined">{showPassword ? "visibility_off" : "visibility"}</span>
                </button>
              </div>
            </div>

            {mode === "login" && (
              <label className="authRemember">
                <input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
                Duy trì đăng nhập trên thiết bị này
              </label>
            )}

            <button className="primaryButton authSubmit" disabled={busy}>
              {busy ? "Đang xử lý..." : mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
              {!busy && <span className="material-symbols-outlined">arrow_forward</span>}
            </button>
          </form>

          <div className="authSwitch">
            <span>{mode === "login" ? "Chưa có tài khoản?" : "Đã có tài khoản?"}</span>
            <button type="button" className="authSwitchBtn" onClick={() => switchMode(mode === "login" ? "register" : "login")}>
              {mode === "login" ? "Đăng ký tài khoản mới" : "Đăng nhập"}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
